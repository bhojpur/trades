# Copyright (c) 2018 Bhojpur Consulting Private Limited, India. All rights reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

"""
The server is a multi-asset, multi-strategy, event-driven trade execution and
backtesting platform for trading common markets.
"""

from dateutil import parser
from datetime import datetime
from typing import Callable, List, Tuple

class Event(object):
    """
    Base class for system events.
    """

class MarketEvent(Event):
    """
    Wrapper for new market data. Consumed by Strategy object to
    produce Signal events.
    """

    # Datetime object format string
    DTFMT = '%Y-%m-%d %H:%M'

    def __init__(self, exchange, bar):
        self.type = 'MARKET'
        self.exchange = exchange
        self.bar = bar

    def __str__(self):
        return str("MarketEvent - Exchange: " + self.exchange.get_name() +
                   " Symbol: " + self.bar['symbol'] + " TS: " +
                   self.get_datetime() + " Close: " + self.bar['close'])

    def get_bar(self):
        return self.bar

    def get_exchange(self):
        return self.exchange

    def get_datetime(self):
        return datetime.fromtimestamp(
            self.bar['timestamp']).strftime(self.DTFMT),

class SignalEvent(Event):
    """
    Entry signal. Consumed by Portfolio to produce Order events.
    """

    def __init__(self, symbol: str, entry_ts, direction: str, timeframe: str,
                 strategy: str, venue, entry_price: float, entry_type: str,
                 targets: list, stop_price: float, void_price: float,
                 note: str):

        self.type = 'SIGNAL'
        self.entry_ts = entry_ts        # Entry bar timestamp.
        self.timeframe = timeframe      # Signal timeframe.
        self.strategy = strategy        # Signal strategy name.
        self.venue = venue              # Signal venue name.
        self.symbol = symbol            # Ticker code for instrument.
        self.direction = direction      # LONG or SHORT.
        self.entry_price = entry_price  # Trade entry price.
        self.entry_type = entry_type    # Order type for entry.
        self.targets = targets          # Profit targets and %'s.
        self.stop_price = stop_price    # Stop-loss order price.
        self.void_price = void_price    # Invalidation price.
        self.note = note                # Signal notes.

    def __str__(self):
        return str("SignalEvent - Direction: " + self.direction + " Symbol: " +
                   self.symbol + " Entry price: " + str(self.entry_price) +
                   " Entry timestamp: " + str(self.entry_ts) + " Timeframe: " +
                   self.timeframe + " Strategy: " + self.strategy +
                   " Venue: " + self.venue.get_name() + " Order type: " +
                   self.entry_type + " Note: " + self.note)

    def get_signal(self):
        return {
            'strategy': self.strategy,
            'venue': self.venue.get_name(),
            'symbol': self.symbol,
            'entry_timestamp': self.entry_ts,
            'direction': self.direction,
            'entry_price': self.entry_price,
            'entry_type': self.entry_type,
            'targets': self.targets,
            'stop_price': self.stop_price,
            'void_price': self.void_price,
            'note': self.note}

class OrderEvent(Event):
    """
    Contains order details to be sent to a broker/exchange.
    """

    def __init__(self, symbol, exchange, order_type, quantity):
        self.type = 'ORDER'
        self.symbol = symbol            # Instrument ticker.
        self.exchange = exchange        # Source exchange.
        self.order_type = order_type    # MKT, LMT, SMKT, SLMT.
        self.quantity = quantity        # Integer.

    def __str__(self):
        return "OrderEvent - Symbol: %s, Type: %s, Qty: %s, Direction: %s" % (
            self.symbol, self.order_type, self.quantity, self.direction)

class FillEvent(Event):
    """
    Holds transaction data including fees/comissions, slippage, brokerage,
    actual fill price, timestamp, etc.
    """

    def __init__(self, timestamp, symbol, exchange, quantity,
                 direction, fill_cost, commission=None):
        self.type = 'FILL'
        self.timestamp = timestamp     # Fill timestamp
        self.symbol = symbol           # Instrument ticker
        self.exchange = exchange       # Source exchange
        self.quantity = quantity       # Position size.
        self.fill_cost = fill_cost     # USD value of fees.

        # use BitMEX taker fees as placeholder
        if commission is None:
            self.commission = (fill_cost / 100) * 0.075
        else:
            self.commission = commission

    def calculate_commission(self):
        """
        """