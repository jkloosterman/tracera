from CacheSet import CacheSet
import math

class Cache(object):
    def __init__(self, mem_side, size_in_bytes, line_size, associativity, hit_latency, stats, name):
        self.num_lines = size_in_bytes / line_size
        self.num_sets = self.num_lines / associativity
        self.line_size = line_size
        self.line_bits = int(math.log(self.line_size, 2))
        self.stats = stats
        self.name = name
        self.active_sets = set()

        assert(self.num_sets > 0)

        self.sets = []
        for i in range(self.num_sets):
            self.sets.append(CacheSet(mem_side, associativity, hit_latency, stats, name))
        # TODO: limit requests per cycle

    def set_for_line(self, line):
        set_idx = (line >> self.line_bits) & (self.num_sets - 1)
        self.active_sets.add(set_idx)
#        print set_idx, "of", self.num_sets
        return self.sets[set_idx]

    def can_accept_line(self, line):
        return self.set_for_line(line).can_accept_line(line)

    def accept(self, line):
        return self.set_for_line(line).accept(line)

    def tick(self):
        for set_idx in self.active_sets:
            self.sets[set_idx].tick()
