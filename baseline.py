from collections import defaultdict


class Baseline:
    def __init__(self):
        self.counter = defaultdict(lambda: 0)
        self.total = 0

    def feed(self, x):
        self.counter[x] += 1
        self.total += 1

    def request(self, s):
        ret = [[], []]
        counter_in_order = {k: v for k, v in sorted(self.counter.items(), key=lambda item: item[1], reverse=True)}
        for e, count in counter_in_order.items():
            if count / self.total >= s:
                ret[0].append(e)
                ret[1].append(count)
            else:
                break
        return ret
