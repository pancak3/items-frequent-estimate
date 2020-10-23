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
from joblib import load, dump
from math import floor, ceil


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
        self.z = z
        self.probabilities = [1 / (i ** z) / zeta(self.z) for i in range(1, high - low + 2)]
        self.stream = []

    def gen(self):
        num = random.choices(self.items, self.probabilities)[0]
        self.stream.append(num)
        return num

    def proof(self, size: int):

        records = defaultdict(lambda: {"count": 0, "prob": .0})

        if os.path.exists("stream" + str(size)):
            print("[*] load stream from file")
            self.stream = load("stream" + str(size))
            for num in tqdm.tqdm(self.stream, desc="zipf"):
                records[num]["count"] += 1
        else:
            for _ in tqdm.tqdm(range(0, size), desc="zipf"):
                num = self.gen()
                self.stream.append(num)
                records[num]["count"] += 1
            print("[*] dump stream to file")
            dump(self.stream, "stream" + str(size))

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


class StickySampling:

    def __init__(self):
        pass


class Delta:

    def __init__(self, e, f, d):
        self.e = e
        self.f = f
        self.d = d


class LossyCounting:

    def __init__(self, s, e: float):
        self.e = e
        self.s = s
        self.d, self.N = 0, 0
        self.D = {}
        self.w = floor(1 / e)
        self.N = 0

    def get_b_curr(self):
        return ceil(self.N / self.w)

    def feed(self, x: int):
        self.N += 1
        if x in self.D:
            self.D[x].f += 1
        else:
            self.D[x] = Delta(x, 1, self.get_b_curr() - 1)

        if self.N == 0 % self.w:
            D = {}
            for e, item in self.D.items():
                if item.f + item.d > self.get_b_curr():
                    D[e] = item
            self.D = D

    def request(self):
        ret = set()
        for e, item in self.D.items():
            if item.f >= self.N * (self.s - self.e):
                ret.add(e)
        return ret


if __name__ == '__main__':
    zipf = Zipf(1, 100, 2)
    zipf.proof(100000000)

    lc = LossyCounting(s=0.001, e=0.0001)
    for num in tqdm.tqdm(zipf.stream, desc="LossyCounting"):
        lc.feed(num)
    lcRes = lc.request()
    zipfTrue = set(zipf.items[:len(lcRes)])
    print(lcRes, zipfTrue)
