"""
Updated on Oct 2020
@author: Qifan Deng
"""

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
from time import time, sleep
from random import randint
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

        real_counts = {}
        for i, item in enumerate(baseline_res[0]):
            real_counts[item] = baseline_res[1][i]

        estimate_counts = {}
        for i, item in enumerate(res[0]):
            estimate_counts[item] = res[1][i]

        relative_err = 0
        for i, x0 in enumerate(baseline_res[0]):
            if i >= len(res[0]):
                x1 = 0
            else:
                x1 = res[0][i]
            relative_err += abs(x1 - x0) / x0
        self.average_relative_error = relative_err / len(baseline_res[0])


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
                                 sticky_sampling_.max_tracked,
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
                                lossy_counting_.max_tracked,
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
                                space_sampling_.max_tracked,
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
    # ax = max_tracked_vs_support.Baseline.plot(label="Baseline", style='_', legend=True)
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
    # ax = runtime_vs_support.Baseline.plot(label="Baseline", style='_-', legend=True)
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
    # ax = max_tracked_vs_runtime.Baseline.plot(label="Baseline", style='_', legend=True)
    ax = max_tracked_vs_runtime.StickySampling.plot(label="StickySampling", style='1', legend=True)
    ax = max_tracked_vs_runtime.LossyCounting.plot(label="LossyCounting", style='|', legend=True)
    max_tracked_vs_runtime.SpaceSaving.plot(label="SpaceSaving", style='.', legend=True)
    ax.set_xlabel(r'Runtime (Micro Seconds)')
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


def average_relative_error(low: float, high: float, size: int, z: float, distinct_nums: int, d: float,
                           stream_size: int):
    df_average_relative_err = DataFrame(data=[], index=["StickySampling", "LossyCounting", "SpaceSaving"])

    ss = np.linspace(low, high, size, endpoint=True)
    zipf = Zipf(z, distinct_nums)
    zipf.proof(stream_size, draw=False)

    def calc_relative_err(res, real_):
        if not len(res[0]):
            return 0
        s_ = 0
        for i, item in enumerate(res[0]):
            s_ += abs(res[1][i] - real_[item]) / real_[item]
        return s_ / len(res[0])

    baseline_ = Baseline()
    for num in zipf.stream:
        baseline_.feed(num)
    real_res = baseline_.request(0)
    real_counts = {}
    for i, item in enumerate(real_res[0]):
        real_counts[item] = real_res[1][i]

    for s in tqdm.tqdm(ss, desc="AverageRelative-Supports"):
        sticky_sampling_ = StickySampling(s=s, e=s / 10, d=d)
        lossy_counting_ = LossyCounting(s=s, e=s / 10)
        space_sampling_ = SpaceSaving(1 / s)

        for num in zipf.stream:
            sticky_sampling_.feed(num)
            lossy_counting_.feed(num)
            space_sampling_.feed(num)

        sticky_sampling_res = sticky_sampling_.request()
        lossy_counting_res = lossy_counting_.request()
        space_sampling_res = space_sampling_.request()

        sticky_sampling_average_relative_err = calc_relative_err(sticky_sampling_res, real_counts)
        lossy_counting_average_relative_err = calc_relative_err(lossy_counting_res, real_counts)
        space_sampling_average_relative_err = calc_relative_err(space_sampling_res, real_counts)

        df_average_relative_err[s] = [sticky_sampling_average_relative_err,
                                      lossy_counting_average_relative_err,
                                      space_sampling_average_relative_err]

    df_average_relative_err = df_average_relative_err.T
    print('Average Relative Error vs Support')
    print(df_average_relative_err)
    plt.figure()
    ax = df_average_relative_err.StickySampling.plot(label="StickySampling", style='1-', legend=True)
    ax = df_average_relative_err.LossyCounting.plot(label="LossyCounting", style='|-', legend=True)
    ax2 = df_average_relative_err.SpaceSaving.plot(label="SpaceSaving", style='.-', legend=True, secondary_y=True)
    ax.set_xlabel(r'Support $s$ ')
    ax.set_ylabel(r'Average Relative Error')
    ax2.set_ylabel(r'Average Relative Error of SpaceSaving')
    # plt.legend()
    plt.title(r'Average Relative Error vs Support')
    plt.show()
    ax.get_figure().savefig(
        'report/eps/AverageRelativeError-Support-zipf-{}-{}-delta-{}-stream-{}.eps'.format(z, distinct_nums, d,
                                                                                           stream_size),
        format='eps')


