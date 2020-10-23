import gc
import os
import psutil
import tqdm
from zipf import Zipf
from sticky_sampling import StickySampling
from lossy_counting import LossyCounting
from space_saving import SpaceSaving
from baseline import Baseline


def mem():
    gc.collect()
    process = psutil.Process(os.getpid())
    return process.memory_info().rss


def test(z: int, distinct_nums: int, s: float, d: float, stream_size: int):
    zipf = Zipf(z, distinct_nums)
    zipf.proof(stream_size)
    e = s / 10

    baseline_ = Baseline()
    for num in tqdm.tqdm(zipf.stream, desc="Baseline"):
        baseline_.feed(num)

    sticky_sampling_ = StickySampling(s=s, e=e, d=d)
    for num in tqdm.tqdm(zipf.stream, desc="StickySampling"):
        sticky_sampling_.feed(num)

    lossy_counting_ = LossyCounting(s=s, e=e)
    for num in tqdm.tqdm(zipf.stream, desc="LossyCounting"):
        lossy_counting_.feed(num)

    space_sampling_ = SpaceSaving(1 / s)
    for num in tqdm.tqdm(zipf.stream, desc="SpaceSampling"):
        space_sampling_.feed(num)

    baseline_res = baseline_.request(s)
    print(baseline_res)

    lossy_counting__res = lossy_counting_.request()
    print(lossy_counting__res)

    sticky_sampling_res = sticky_sampling_.request()
    print(sticky_sampling_res)

    space_sampling_res = space_sampling_.request()
    print(space_sampling_res)


def run():
    test(z=2, distinct_nums=100, s=0.01, d=0.01, stream_size=100000)
