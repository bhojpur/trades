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

from abc import ABC, abstractmethod

class Trade(ABC):
    """
    Trade parent class, different types of trade subclasses must inherit this.

    Trade subclasses are used to generalise a collective set of orders and
    positions that make up a trades management from start to finish.

    Child trade classes may be composed of positons and orders across one or
    multiple instruments and venues.
    """

    def __init__(self):
        self.trade_id = None            # Must be set before saving to database.
        self.active = False             # True/False.
        self.venue_count = 0            # Number of venues in use.
        self.instrument_count = 0       # Number of instruments in use.
        self.model = None               # Name of model that triggered trade.
        self.u_pnl = 0                  # Total unrealised P&L.
        self.r_pnl = 0                  # Total realised P&L.
        self.fees = 0                   # Total fees/commisions paid.
        self.exposure = None            # Percentage of capital at risk.

    @abstractmethod
    def get_trade_dict(self):
        """
        Return all trade variables as a dict for database storage.
        """

class SingleInstrumentTrade(Trade):
    """
    Models the state of a single-instrument, single venue trade.

    Used when trading a single instrument directionally, with take profit
    and stop loss orders.
    """

    def __init__(self, logger, venue, symbol, model, position=None,
                 open_orders=None, filled_orders=None):
        super().__init__()
        self.logger = logger
        self.type = "SINGLE_INSTRUMENT"
        self.venue_count = 1
        self.instrument_count = 1
        self.venue = venue                  # Exchange or broker traded with.
        self.symbol = symbol                # Instrument ticker code.
        self.model = model                  # Name of triggerstrategy.
        self.position = position            # Position object, if positioned.
        self.open_orders = open_orders      # List of active orders.
        self.filled_orders = filled_orders  # List of filled orders.

    def get_trade_dict(self):
        return {
            'trade_id': self.trade_id,
            'type': self.type,
            'active': self.active,
            'venue_count': self.venue_count,
            'instrument_count': self.instrument_count,
            'model': self.model,
            'u_pnl': self.u_pnl,
            'r_pnl': self.r_pnl,
            'fees': self.fees,
            'exposure': self.exposure,
            'venue': self.venue,
            'symbol': self.symbol,
            'open_orders': self.open_orders,
            'filled_orders': self.filled_orders}

class Position:
    """
    Models a single active position, as part of a parent trade.
    """

    def __init__(self, logger, trade_id, direction, leverage,
                 liquidation, size, entry_price):
        self.logger = logger
        self.trade_id = trade_id        # Parent trade ID.
        self.direction = direction      # Long or short.
        self.leverage = leverage        # Leverage in use.
        self.liquidation = liquidation  # Liquidation price.
        self.size = size                # Asset/contract demonination.
        self.entry_price = entry_price  # Average entry price.

    def get_position_dict(self):
        """
        Return all position variables as a dict for database storage.
        """
        return {
            'trade_id': self.trade_id,
            'direction': self.direction,
            'leverage': self.leverage,
            'liquidation': self.liquidation,
            'size': self.size,
            'entry_price': self.entry_price}

class Order:
    """
    Models a single order, as part of parent trade.
    """

    def __init__(self, logger, trade_id, p_id, order_id, direction,
                 size, price, order_type, metatype, void_price, trail,
                 reduce_only, post_only, status="UNFILLED"):
        self.logger = logger
        self.trade_id = trade_id        # Parent trade ID.
        self.position_id = p_id         # Related position ID.
        self.order_id = order_id        # Order ID as used by venue.
        self.direction = direction      # Long or short.
        self.size = size                # Size in local asset/contract.
        self.price = price              # Order price.
        self.order_type = order_type    # LIMIT MARKET STOP_LIMIT STOP_MARKET.
        self.metatype = metatype        # ENTRY, TAKE_PROFIT, STOP.
        self.void_price = void_price    # Order invalidation price.
        self.trail = trail              # True or False, only for stops.
        self.reduce_only = reduce_only  # True or False.
        self.post_only = post_only      # True of False.
        self.status = status            # FILLED, UNFILLED, PARTIAL.

    def get_order_dict(self):
        """
        Return all order variables as a dict for database storage.
        """
        return {
            'trade_id': self.trade_id,
            'position_id': self.position_id,
            'order_id': self.order_id,
            'direction': self.direction,
            'size': self.size,
            'price': self.price,
            'order_type': self.order_type,
            'metatype': self.metatype,
            'void_price': self.void_price,
            'trail': self.trail,
            'reduce_only': self.reduce_only,
            'post_only': self.post_only,
            'status': self.status}

class TradeID():
    """
    Utility class for generating sequential trade ID's from database.
    """

    def __init__(self, db):
        self.db = db

    def new_id(self):
        result = list(self.db['trades'].find({}).sort([("trade_id", -1)]))
        return (int(result[0]['trade_id']) + 1) if result else 1