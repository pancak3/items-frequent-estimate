"""
Updated on Oct 2020
@author: Qifan Deng
"""

import random
from collections import defaultdict
from pandas import DataFrame, read_csv
import matplotlib.pyplot as plt
from scipy.special import zeta
import tqdm
import os
import numpy   as np
from math import log
from joblib import load, dump
from helpers import sci


class Zipf:

    def __init__(self, z: float, distinct_nums: int):
        self.distinct_nums = distinct_nums
        self.items = [i for i in range(1, distinct_nums + 2)]
        self.z = z
        self.probabilities = [1 / (i ** z) / zeta(self.z) for i in range(1, distinct_nums + 2)]
        self.probabilities = np.array(self.probabilities)
        self.probabilities /= self.probabilities.sum()
        self.stream = []
        self.df = None
        self.total = 0

    def gen(self):
        num = random.choices(self.items, self.probabilities)[0]
        self.stream.append(num)
        self.total += 1
        return num

    def request(self, s):
        ret = set([])
        for index, row in self.df.iterrows():
            if row["prob"] >= s:
                ret.add(index)
            else:
                break
        return ret

    def proof(self, stream_size: int, draw=True):

        df_filename = "zipf-{}-{}-stream-{}.df".format(self.z, self.distinct_nums, stream_size)
        stream_filename = "zipf-{}-{}-stream-{}.in".format(self.z, self.distinct_nums, stream_size)
        if os.path.exists(df_filename):
            # print("[*] read {} {}".format(stream_filename, df_filename))
            df = read_csv(df_filename, index_col="index")
            self.stream = load(stream_filename)
        else:
            records = defaultdict(lambda: {"count": 0, "prob": .0})
            if os.path.exists(stream_filename):
                # print("[*] load stream: {}".format(stream_filename))
                self.stream = load(stream_filename)
                for num in tqdm.tqdm(self.stream, desc="zipf count"):
                    records[num]["count"] += 1
            else:
                # for _ in tqdm.tqdm(range(0, stream_size), desc="zipf gen and count"):
                for _ in range(0, stream_size):
                    num = self.gen()
                    records[num]["count"] += 1
                # print("[*] dump stream: {}".format(stream_filename))
                dump(self.stream, filename=stream_filename)
            self.total = 0

            for value in records.values():
                self.total += value["count"]

            for key, value in records.items():
                records[key]["prob"] = value["count"] / self.total
                records[key]["theory"] = self.probabilities[key - 1]

            df = DataFrame(data=records, columns=records.keys()).T
            df = df.sort_index()
            df['index'] = df.index
            df.to_csv(path_or_buf=df_filename, index=False)

        self.df = df

        if draw:
            greater = df["count"][df["prob"] >= .01].sum()
            plt.figure()
            ax = df.theory.plot(label="In Theory", style='.', logy=True, legend=True)
            df.prob.plot(label="Observed", style='.', logy=True, legend=True)
            ax.set_xlabel(r'$i^{th}$ most frequent item')
            ax.set_ylabel(r'Probability')
            ax.axhline(y=.01, ls="--", label="1%", color="gray")
            ax.annotate(r'$\geq$1%: {} out of {}'.format(sci(greater), sci(stream_size)), (10, 0.05))
            plt.legend()
            plt.title(r'Power-law Distribution; $z = {}$, {} items'.format(self.z, sci(stream_size)))
            plt.show()
            ax.get_figure().savefig(
                'report/eps/zipf-{}-{}-stream-{}.eps'.format(self.z, self.distinct_nums, stream_size),
                format='eps')
