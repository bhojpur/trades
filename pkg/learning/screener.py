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

from __future__ import (absolute_import, division, print_function, unicode_literals)
from argparse import ArgumentParser
from urllib.parse import quote_plus
import requests
from base64 import b64encode
from pyquery import PyQuery as pq
from utility import *

# get data from Yahoo predefined screeners
def yahoo(screener):
    d = pq(url='https://finance.yahoo.com/screener/predefined/%s' % screener)
    elements = d("td.Va\\(m\\) > a.Fw\\(b\\)")
    return [a.text for a in elements]

def get_symbols(symbols, screener, limit):
    symbols = symbols or []
    if screener:
        symbols += yahoo(screener)
    return symbols[:limit]

# AAII screener 'table > tbody > tr:nth-child(2n+1) > td:nth-child(2) > a'
# needs authentication

USERNAME = PARAMS['credentials']['intrinio']['username']
PASSWORD = PARAMS['credentials']['intrinio']['password']

# get data from Intrinio custom screeners
def request(conditions):
    params = encode_conditions(conditions)
    url = 'https://api.intrinio.com/securities/search?conditions=%s' % quote_plus(params)
    auth = 'Basic %s' % b64encode(('%s:%s' % (USERNAME, PASSWORD)).encode()).decode()
    headers = {
        'Authorization': auth
    }
    return requests.get(url, headers=headers).json()

def encode_element(element):
    if element == '>':
        return 'gt'
    elif element == '>=':
        return 'gte'
    elif element == '<':
        return 'lt'
    elif element == '<=':
        return 'lte'
    elif element == '=':
        return 'eq'
    else:
        return str(element)

def encode_condition(condition):
    return "~".join(map(encode_element, condition))

def encode_conditions(conditions):
    return ",".join(map(encode_condition, conditions))

def add_args(parser):
    parser.add_argument('screener', type=str, help='name of Yahoo screener')
    parser.add_argument('-l', '--limit', type=int, help='take the first l symbols')

def handle_args(args, parser):
    pass

def main():
    args = parse_args('Screen for symbols.', add_args, handle_args)
    data = ' '.join(get_symbols(None, args.screener, args.limit))
    log(data, force=args.print)

if __name__ == '__main__':
    main()
