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

from utility import *
import traceback
import os

class DataException(Exception):
    pass

class Data:

    def __init__(self, **params):
        self.params = params
        self.path = None
        self.data = None
        self.get_path()
        self.make_path()
        self.write_params()
        self.data = self.get_data()

    def data_error_msg(self):
        return 'Failed to get data for ' + str(self.params)

    def get_data(self):
        try:
            if self.data is None:
                self.data = self.read_data()
                if self.data is None:
                    self.data = self.get_new_data()
                    if self.data is None:
                        raise DataException(self.data_error_msg())
                    self.write_data()
            return self.data
        except Exception:
            raise DataException(traceback.format_exc() + '\n' + self.data_error_msg())

    def get_base_path(self):
        if not self.path:
            file_name = shorten_path(encrypt_dict(self.params))
            cwd = os.getcwd()
            self.path = os.path.join(cwd, PARAMS['data_folder'], self.get_folder(), file_name)
        return self.path

    def get_path(self, *paths):
        return os.path.join(self.get_base_path(), *paths)

    def make_path(self):
        make_path(self.get_params_path())

    def get_params_path(self):
        return self.get_path('params.pkl')

    def write_params(self):
        write_pickle(self.get_params_path(), self.params)

    @classmethod
    def load(cls, path):
        params = read_pickle(os.path.join(path, 'params.pkl'))
        return cls(**params)

    def get_new_data(self):
        raise NotImplementedError()

    def get_folder(self):
        raise NotImplementedError()

    def read_data(self):
        raise NotImplementedError()

    def write_data(self):
        raise NotImplementedError()
