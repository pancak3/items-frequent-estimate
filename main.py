import random
import numpy as np
from collections import defaultdict
from pandas import DataFrame, read_csv
import matplotlib.pyplot as plt
from scipy.special import zeta
import tqdm
import os
import psutil
import gc
from zipf import Zipf
from sticky_sampling import StickySampling
from lossy_counting import LossyCounting


def mem():
    gc.collect()
    process = psutil.Process(os.getpid())
    return process.memory_info().rss


if __name__ == '__main__':
    zipf = Zipf(1, 100, 2)
    zipf.proof(10000)

    s = 0.001
    e = s / 10
    d = 0.001
    ss = StickySampling(s=s, e=e, d=d)
    for num in tqdm.tqdm(zipf.stream, desc="StickySampling"):
        ss.feed(num)
    lc = LossyCounting(s=s, e=e)
    for num in tqdm.tqdm(zipf.stream, desc="LossyCounting"):
        lc.feed(num)

    zipfTrue = zipf.request(s)
    lcRes = lc.request()
    print(lcRes, zipfTrue)

    ssRes = ss.request()
    print(ssRes, zipfTrue)
