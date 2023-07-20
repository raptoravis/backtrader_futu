from __future__ import absolute_import, division, print_function, unicode_literals

from datetime import timedelta
import pandas as pd
from backtrader.feed import DataBase
from backtrader import date2num, num2date
from backtrader.utils.py3 import queue, with_metaclass
import backtrader as bt

from backtrader_futu.stores import futustore
from ..streamer import MsgType, _load_tick_lines


class FutuTickData(DataBase):
    params = (
        ("useask", True),
    )

    def __init__(self, **kwargs):
        self.msg = None
        self.quote_update = False

        self.last_volume = None

    def _load(self):
        if self.msg:
            ret = self._load_tick(self.msg, self.quote_update)
            self.msg = None

            return ret

        return False

    def add_tick(self, msg, quote_update: bool):
        self.msg = msg
        self.quote_update = quote_update

    def new_minutes(self):
        # self.last_volume = None
        pass

    def _load_tick(self, msg, quote_update: bool):
        ret, self.last_volume = _load_tick_lines(self.lines, self.last_volume, msg, quote_update)
        return ret
