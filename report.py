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
    def __init__(self, time_cost, mem_cost, res, baseline_res):
        self.time_cost = time_cost
        self.mem_cost = mem_cost

        estimate, actual = set(res[0]), set(baseline_res[0])
        self.precision = len(estimate.intersection(actual)) / len(estimate)


def mem(garbage_collection=False):
    if garbage_collection:
        gc.collect()
    process = psutil.Process(os.getpid())
    return process.memory_info().rss


def test(z: int, distinct_nums: int, s: float, d: float, stream_size: int):
    zipf = Zipf(z, distinct_nums)
    zipf.proof(stream_size)
    e = s / 10

    start_time = time()
    start_mem = mem(garbage_collection=False)
    baseline_ = Baseline()
    for num in tqdm.tqdm(zipf.stream, desc="Baseline"):
        baseline_.feed(num)

    baseline_res = baseline_.request(s)

    baseline_res_ = Result(time() - start_time,
                           mem() - start_mem,
                           baseline_res,
                           baseline_res)
    pprint(vars(baseline_res_))

    start_time = time()
    start_mem = mem(garbage_collection=False)
    sticky_sampling_ = StickySampling(s=s, e=e, d=d)
    for num in tqdm.tqdm(zipf.stream, desc="StickySampling"):
        sticky_sampling_.feed(num)
    sticky_sampling_res = Result(time() - start_time,
                                 mem() - start_mem,
                                 sticky_sampling_.request(),
                                 baseline_res)
    pprint(vars(sticky_sampling_res))

    start_time = time()
    start_mem = mem(garbage_collection=False)
    lossy_counting_ = LossyCounting(s=s, e=e)
    for num in tqdm.tqdm(zipf.stream, desc="LossyCounting"):
        lossy_counting_.feed(num)
    lossy_counting_res = Result(time() - start_time,
                                mem() - start_mem,
                                lossy_counting_.request(),
                                baseline_res)
    pprint(vars(lossy_counting_res))

    start_time = time()
    start_mem = mem(garbage_collection=False)
    space_sampling_ = SpaceSaving(1 / s)
    for num in tqdm.tqdm(zipf.stream, desc="SpaceSampling"):
        space_sampling_.feed(num)
    space_sampling_res = Result(time() - start_time,
                                mem() - start_mem,
                                space_sampling_.request(),
                                baseline_res)
    pprint(vars(space_sampling_res))


def run():
    test(z=2, distinct_nums=100, s=0.0001, d=0.01, stream_size=100000000)
