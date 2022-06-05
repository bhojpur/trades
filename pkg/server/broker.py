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

class Broker:
    """
    Broker consumes Order events, executes orders, then creates and places
    Fill events in the event queue post-transaction.
    """

    def __init__(self, exchanges, logger, db_other, db_client, live_trading):
        self.exchanges = exchanges
        self.logger = logger
        self.db_other = db_other
        self.db_client = db_client
        self.live_trading = live_trading

    def new_order(self, events, event):
        """
        Process incoming order event, place orders with venues and generate
        a fill event post-execution.

        Args:
            events: event queue object.
            event: new market event.

        Returns:
           None.

        Raises:
            None.
        """
        pass