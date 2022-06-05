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

from trade_types import SingleInstrumentTrade, Order, Position, TradeID
from event_types import OrderEvent, FillEvent
from pymongo import MongoClient, errors
import pymongo
import time
import queue

class Portfolio:
    """
    Portfolio manages the net holdings for all models, issuing order events
    and reacting to fill events to open and close positions and strategies
    dictate.

    Capital allocations to strategies and risk parameters defined here.
    """

    MAX_SIMULTANEOUS_POSITIONS = 20
    MAX_CORRELATED_TRADES = 1
    MAX_ACCEPTED_DRAWDOWN = 15          # Percentage as integer.
    RISK_PER_TRADE = 1                  # Percentage as integer OR 'KELLY'
    DEFAULT_STOP = 3                    # % stop distance if none provided.

    def __init__(self, exchanges, logger, db_other, db_client, models):
        self.exchanges = {i.get_name(): i for i in exchanges}
        self.logger = logger
        self.db_other = db_other
        self.db_client = db_client
        self.models = models

        self.id_gen = TradeID(db_other)
        self.pf = self.load_portfolio()
        self.trades_save_to_db = queue.Queue(0)

    def new_signal(self, events, event):
        """
        Interpret incoming signal events to produce Order Events.

        Args:
            events: event queue object.
            event: new market event.

        Returns:
           None.

        Raises:
            None.
        """

        signal = event.get_signal_dict()

        if self.within_risk_limits(signal):
            orders = []

            # Prepare orders for single-instrument signals:
            if signal['instrument_count'] == 1:

                stop = self.calculate_stop_price(signal),
                size = self.calculate_position_size(stop[0],
                                                    signal['entry_price'])

                # Generate sequential trade ID for order and trade objects.
                trade_id = self.id_gen.new_id()

                # Entry order.
                orders.append(Order(
                    self.logger,
                    trade_id,               # Parent trade ID.
                    None,                   # Related position ID.
                    None,                   # Order ID as used by venue.
                    signal['direction'],    # LONG or SHORT.
                    size,                   # Size in native denomination.
                    signal['entry_price'],  # Order price.
                    signal['entry_type'],   # LIMIT MARKET STOP_LIMIT/MARKET.
                    "ENTRY",                # ENTRY, TAKE_PROFIT, STOP.
                    stop[0],                # Order invalidation price.
                    False,                  # Trail.
                    False,                  # Reduce-only order.
                    False))                 # Post-only order.

                # Stop order.
                orders.append(Order(
                    self.logger,
                    trade_id,
                    None,
                    None,
                    event.inverse_direction(),
                    size,
                    stop[0],
                    "STOP_MARKET",
                    "STOP",
                    None,
                    signal['trail'],
                    True,
                    False))

                # Take profit order(s).
                if signal['targets']:
                    for target in signal['targets']:
                        tp_size = (size / 100) * target[1]
                        orders.append(Order(
                            self.logger,
                            trade_id,
                            None,
                            None,
                            event.inverse_direction(),
                            tp_size,
                            target[0],
                            "LIMIT",
                            "TAKE_PROFIT",
                            stop[0],
                            False,
                            True,
                            False))

                # Parent trade object:
                trade = SingleInstrumentTrade(
                    self.logger,
                    signal['venue'],        # Exchange or broker traded with.
                    signal['symbol'],       # Instrument ticker code.
                    signal['strategy'],     # Model name.
                    None,                   # Position object.
                    [i.get_order_dict() for i in orders],  # Open orders dicts.
                    None)                   # Filled order dicts.

                # Set trade_id manually, since we already generated it above.
                trade.trade_id = trade_id

                # Queue the trade for storage and update portfolio state.
                self.trades_save_to_db.put(trade.get_trade_dict())
                self.pf['trades'].append(trade.get_trade_dict())
                self.save_porfolio(self.pf)

            # TODO: Other trade types (multi-instrument, multi-venue etc).

            # Queue orders for execution.
            for order in orders:
                events.put(OrderEvent(order.get_order_dict()))

            self.logger.debug("Trade " + str(trade_id) + " registered.")

    def new_fill(self, events, event):
        """
        Process incoming fill event and update position records accordingly.

        Args:
            events: event queue object.
            event: new market event.

        Returns:
           None.

        Raises:
            None.
        """
        pass

    def update_price(self, events, market_event):
        """
        Check price and time updates against existing positions.

        Args:
            events: event queue object.
            event: new market event.

        Returns:
           None.

        Raises:
            None.
        """
        pass

    def load_portfolio(self, ID=1):
        """
        Load portfolio matching ID from database or return empty portfolio.
        """

        portfolio = self.db_other['portfolio'].find_one({"id": ID}, {"_id": 0})

        if portfolio:
            self.verify_portfolio_state(portfolio)
            return portfolio

        else:
            empty_portfolio = {
                'id': ID,
                'start_date': int(time.time()),
                'initial_funds': 0,
                'current_value': 0,
                'current_drawdown': 0,
                'trades': [],
                'model_allocations': {  # Equal allocation by default.
                    i.get_name(): (100 / len(self.models)) for i in self.models},
                'risk_per_trade': self.RISK_PER_TRADE,
                'max_correlated_trades': self.MAX_CORRELATED_TRADES,
                'max_accepted_drawdown': self.MAX_ACCEPTED_DRAWDOWN,
                'max_simultaneous_positions': self.MAX_SIMULTANEOUS_POSITIONS,
                'default_stop': self.DEFAULT_STOP}

            self.save_porfolio(empty_portfolio)
            return empty_portfolio

    def verify_portfolio_state(self, portfolio):
        """
        Check stored portfolio data matches actual positions and orders.
        """

        trades = self.db_other['trades'].find({"active": "True"}, {"_id": 0})

        # If trades marked active exist (in DB), check their orders and
        # positions match actual trade state, update portfoilio if disparate.
        if trades:
            self.logger.debug("Verifying trade records match trade state.")
            for venue in [trade['venue'] for trade in trades]:

                print("Fetched positions and orders.")
                positions = self.exchanges[venue].get_positions()
                orders = self.exchanges[venue].get_orders()

                # TODO: state checking.

        self.save_porfolio(portfolio)
        self.logger.debug("Portfolio verification complete.")

        return portfolio

    def save_porfolio(self, portfolio):
        """
        Save portfolio state to database.
        """

        result = self.db_other['portfolio'].replace_one(
            {"id": portfolio['id']}, portfolio, upsert=True)

        if result.acknowledged:
            self.logger.debug("Portfolio update successful.")
        else:
            self.logger.debug("Portfolio update unsuccessful.")

    def within_risk_limits(self, signal):
        """
        Return true if the new signal would be within risk limits if traded.
        """

        # TODO: Finish after signal > order > fill logic is done.

        return True

    def calculate_exposure(self, trade):
        """
        Calculate the currect capital at risk for the given trade.
        """
        pass

    def correlated(self, instrument):
        """
        Return true if any active trades are correlated with 'instrument'.
        """
        pass

    def calculate_stop_price(self, signal):
        """
        Find the stop price for the given signal.
        """

        if signal['stop_price'] is not None:
            stop = signal['stop_price']
        else:
            stop = signal['entry_price'] / 100 * (100 - self.DEFAULT_STOP)

        return stop

    def calculate_position_size(self, stop, entry):
        """
        Find appropriate position size for the given parameters.
        """

        # Fixed percentage per trade risk management.
        if isinstance(self.RISK_PER_TRADE, int):

            account_size = self.pf['current_value']
            risked_amt = (account_size / 100) * self.RISK_PER_TRADE
            position_size = risked_amt // ((stop - entry) / entry)

            return abs(position_size)

        # TOOD: Kelly criteron risk management.
        elif self.RISK_PER_TRADE.upper() == "KELLY":
            pass

    def fees(self, trade):
        """
        Calculate total current fees paid for the given trade object.
        """

    def save_new_trades_to_db(self):
        """
        Save trades in save-later queue to database.

        Args:
            None.
        Returns:
            None.
        Raises:
            pymongo.errors.DuplicateKeyError.
        """

        count = 0
        while True:

            try:
                trade = self.trades_save_to_db.get(False)

            except queue.Empty:
                if count:
                    self.logger.debug(
                        "Wrote " + str(count) + " new trades to database " +
                        str(self.db_other.name) + ".")
                break

            else:
                if trade is not None:
                    count += 1
                    # Store signal in relevant db collection.
                    try:
                        self.db_other['trades'].insert_one(trade)

                    # Skip duplicates if they exist.
                    except pymongo.errors.DuplicateKeyError:
                        continue

                self.trades_save_to_db.task_done()