"""
Updated on Oct 2020
@author: Qifan Deng
"""

import random
from math import ceil, log, floor


class EntryStickySampling:

    def __init__(self, e, f):
        self.e = e
        self.f = f


class StickySampling:

    def __init__(self, s, e, d):
        self.S = {}
        self.r = 1
        self.e = e
        self.d = d
        self.s = s
        self.t = ceil(1 / e * log(1 / (s * d)))
        self.N = 0
        self.max_tracked = 0

    def update_max_tracked(self):
        n = len(self.S)
        if n > self.max_tracked:
            self.max_tracked = n

    def get_rate(self):
        rate = 1 if self.N == 1 else 2 ** (floor(log(self.N - 1, 2)))
        if rate != self.r:
            S = {}
            for entry in self.S.values():
                # repeatedly toss an unbiased coin until the coin toss is successful
                coin = 1
                while coin:
                    #  we repeatedly toss an unbiased coin until the coin toss is successful,
                    #  diminishing by one for every unsuccessful outcome
                    coin = random.randint(0, 1)
                    entry.f -= 1
                # if f becomes 0 during this process, we delete the entry from S
                if entry.f > 0:
                    S[entry.e] = entry
            self.update_max_tracked()
            self.S = S
            self.r = rate
        return self.r

    def feed(self, x):
        self.N += 1
        if x in self.S:
            self.S[x].f += 1
        else:
            rate = 1 / self.get_rate()
            toll = random.choices([True, False], [rate, 1 - rate])
            if toll:
                self.S[x] = EntryStickySampling(e=x, f=1)
                self.update_max_tracked()

    def request(self):
        ret = [[], []]
        for entry in self.S.values():
            if entry.f >= self.N * (self.s - self.e):
                ret[0].append(entry.e)
                ret[1].append(entry.f)
        return ret
