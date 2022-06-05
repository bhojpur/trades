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

def daily():
    return {
        'function': 'TIME_SERIES_DAILY',
        'columns': ['open', 'high', 'low', 'close', 'volume'],
        'outputsize': 'full'
    }

def daily_adjusted():
    return {
        'function': 'TIME_SERIES_DAILY_ADJUSTED',
        'columns': ['adjusted close', 'dividend amount', 'split coefficient'],
        'outputsize': 'full'
    }

def sma(period=30):
    return {
        'function': 'SMA',
        'columns': ['SMA'],
        'interval': 'daily',
        'time_period': period,
        'series_type': 'close'
    }

def ema(period=20):
    return {
        'function': 'EMA',
        'columns': ['EMA'],
        'interval': 'daily',
        'time_period': period,
        'series_type': 'close'
    }

def macd(fast=12, slow=26, signal=9):
    return {
        'function': 'MACD',
        'columns': ['MACD_Signal', 'MACD_Hist', 'MACD'],
        'interval': 'daily',
        'series_type': 'close',
        'fastperiod': fast,
        'slowperiod': slow,
        'signalperiod': signal,
    }

def stoch(fastk=5, slowk=3, slowd=3, kma=0, dma=0):
    return {
        'function': 'STOCH',
        'columns': ['SlowD', 'SlowK'],
        'interval': 'daily',
        'series_type': 'close',
        'fastkperiod': fastk,
        'slowkperiod': slowk,
        'slowdperiod': slowd,
        'slowkmatype': kma,
        'slowdmatype': dma
    }

def rsi(period=14):
    return {
        'function': 'RSI',
        'columns': ['RSI'],
        'interval': 'daily',
        'series_type': 'close',
        'time_period': period
    }

def adx(period=14):
    return {
        'function': 'ADX',
        'columns': ['ADX'],
        'interval': 'daily',
        'series_type': 'close',
        'time_period': period
    }

def cci(period=14):
    return {
        'function': 'CCI',
        'columns': ['CCI'],
        'interval': 'daily',
        'series_type': 'close',
        'time_period': period
    }

def aroon(period=14):
    return {
        'function': 'AROON',
        'columns': ['Aroon Up', 'Aroon Down'],
        'interval': 'daily',
        'time_period': period
    }

def bbands(period=14, ndev=2, ma=0):
    return {
        'function': 'BBANDS',
        'columns': ['Real Middle Band', 'Real Upper Band', 'Real Lower Band'],
        'interval': 'daily',
        'time_period': period,
        'series_type': 'close',
        'nbdevup': ndev,
        'nbdevdn': ndev,
        'matype': ma
    }

def ad():
    return {
        'function': 'AD',
        'columns': ['Chaikin A/D'],
        'interval': 'daily',
    }

def obv():
    return {
        'function': 'OBV',
        'columns': ['OBV'],
        'interval': 'daily',
    }
