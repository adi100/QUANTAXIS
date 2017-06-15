# coding:utf-8
#
# The MIT License (MIT)
#
# Copyright (c) 2016-2017 yutiansut/QUANTAXIS
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import datetime
import random
import time

from tabulate import tabulate

# 2017/6/4修改: 去除总资产的动态权益计算


class QA_Account:
    """
    账户类:    
    记录回测的时候的账户情况(持仓列表,交易历史,利润,报单,可用资金)
    """
    # 一个hold改成list模式

    def __init__(self):

        self.hold = [['date', 'code', ' price',
                      'amount', 'order_id', 'trade_id']]
        self.init_assest = 1000000
        self.cash = []
        self.history = []
        self.detail = []
        self.assets = []
        self.profit = []
        self.account_cookie = str()
        self.message = {}

    def init(self):
        self.hold = [['date', 'code', ' price',
                      'amount', 'order_id', 'trade_id']]
        self.history = []
        self.profit = []
        self.account_cookie = str(random.random())
        self.cash = [self.init_assest]
        self.message = {
            'header': {
                'source': 'account',
                'cookie': self.account_cookie,
                'session': {
                    'user': '',
                    'strategy': ''
                }
            },
            'body': {
                'account': {
                    'hold': self.hold,
                    'cash': self.cash,
                    'assets': self.cash,
                    'history': self.history,
                    'detail': self.detail
                },
                #'time':datetime.datetime.now(),
                'date_stamp': str(time.mktime(datetime.datetime.now().timetuple()))
            }
        }

    def QA_account_update(self, __update_message):
        if str(__update_message['status'])[0] == '2':
            # 这里就是买卖成功的情况
            # towards>1 买入成功
            # towards<1 卖出成功

            __new_code = __update_message['bid']['code']
            __new_amount = __update_message['bid']['amount']
            __new_trade_date = __update_message['bid']['date']
            __new_towards = __update_message['bid']['towards']
            __new_price = __update_message['bid']['price']
            __new_order_id = __update_message['order_id']
            __new_trade_id = __update_message['trade_id']
            self.history.append(
                [__new_trade_date, __new_code, __new_price, __new_towards,
                 __new_amount, __new_order_id, __new_trade_id])
            # 先计算收益和利润

            # 修改持仓表
            if int(__new_towards) > 0:

                self.hold.append(
                    [__new_trade_date, __new_code, __new_price, __new_amount,
                     __new_order_id, __new_trade_id])
                self.detail.append([__new_trade_date, __new_code, __new_price,
                                    __new_amount, __new_order_id, __new_trade_id,
                                    [], [], [], [], __new_amount])
                # 将交易记录插入历史交易记录
            else:
                # 更新账户
                __pop_list = []
                while __new_amount > 0:

                    if len(self.hold) > 1:
                        for i in range(0, len(self.hold)):

                            if __new_code in self.hold[i]:
                                if __new_amount > self.hold[i][3]:

                                    __new_amount = __new_amount - \
                                        self.hold[i][3]

                                    __pop_list.append(i)

                                elif __new_amount < self.hold[i][3]:
                                    self.hold[i][3] = self.hold[i][3] - \
                                        __new_amount

                                    for item_detail in self.detail:
                                        if item_detail[5] == self.hold[i][5] and \
                                                __new_trade_id not in item_detail[7]:
                                            item_detail[6].append(__new_price)
                                            item_detail[7].append(
                                                __new_order_id)
                                            item_detail[8].append(
                                                __new_trade_id)
                                            item_detail[9].append(
                                                __new_trade_date)
                                            item_detail[10] = self.hold[i][3] - \
                                                __new_amount
                                    __new_amount = 0
                                elif __new_amount == self.hold[i][3]:

                                    __new_amount = 0
                                    __pop_list.append(i)

                __pop_list.sort()
                __pop_list.reverse()
                for __id in __pop_list:

                    for item_detail in self.detail:
                        if item_detail[5] == self.hold[__id][5] and \
                                __new_trade_id not in item_detail[7]:
                            item_detail[6].append(__new_price)
                            item_detail[7].append(__new_order_id)
                            item_detail[8].append(__new_trade_id)
                            item_detail[9].append(__new_trade_date)
                            item_detail[10] = 0
                    self.hold.pop(__id)
            # 将交易记录插入历史交易记录
        else:
            pass
        self.QA_account_calc_profit(__update_message)
        self.message = {
            'header': {
                'source': 'account',
                'cookie': self.account_cookie,
                'session': {
                    'user': __update_message['user'],
                    'strategy': __update_message['strategy'],
                    'code': __update_message['bid']['code']
                }

            },
            'body': {
                'account': {
                    'hold': self.hold,
                    'history': self.history,
                    'cash': self.cash,
                    'assets': self.assets,
                    'detail': tabulate(self.detail, headers=('date', 'code', 'price',
                                                             'amounts', 'sell_price', 'order_id', 'trade_id',
                                                             'sell_order_id', 'sell_trade_id', 'left_amount'))
                },
                'time': str(datetime.datetime.now()),
                'date_stamp': str(time.mktime(datetime.datetime.now().timetuple()))
            }
        }

        return self.message

    def QA_account_calc_profit(self, __update_message):
        if __update_message['status'] == 200 and __update_message['bid']['towards'] == 1:
            # 买入/
            # 证券价值=买入的证券价值+持有到结算(收盘价)的价值

            # 买入的部分在update_message

            # 可用资金=上一期可用资金-买入的资金
            self.cash.append(float(self.cash[-1]) - float(
                __update_message['bid']['price']) * float(
                    __update_message['bid']['amount']) * __update_message['bid']['towards'])

        elif __update_message['status'] == 200 and __update_message['bid']['towards'] == -1:
            # success trade,sell
            # 证券价值=买入的证券价值+持有到结算(收盘价)的价值
            # 买入的部分在update_message

            # 卖出的时候,towards=-1,所以是加上卖出的资产
            # 可用资金=上一期可用资金+卖出的资金
            self.cash.append(float(self.cash[-1]) - float(
                __update_message['bid']['price']) * float(
                    __update_message['bid']['amount']) * __update_message['bid']['towards'])

            # 更新可用资金历史

            # hold
        market_value = 0
        for i in range(1, len(self.hold)):
            market_value += (float(self.hold[i][2]) * float(self.hold[i][3]))
        self.assets.append(self.cash[-1] + market_value)

    def QA_account_receive_deal(self, __message):
        # 主要是把从market拿到的数据进行解包,一个一个发送给账户进行更新,再把最后的结果反回
        __data = self.QA_account_update({
            'code': __message['header']['code'],
            'status': __message['header']['status'],
            'user': __message['header']['session']['user'],
            'strategy': __message['header']['session']['strategy'],
            'trade_id': __message['header']['trade_id'],
            'order_id': __message['header']['order_id'],
            'date_stamp': str(time.mktime(datetime.datetime.now().timetuple())),
            'bid': __message['body']['bid'],
            'market': __message['body']['market']
        })
        return __data
