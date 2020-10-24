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


class Result:
    def __init__(self, time_cost, counters_count, res, baseline_res):
        self.time_cost = time_cost
        self.counters_count = counters_count

        estimate, actual = set(res[0]), set(baseline_res[0])
        self.precision = len(estimate.intersection(actual)) / len(estimate)
        self.accuracy = len(estimate.intersection(actual)) / len(estimate.union(actual))


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

    baseline_res = baseline_.request(s)

    baseline_res_ = Result(time() - start_time,
                           len(baseline_.counter),
                           baseline_res,
                           baseline_res)
    pprint(vars(baseline_res_))

    start_time = time()
    sticky_sampling_ = StickySampling(s=s, e=e, d=d)
    for num in tqdm.tqdm(zipf.stream, desc="StickySampling"):
        sticky_sampling_.feed(num)
    sticky_sampling_res = Result(time() - start_time,
                                 len(sticky_sampling_.S),
                                 sticky_sampling_.request(),
                                 baseline_res)
    pprint(vars(sticky_sampling_res))

    start_time = time()
    lossy_counting_ = LossyCounting(s=s, e=e)
    for num in tqdm.tqdm(zipf.stream, desc="LossyCounting"):
        lossy_counting_.feed(num)
    lossy_counting_res = Result(time() - start_time,
                                len(lossy_counting_.D),
                                lossy_counting_.request(),
                                baseline_res)
    pprint(vars(lossy_counting_res))

    start_time = time()
    space_sampling_ = SpaceSaving(10)
    for num in tqdm.tqdm(zipf.stream, desc="SpaceSaving"):
        space_sampling_.feed(num)
    space_sampling_res = Result(time() - start_time,
                                len(space_sampling_.C),
                                space_sampling_.request(),
                                baseline_res)
    pprint(vars(space_sampling_res))


def power_law():
    zs = [1.1, 1.4, 1.7, 2.0]

    for z in zs:
        zipf = Zipf(z, 100)
        zipf.proof(1000000)


def run():
    test(z=2.0, distinct_nums=100, s=0.0001, d=0.01, stream_size=1000000)

    # power_law()
