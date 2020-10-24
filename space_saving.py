from functools import cmp_to_key
from math import ceil


class EntrySpaceSaving:

    def __init__(self, e, f):
        self.e = e
        self.f = f


class SpaceSaving:

    def __init__(self, t):
        self.t = ceil(t)
        self.C = {}
        self.SortedC = []

    def sort_entries(self):
        self.SortedC = self.C.values()
        sorted(self.SortedC, key=lambda x: x.f)
        self.SortedC = list(self.SortedC)

    def feed(self, x):
        if x in self.C:
            # increment the counter of e
            self.C[x].f += 1
        elif len(self.C) < self.t:
            self.sort_entries()
            self.C[x] = EntrySpaceSaving(x, 1)
        else:
            # let em be the element with least hits, min
            # replace em with e
            # Assign count_m the value min + 1
            self.sort_entries()
            self.C[x] = EntrySpaceSaving(x, self.SortedC[0].f + 1)
            del self.C[self.SortedC[0].e]

    def request(self):
        ret = [[], []]
        for entry in self.C.values():
            ret[0].append(entry.e)
            ret[1].append(entry.f)
        return ret
