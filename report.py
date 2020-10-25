import gc
import os
import psutil
import tqdm
import numpy as np
from matplotlib import pyplot as plt
from zipf import Zipf
from sticky_sampling import StickySampling
from lossy_counting import LossyCounting
from space_saving import SpaceSaving
from baseline import Baseline
from time import time
from pprint import pprint
from pandas import DataFrame
from matplotlib.ticker import ScalarFormatter


class Result:
    def __init__(self, algorithm_name, max_tracked, res, baseline_res, all_items, time_cost):
        self.algorithm = algorithm_name
        self.time_cost = time_cost * 1000
        self.max_tracked = max_tracked

        estimate, actual, all_items = set(res[0]), set(baseline_res[0]), set(all_items)
        tp = len(estimate.intersection(actual))
        tn = len(all_items.difference(estimate).intersection(all_items.difference(actual)))
        fp = len(estimate.difference(actual))
        fn = len(all_items.difference(estimate).intersection(actual))
        # Accuracy = (TP + TN) / (TP + TN + FP + FN)
        # Precision = TP / (TP + FP)
        self.precision = tp / (tp + fp)
        self.accuracy = (tp + tn) / (tp + tn + fp + fn)


def mem(garbage_collection=False):
    if garbage_collection:
        gc.collect()
    process = psutil.Process(os.getpid())
    return process.memory_info().rss


def test(zipf: Zipf, s: float, d: float):
    e = s / 10

    start_time = time()
    baseline_ = Baseline()
    # for num in tqdm.tqdm(zipf.stream, desc="Baseline"):
    for num in zipf.stream:
        baseline_.feed(num)

    baseline_res_ = baseline_.request(s)

    baseline_res = Result("Baseline",
                          len(baseline_.counter),
                          baseline_res_,
                          baseline_res_,
                          zipf.items,
                          time() - start_time)

    start_time = time()
    sticky_sampling_ = StickySampling(s=s, e=e, d=d)
    # for num in tqdm.tqdm(zipf.stream, desc="StickySampling"):
    for num in zipf.stream:
        sticky_sampling_.feed(num)
    sticky_sampling_res = Result("StickySampling",
                                 len(sticky_sampling_.S),
                                 sticky_sampling_.request(),
                                 baseline_res_,
                                 zipf.items,
                                 time() - start_time)

    start_time = time()
    lossy_counting_ = LossyCounting(s=s, e=e)
    # for num in tqdm.tqdm(zipf.stream, desc="LossyCounting"):
    for num in zipf.stream:
        lossy_counting_.feed(num)
    lossy_counting_res = Result("LossyCounting",
                                len(lossy_counting_.D),
                                lossy_counting_.request(),
                                baseline_res_,
                                zipf.items,
                                time() - start_time)

    start_time = time()
    space_sampling_ = SpaceSaving(1 / s)
    # for num in tqdm.tqdm(zipf.stream, desc="SpaceSaving"):
    for num in zipf.stream:
        space_sampling_.feed(num)
    space_sampling_res = Result("SpaceSaving",
                                len(space_sampling_.C),
                                space_sampling_.request(),
                                baseline_res_,
                                zipf.items,
                                time() - start_time)

    df = DataFrame(data=[vars(baseline_res).values(),
                         vars(sticky_sampling_res).values(),
                         vars(lossy_counting_res).values(),
                         vars(space_sampling_res).values()],
                   columns=vars(baseline_res).keys())
    return df


def power_law(distinct_nums: int, stream_size: int):
    zs = [1.1, 1.4, 1.7, 2.0]

    for z in zs:
        zipf = Zipf(z, distinct_nums)
        zipf.proof(stream_size)


