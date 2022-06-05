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

import os
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())
from indicators import *

ALPHAVANTAGE = 'alphavantage_key'
INTRINIO_USERNAME = 'intrinio_username'
INTRINIO_PASSWORD = 'intrinio_password'
DATA_FOLDER = 'data'

def check_credentials():
    for var in [ALPHAVANTAGE, INTRINIO_USERNAME, INTRINIO_PASSWORD]:
        if not os.environ.get(var):
            not_found(var)

def not_found(var):
    raise Exception(var + ' not found in environment')

check_credentials()

PARAMS = {

    'verbose': os.environ.get('verbose', False),

    'credentials': {
        'alphavantage': os.environ.get(ALPHAVANTAGE),
        'intrinio': {
            'username': os.environ.get(INTRINIO_USERNAME),
            'password': os.environ.get(INTRINIO_PASSWORD)
        }
    },

    'data_folder': os.environ.get('data_folder', DATA_FOLDER),

    'screeners': {
        'yahoo': [
            'undervalued_growth_stocks',
            'day_gainers',
            'day_losers',
            'most_actives',
            'growth_technology_stocks',
            'undervalued_large_caps',
            'aggressive_small_caps',
            'portfolio_anchors',
            'solid_large_growth_funds'
        ],
        'intrinio': {
            'undervalued': {
                'conditions': [
                    ['pricetoearnings', '<=', 20],
                    ['pricetoearnings', '>', 0]
                ]
            }
        }
    },

    'data_options': {
        'daily': daily,
        'daily_adj': daily_adjusted,
        'sma': sma,
        'ema': ema,
        'macd': macd,
        'stoch': stoch,
        'rsi': rsi,
        'adx': adx,
        'cci': cci,
        'aroon': aroon,
        'bbands': bbands,
        'ad': ad,
        'obv': obv
    }

}