import random
import numpy as np
from collections import defaultdict
from pandas import DataFrame
import matplotlib.pyplot as plt
from scipy.special import zeta
import tqdm
import os
import psutil
import gc


def mem():
    gc.collect()
    process = psutil.Process(os.getpid())
    return process.memory_info().rss


class StickySampling:

    def __init__(self):
        pass


class Zipf:

    def __init__(self, low: int, high: int, z: int):
        self.low = low
        self.high = high
        self.items = [i for i in range(low, high + 1)]
        self.counter = [0 for _ in range(low, high + 1)]
        self.z = z
        self.probabilities = [1 / (i ** z) / zeta(self.z) for i in range(1, high - low + 2)]
        self.stream = []

    def gen(self):
        num = random.choices(self.items, self.probabilities)[0]
        self.counter[num - self.low] += 1
        self.stream.append(num)
        return num

    def proof(self, tests: int):

        records = defaultdict(lambda: {"count": 0, "prob": .0})
        for _ in tqdm.tqdm(range(0, tests), desc="zipf"):
            num = self.gen()
            self.stream.append(num)
            records[num]["count"] += 1

        total = 0
        for key, value in records.items():
            total += value["count"]

        for key, value in records.items():
            records[key]["prob"] = value["count"] / total
            records[key]["theory"] = self.probabilities[key - 1]

        df = DataFrame(data=records, columns=records.keys()).T
        df = df.sort_index()

        plt.figure()
        df.theory.plot(label="Probability in Theory", style='.', logy=True, legend=True)
        df.prob.plot(label="Probability Observed", style='.', logy=True, legend=True)
        plt.show()
        plt.savefig('report/eps/zipf.eps', format='eps')
        return


class LossyCounting:

    def __init__(self, s, e):
        self.s = s
        self.e = e
        self.d, self.m = 0, 0
        self.counter = {}
        self.k = 1 / e

    def feed(self, x):
        self.m += 1
        if x in self.counter:
            self.counter[x] += 1
        else:
            self.counter[x] = 1 + self.d
        tmp = round(self.m / self.k)
        if self.d != tmp:
            self.d = tmp
            _counter = defaultdict(lambda: 0)
            for num, count in self.counter.items():
                if count != self.d:
                    _counter[num] = count
            self.counter = _counter

    def res(self):
        ret = set([])
        for key, value in self.counter.items():
            if value > self.m * (self.s - self.e):
                ret.add(key)
        return ret


if __name__ == '__main__':
    zipf = Zipf(1, 100, 2)
    lc = LossyCounting(0.02, 0.01)
    for i in range(0, 10000):
        lc.feed(zipf.gen())
    lcRes = lc.res(),
    zipfTrue = set(zipf.items[:len(lc.counter)])
    print(lcRes, zipfTrue)
