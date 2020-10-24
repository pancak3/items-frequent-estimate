import gc
import os
import psutil
import tqdm
from zipf import Zipf
from sticky_sampling import StickySampling
from lossy_counting import LossyCounting
from space_saving import SpaceSaving
from baseline import Baseline
from time import time
from pprint import pprint
from pandas import DataFrame


class Result:
    def __init__(self, algorithm_name, time_cost, counters_used, res, baseline_res, all_items):
        self.algorithm = algorithm_name
        self.time_cost = time_cost
        self.counters_used = counters_used

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


def test(z: float, distinct_nums: int, s: float, d: float, stream_size: int):
    zipf = Zipf(z, distinct_nums)
    zipf.proof(stream_size)
    e = s / 10

    start_time = time()
    baseline_ = Baseline()
    for num in tqdm.tqdm(zipf.stream, desc="Baseline"):
        baseline_.feed(num)

    baseline_res_ = baseline_.request(s)

    baseline_res = Result("Baseline",
                          time() - start_time,
                          len(baseline_.counter),
                          baseline_res_,
                          baseline_res_,
                          zipf.items)

    start_time = time()
    sticky_sampling_ = StickySampling(s=s, e=e, d=d)
    for num in tqdm.tqdm(zipf.stream, desc="StickySampling"):
        sticky_sampling_.feed(num)
    sticky_sampling_res = Result("StickySampling",
                                 time() - start_time,
                                 len(sticky_sampling_.S),
                                 sticky_sampling_.request(),
                                 baseline_res_,
                                 zipf.items)

    start_time = time()
    lossy_counting_ = LossyCounting(s=s, e=e)
    for num in tqdm.tqdm(zipf.stream, desc="LossyCounting"):
        lossy_counting_.feed(num)
    lossy_counting_res = Result("LossyCounting",
                                time() - start_time,
                                len(lossy_counting_.D),
                                lossy_counting_.request(),
                                baseline_res_,
                                zipf.items)

    start_time = time()
    space_sampling_ = SpaceSaving(1 / s)
    for num in tqdm.tqdm(zipf.stream, desc="SpaceSaving"):
        space_sampling_.feed(num)
    space_sampling_res = Result("SpaceSaving",
                                time() - start_time,
                                len(space_sampling_.C),
                                space_sampling_.request(),
                                baseline_res_,
                                zipf.items)

    df = DataFrame(data=[vars(baseline_res).values(),
                         vars(sticky_sampling_res).values(),
                         vars(lossy_counting_res).values(),
                         vars(space_sampling_res).values()],
                   columns=vars(baseline_res).keys())
    print(df)


def power_law():
    zs = [1.1, 1.4, 1.7, 2.0]

    for z in zs:
        zipf = Zipf(z, 100)
        zipf.proof(1000000)


def run():
    test(z=2.0, distinct_nums=100, s=0.0001, d=0.01, stream_size=1000000)

    # power_law()