def precision_runtime_vs_z(repeat: int, low: float, high: float, size: int, s: float, distinct_nums: int,
                           stream_size: int):
    indexes = ["Baseline", "StickySampling",
               "LossyCounting", "SpaceSaving"]
    precision_vs_skew = {}
    runtime_vs_skew = {}

    zs = np.linspace(low, high, size)
    e = s / 10
    d = 1 / s
    for z in tqdm.tqdm(zs, desc="Skew,z"):
        zipf = Zipf(z, distinct_nums)
        zipf.proof(stream_size, draw=False)

        for i in range(repeat):

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
                                         sticky_sampling_.max_tracked,
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
                                        lossy_counting_.max_tracked,
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
                                        space_sampling_.max_tracked,
                                        space_sampling_.request(),
                                        baseline_res_,
                                        zipf.items,
                                        time() - start_time)

            df = DataFrame(data=[vars(baseline_res).values(),
                                 vars(sticky_sampling_res).values(),
                                 vars(lossy_counting_res).values(),
                                 vars(space_sampling_res).values()],
                           columns=vars(baseline_res).keys())
            df.index = indexes
            if z not in precision_vs_skew:
                precision_vs_skew[z] = df["precision"]
                runtime_vs_skew[z] = df["time_cost"]
            else:
                precision_vs_skew[z] += df["precision"]
                runtime_vs_skew[z] += df["time_cost"]

    precision_vs_skew = DataFrame(precision_vs_skew).T
    runtime_vs_skew = DataFrame(runtime_vs_skew).T

    precision_vs_skew = precision_vs_skew.div(repeat)
    runtime_vs_skew = runtime_vs_skew.div(repeat)

    if repeat > 1:
        title_log = '[*] Average Precision vs Skew $z$; $s={}$'.format(s)
    else:
        title_log = '[*] Precision vs Skew $z$; $s={}$'.format(s)
    print(title_log)
    print(precision_vs_skew)

    if repeat > 1:
        title_log = '[*] Average Precision vs Skew $z$; $s={}$'.format(s)
    else:
        title_log = '[*] Precision vs Skew $z$; $s={}$'.format(s)
    print(title_log)
    print(runtime_vs_skew)

    plt.figure()
    ax = precision_vs_skew.StickySampling.plot(label="StickySampling", style='1-', legend=True)
    ax = precision_vs_skew.LossyCounting.plot(label="LossyCounting", style='|-', legend=True)
    precision_vs_skew.SpaceSaving.plot(label="SpaceSaving", style='.-', legend=True)
    ax.set_xlabel(r'Skew $z$ ')
    if repeat > 1:
        ax.set_ylabel(r'Average Precision')
        plt.title(r'Average Precision vs Skew $z$; $s={}$'.format(s))
    else:
        ax.set_ylabel(r'Precision')
        plt.title(r'Precision vs Skew $z$; $s={}$'.format(s))
    plt.legend()
    plt.show()
    ax.get_figure().savefig(
        'report/eps/Precision-Skew-s-{}-zipf-{}-delta-{}-stream-{}.eps'.format(s, distinct_nums, d, stream_size),
        format='eps')

    plt.figure()
    ax = runtime_vs_skew.StickySampling.plot(label="StickySampling", style='1-', legend=True)
    ax = runtime_vs_skew.LossyCounting.plot(label="LossyCounting", style='|-', legend=True)
    runtime_vs_skew.SpaceSaving.plot(label="SpaceSaving", style='.-', legend=True)
    ax.set_xlabel(r'Skew $z$ ')
    if repeat > 1:
        plt.title(r'Average Runtime vs Skew $z$; $s={}$'.format(s))
        ax.set_ylabel(r'Average Runtime (Micro Seconds)')
    else:
        plt.title(r'Runtime vs Skew $z$; $s={}$'.format(s))
        ax.set_ylabel(r'Runtime (Micro Seconds)')

    plt.legend()
    plt.show()
    ax.get_figure().savefig(
        'report/eps/Runtime-Skew-s-{}-zipf-{}-delta-{}-stream-{}.eps'.format(s, distinct_nums, d, stream_size),
        format='eps')


def run():
    z = 2.0
    d = 0.01

    power_law(distinct_nums=100,
              stream_size=1000000)

    precision_runtime_vs_z(low=1.1, high=5.1, size=100,
                           s=0.0001, repeat=1,
                           distinct_nums=1000,
                           stream_size=100000)

    support(low=0.00001, high=0.01, size=100, z=z,
            distinct_nums=10000, d=d,
            stream_size=100000)

    average_relative_error(low=0.00001, high=0.0125, size=100,
                           z=z,
                           distinct_nums=100,
                           d=d,
                           stream_size=100000)
