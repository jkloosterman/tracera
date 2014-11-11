from CacheSet import CacheSet
import math

class Cache(object):
    def __init__(self, mem_side, size_in_bytes, num_banks, line_size, associativity, hit_latency, ports, max_outstanding_requests, stats, name):
        self.num_lines = size_in_bytes / line_size
        self.num_sets = self.num_lines / associativity
        self.num_banks = num_banks
        self.bank_bits = int(math.log(self.num_banks, 2))
        self.line_size = line_size
        self.line_bits = int(math.log(self.line_size, 2))
        self.stats = stats
        self.name = name
        self.active_sets = set()
        self.ports = ports
        self.requests_this_cycle = 0
        self.max_outstanding_requests = max_outstanding_requests
        self.outstanding_requests = 0

        assert(self.num_sets > 0)
        self.sets = []
        for i in range(self.num_sets):
            self.sets.append(CacheSet(self, mem_side, associativity, hit_latency, stats, name))

    def has_outstanding_request(self):
        return self.outstanding_requests < self.max_outstanding_requests

    def outstanding_request_add(self):
        self.outstanding_requests += 1

    def outstanding_request_finished(self):
        self.outstanding_requests -= 1

    def set_for_line(self, line):
        set_idx = (line >> (self.line_bits + self.bank_bits)) & (self.num_sets - 1)
        self.active_sets.add(set_idx)
        return self.sets[set_idx]

    def can_accept_line(self, line):
        if self.requests_this_cycle >= self.ports:
            self.stats.increment(self.name + ".cant_accept_ports", 1)
            return False

        if not self.set_for_line(line).can_accept_line(line):
            if not self.has_outstanding_request():
                self.stats.increment(self.name + ".cant_accept_outstanding_requests", 1)
            else:
                self.stats.increment(self.name + ".cant_accept_line", 1)
            return False

        return True

    def accept(self, line):
        self.requests_this_cycle += 1
        return self.set_for_line(line).accept(line)

    def tick(self):
        self.requests_this_cycle = 0
        for set_idx in self.active_sets:
            self.sets[set_idx].tick()
