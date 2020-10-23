import tqdm
import os
import psutil
import gc
from zipf import Zipf
from sticky_sampling import StickySampling
from lossy_counting import LossyCounting
from space_saving import SpaceSaving


def mem():
    gc.collect()
    process = psutil.Process(os.getpid())
    return process.memory_info().rss


if __name__ == '__main__':
    zipf = Zipf(1, 100, 2)
    zipf.proof(100000)

    s = 0.001
    e = s / 10
    d = 0.001

    sticky_sampling_ = StickySampling(s=s, e=e, d=d)
    for num in tqdm.tqdm(zipf.stream, desc="StickySampling"):
        sticky_sampling_.feed(num)

    lossy_counting_ = LossyCounting(s=s, e=e)
    for num in tqdm.tqdm(zipf.stream, desc="LossyCounting"):
        lossy_counting_.feed(num)

    space_sampling_ = SpaceSaving(1 / s)
    for num in tqdm.tqdm(zipf.stream, desc="SpaceSampling"):
        space_sampling_.feed(num)

    zipfTrue = zipf.request(s)

    lcRes = lossy_counting_.request()
    print(lcRes, zipfTrue)

    ssRes = sticky_sampling_.request()
    print(ssRes, zipfTrue)

    ss_Res = space_sampling_.request()
    print(ss_Res, zipfTrue)
    print()
