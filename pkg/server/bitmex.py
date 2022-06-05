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

from datetime import timezone, datetime, timedelta
from requests import Request, Session
from requests.auth import AuthBase
from urllib.parse import urlparse
from bitmex_ws import Bitmex_WS
from exchange import Exchange
from dateutil import parser
import traceback
import requests
import hashlib
import hmac
import time

class Bitmex(Exchange):
    """
    BitMEX exchange model.
    """

    MAX_BARS_PER_REQUEST = 750
    TIMESTAMP_FORMAT = '%Y-%m-%d%H:%M:%S.%f'

    BASE_URL = "https://www.bitmex.com/api/v1"
    BASE_URL_TESTNET = "https://www.testnet.bitmex.com/api/v1"
    WS_URL = "wss://www.bitmex.com/realtime"
    BARS_URL = "/trade/bucketed?binSize="
    TICKS_URL = "/trade?symbol="
    POSITIONS_URL = "/position"
    ORDERS_URL = "/order"

    def __init__(self, logger):
        super()
        self.logger = logger
        self.name = "BitMEX"
        self.symbols = ["XBTUSD"]  # "ETHUSD", "XRPUSD"
        self.channels = ["trade"]

        self.origin_tss = {
            "XBTUSD": 1483228800,
            "ETHUSD": 1533200520,
            "XRPUSD": 1580875200}

        self.api_key, self.api_secret = self.load_api_keys()

        # Non persistent datastores.
        self.bars = {}
        self.ticks = {}

        # Connect to trade websocket.
        self.ws = Bitmex_WS(
            self.logger, self.symbols, self.channels, self.WS_URL,
            self.api_key, self.api_secret)
        if not self.ws.ws.sock.connected:
            self.logger.debug("Failed to to connect to BitMEX websocket.")

        # Note, for future channel subs, create new Bitmex_WS in new process.

    def parse_ticks(self):

        if not self.ws.ws:
            self.logger.debug("BitMEX websocket disconnected.")
        else:
            all_ticks = self.ws.get_ticks()
            target_minute = datetime.now().minute - 1
            ticks_target_minute = []
            tcount = 0

            # Search from end of tick list to grab newest ticks first.
            for i in reversed(all_ticks):
                try:
                    ts = i['timestamp']
                    if type(ts) is not datetime:
                        ts = parser.parse(ts)
                except Exception:
                    self.logger.debug(traceback.format_exc())

                # Scrape prev minutes ticks.
                if ts.minute == target_minute:
                    ticks_target_minute.append(i)
                    ticks_target_minute[tcount]['timestamp'] = ts
                    tcount += 1

                # Store the previous-to-target bar's last
                # traded price to use as the open price for target bar.
                if ts.minute == target_minute - 1:
                    ticks_target_minute.append(i)
                    ticks_target_minute[tcount]['timestamp'] = ts
                    break

            ticks_target_minute.reverse()

            # Group ticks by symbol.
            self.ticks = {i: [] for i in self.symbols}
            for tick in ticks_target_minute:
                self.ticks[tick['symbol']].append(tick)

            #  Build bars from ticks.
            self.bars = {i: [] for i in self.symbols}
            for symbol in self.symbols:
                bar = self.build_OHLCV(self.ticks[symbol], symbol)
                self.bars[symbol].append(bar)

    def get_bars_in_period(self, symbol, start_time, total):

        if total >= self.MAX_BARS_PER_REQUEST:
            total = self.MAX_BARS_PER_REQUEST

        # Convert epoch timestamp to ISO 8601.
        start = datetime.utcfromtimestamp(start_time).isoformat()
        timeframe = "1m"

        payload = (
            f"{self.BASE_URL}{self.BARS_URL}{timeframe}&"
            f"symbol={symbol}&filter=&count={total}&"
            f"startTime={start}&reverse=false")

        # Uncomment below line to manually verify results.
        # self.logger.debug("API request string: " + payload)

        bars_to_parse = requests.get(payload).json()

        # Store only required values (OHLCV) and convert timestamp to epoch.
        new_bars = []
        for bar in bars_to_parse:
            new_bars.append({
                'symbol': symbol,
                'timestamp': int(parser.parse(bar['timestamp']).timestamp()),
                'open': bar['open'],
                'high': bar['high'],
                'low': bar['low'],
                'close': bar['close'],
                'volume': bar['volume']})

        return new_bars

    def get_origin_timestamp(self, symbol: str):

        if self.origin_tss[symbol] is not None:
            return self.origin_tss[symbol]
        else:
            payload = (
                f"{self.BASE_URL}{self.BARS_URL}1m&symbol={symbol}&filter=&"
                f"count=1&startTime=&reverse=false")

            response = requests.get(payload).json()[0]['timestamp']
            timestamp = int(parser.parse(response).timestamp())

            self.logger.debug(
                "BitMEX" + symbol + " origin timestamp: " + str(timestamp))

            return timestamp

    def get_recent_bars(timeframe, symbol, n=1):

        payload = str(
            self.BASE_URL + self.BARS_URL + timeframe +
            "&partial=false&symbol=" + symbol + "&count=" +
            str(n) + "&reverse=true")

        result = requests.get(payload).json()

        bars = []
        for i in result:
            bars.append({
                    'symbol': symbol,
                    'timestamp': i['timestamp'],
                    'open': i['open'],
                    'high': i['high'],
                    'low': i['low'],
                    'close': i['close'],
                    'volume': i['volume']})
        return bars

    def get_recent_ticks(symbol, n=1):

        # Find difference between start and end of period.
        delta = n * 60

        # Find start timestamp and convert to ISO1806.
        start_epoch = self.previous_minute() + 60 - delta
        start_iso = datetime.utcfromtimestamp(start_epoch).isoformat()

        # find end timestamp and convert to ISO1806
        end_epoch = previous_minute() + 60
        end_iso = datetime.utcfromtimestamp(end_epoch).isoformat()

        # Initial poll.
        sleep(1)
        payload = str(
            self.BASE_URL + self.TICKS_URL + symbol + "&count=" +
            "1000&reverse=false&startTime=" + start_iso + "&endTime" + end_iso)

        ticks = []
        initial_result = requests.get(payload).json()
        for tick in initial_result:
            ticks.append(tick)

        # If 1000 ticks in result (max size), keep polling until
        # we get a response with length <1000.
        if len(initial_result) == 1000:

            maxed_out = True
            while maxed_out:

                # Dont use endTime as it seems to cut off the final few ticks.
                payload = str(
                    BASE_URL + TICKS_URL + symbol + "&count=" +
                    "1000&reverse=false&startTime=" + ticks[-1]['timestamp'])

                interim_result = requests.get(payload).json()
                for tick in interim_result:
                    ticks.append(tick)

                if len(interim_result) != 1000:
                    maxed_out = False

        # Check median tick timestamp matches start_iso.
        median_dt = parser.parse(ticks[int((len(ticks) / 2))]['timestamp'])
        match_dt = parser.parse(start_iso)
        if median_dt.minute != match_dt.minute:
            raise Exception("Tick data timestamp error: timestamp mismatch.")

        # Populate list with matching-timestamped ticks only.
        final_ticks = [
            i for i in ticks if parser.parse(
                i['timestamp']).minute == match_dt.minute]

        return final_ticks

    def get_positions(self):
        s = Session()
        prepared_request = Request(
            'GET',
            self.BASE_URL_TESTNET + self.POSITIONS_URL,
            params='').prepare()
        request = self.generate_request_headers(prepared_request, api_key,
                                                api_secret)
        response = s.send(request).json()

        return response

    def get_orders(self):
        s = Session()
        prepared_request = Request(
            'GET',
            self.BASE_URL_TESTNET + self.ORDERS_URL,
            params='').prepare()
        request = self.generate_request_headers(prepared_request, api_key,
                                                api_secret)
        response = s.send(request).json()

        return response

    def generate_request_signature(self, secret, request_type, url, nonce,
                                   data):
        """
        Generate BitMEX-compatible authenticated request signature header.

        Args:
            secret: API secret key.
            request_type: Request type (GET, POST, etc).
            url: full request url.
            validity: seconds request will be valid for after creation.
        Returns:
            signature: hex(HMAC_SHA256(apiSecret, verb + path + expires + data)
        Raises:
            None.
        """

        parsed_url = urlparse(url)
        path = parsed_url.path

        if parsed_url.query:
            path = path + '?' + parsed_url.query

        if isinstance(data, (bytes, bytearray)):
            data = data.decode('utf8')

        message = str(request_type).upper() + path + str(nonce) + data
        signature = hmac.new(bytes(secret, 'utf8'), bytes(message, 'utf8'),
                             digestmod=hashlib.sha256).hexdigest()

        return signature

    def generate_request_headers(self, request, api_key, api_secret):
        """
        Add BitMEX-compatible authentication headers to a request object.

        Args:
            api_key: API key.
            api_secret: API secret key.
            request: Request object to be amended.
        Returns:
            request: Modified request object.
        Raises:
            None.
        """

        nonce = str(int(round(time.time()) + 5))
        request.headers['api-expires'] = nonce
        request.headers['api-key'] = api_key
        request.headers['api-signature'] = generate_request_signature(
            api_secret, request.method, request.url, nonce, request.body or '')

        return request