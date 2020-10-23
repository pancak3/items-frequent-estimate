from math import floor, ceil


class EntryLossyCounting:

    def __init__(self, e, f, d):
        self.e = e
        self.f = f
        self.d = d


class LossyCounting:

    def __init__(self, s, e: float):
        self.e = e
        self.s = s
        self.d, self.N = 0, 0
        self.D = {}
        self.w = floor(1 / e)
        self.N = 0

    def get_b_curr(self):
        return ceil(self.N / self.w)

    def feed(self, x: int):
        self.N += 1
        if x in self.D:
            self.D[x].f += 1
        else:
            self.D[x] = EntryLossyCounting(x, 1, self.get_b_curr() - 1)

        if self.N == 0 % self.w:
            D = {}
            for entry in self.D.values():
                if entry.f + entry.d > self.get_b_curr():
                    D[entry.e] = entry
            self.D = D

    def request(self):
        ret = set()
        for entry in self.D.values():
            if entry.f >= self.N * (self.s - self.e):
                ret.add(entry.e)
        return ret