def support(low: float, high: float, size: int, z: float, distinct_nums: int, d: float, stream_size: int):
    max_tracked_vs_support = DataFrame(data=[],
                                       index=["Baseline", "StickySampling",
                                              "LossyCounting", "SpaceSaving"])
    runtime_vs_support = DataFrame(data=[],
                                   index=["Baseline", "StickySampling",
                                          "LossyCounting", "SpaceSaving"])
    max_tracked_vs_runtime = {"Baseline": {},
                              "StickySampling": {},
                              "LossyCounting": {},
                              "SpaceSaving": {}
                              }

    ss = np.linspace(low, high, size, endpoint=True)
    zipf = Zipf(z, distinct_nums)
    zipf.proof(stream_size, draw=False)
    for s in tqdm.tqdm(ss, desc="Supports"):
        df = test(zipf=zipf, s=s, d=d)
        max_tracked_vs_support[str(s)] = list(df["max_tracked"])
        runtime_vs_support[str(s)] = list(df["time_cost"])
        for index, algorithm_name in enumerate(max_tracked_vs_runtime.keys()):
            max_tracked = max_tracked_vs_support.T[algorithm_name]
            for i, time_cost in enumerate(runtime_vs_support.T[algorithm_name]):
                max_tracked_vs_runtime[algorithm_name][time_cost] = max_tracked[i]
    max_tracked_vs_runtime = DataFrame(max_tracked_vs_runtime).sort_index()

    max_tracked_vs_support = max_tracked_vs_support.T
    indexes = [float(i) for i in max_tracked_vs_support.index]
    max_tracked_vs_support.index = indexes
    plt.figure()
    ax = max_tracked_vs_support.Baseline.plot(label="Baseline", style='_', legend=True)
    ax = max_tracked_vs_support.StickySampling.plot(label="StickySampling", style='1', legend=True)
    ax = max_tracked_vs_support.LossyCounting.plot(label="LossyCounting", style='|', legend=True)
    max_tracked_vs_support.SpaceSaving.plot(label="SpaceSaving", style='.', legend=True)
    ax.set_xlabel(r'Support $s$ ')
    ax.set_ylabel(r'Maximum Number of Tracked Items')
    plt.legend()
    plt.title(r'Maximum Number of Tracked Items vs Support')
    plt.show()
    ax.get_figure().savefig(
        'report/eps/MaxTracked-Support-zipf-{}-{}-delta-{}-stream-{}.eps'.format(z, distinct_nums, d, stream_size),
        format='eps')

    runtime_vs_support = runtime_vs_support.T
    indexes = [float(i) for i in runtime_vs_support.index]
    runtime_vs_support.index = indexes
    plt.figure()
    ax = runtime_vs_support.Baseline.plot(label="Baseline", style='_-', legend=True)
    ax = runtime_vs_support.StickySampling.plot(label="StickySampling", style='1-', legend=True)
    ax = runtime_vs_support.LossyCounting.plot(label="LossyCounting", style='|-', legend=True)
    runtime_vs_support.SpaceSaving.plot(label="SpaceSaving", style='.-', legend=True)
    ax.set_xlabel(r'Support $s$ ')
    ax.set_ylabel(r'Runtime (Micro Seconds)')
    plt.legend()
    plt.title(r'Runtime vs Support')
    plt.show()
    ax.get_figure().savefig(
        'report/eps/Runtime-Support-zipf-{}-{}-delta-{}-stream-{}.eps'.format(z, distinct_nums, d, stream_size),
        format='eps')

    plt.figure()
    ax = max_tracked_vs_runtime.Baseline.plot(label="Baseline", style='_-', legend=True)
    ax = max_tracked_vs_runtime.StickySampling.plot(label="StickySampling", style='1-', legend=True)
    ax = max_tracked_vs_runtime.LossyCounting.plot(label="LossyCounting", style='|-', legend=True)
    runtime_vs_support.SpaceSaving.plot(label="SpaceSaving", style='.-', legend=True)
    ax.set_xlabel(r'Runtime')
    ax.set_ylabel(r'Maximum Number of Tracked Items')
    plt.legend()
    plt.title(r'Maximum Number of Tracked Items vs Runtime')
    plt.show()
    ax.get_figure().savefig(
        'report/eps/MaxTracked-Runtime-zipf-{}-{}-delta-{}-stream-{}.eps'.format(z, distinct_nums, d, stream_size),
        format='eps')

    print(max_tracked_vs_support)
    print(runtime_vs_support)
    print(max_tracked_vs_runtime)


def run():
    z = 2.0
    distinct_nums = 1000
    d = 0.01
    stream_size = 100000

    # power_law(distinct_nums=distinct_nums, stream_size=stream_size)

    support(low=0.00001, high=0.01, size=100, z=z, distinct_nums=distinct_nums, d=d, stream_size=stream_size)
