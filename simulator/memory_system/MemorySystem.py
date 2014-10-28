from ZeroLatency import *

from Dram import Dram
from MissQueue import MissQueue
from WarpReconstructor import WarpReconstructor

def CreateMemorySystem(system_type):
    if system_type == "zero_latency":
        return ZeroLatency()
    else:
        print "Unknown memory system: ", system_type
        assert(False)

class MemorySystem(object):
    def __init__(self, frontend, coalescer, caches, miss_queue_size, stats, core_idx, cache_system_ticks):
        self.frontend = frontend
        self.coalescer = coalescer
        self.num_banks = len(caches)
        self.stats = stats
        self.core_idx = core_idx

        self.miss_queues = []
        for i in range(len(caches)):
            mq = MissQueue(miss_queue_size, caches[i], self.stats, "core_%d.miss_queue_%d" % (self.core_idx, i))
            self.miss_queues.append(mq)

        self.warp_reconstructors = [WarpReconstructor() for x in range(self.num_banks)]
        self.issue_rr = 0

        # These are the memory system objects that need to be clocked each cycle.
        #  The ticks are sent in order, so element 0 should be the farthest back,
        #  and the last element should be the L1 cache.
        self.cache_system_ticks = cache_system_ticks

    def can_accept(self):
        return self.frontend.canAccept()

    def accept(self, warp):
        self.frontend.accept(warp)

    def can_complete(self):
        for wr in self.warp_reconstructors:
            if wr.canIssue():
                return True
        return False

    def complete(self):
        self.issue_rr += 1
        for i in range(len(self.warp_reconstructors)):
            real_i = (i + self.issue_rr) % len(self.warp_reconstructors)
            if self.warp_reconstructors[real_i].canIssue():
                return self.warp_reconstructors[real_i].issue()
        assert(False and "complete() called when nothing to issue.")

    def tick(self):
        # Work backwards to forwards
        for i in range(len(self.miss_queues)):
            if self.miss_queues[i].canIssue() and self.warp_reconstructors[i].canAccept():
                self.warp_reconstructors[i].accept(self.miss_queues[i].issue())

        for cache in self.cache_system_ticks:
            cache.tick()

        for mq in self.miss_queues:
            mq.tick()

        if self.frontend.canIssue():
            if self.coalescer.canAccept():
                self.stats.increment_core(self.core_idx, "coalescer_accept_cycles", 1)
                self.coalescer.accept(self.frontend.issue())
            else:
                self.stats.increment_core(self.core_idx, "coalescer_stall_cycles", 1)

        if self.coalescer.canIssue():
            self.stats.increment_core(self.core_idx, "coalescer_issue_cycles", 1)
            self.coalescer.issue(self.miss_queues)

    def dump(self):
        self.frontend.dump()
        self.coalescer.dump()

        print "Miss queues:"
        for i in range(len(self.miss_queues)):
            print "====== %d ======" % i
            self.miss_queues[i].dump()
            print ""
