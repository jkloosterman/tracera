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
    def __init__(self, frontend, coalescer, caches, miss_queue_size):
        self.frontend = frontend
        self.coalescer = coalescer
        self.num_banks = len(caches)
        self.miss_queues = [MissQueue(miss_queue_size, cache) for cache in caches]
        self.warp_reconstructors = [WarpReconstructor() for x in range(self.num_banks)]
        self.issue_rr = 0

        # We store these as a set so that tick() can call each unique cache once.
        self.cache_set = set(caches)

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

        # Cache is a set, so each unique object gets ticked once.
        # XXX: this is probably not the way it should stay.
        for cache in self.cache_set:
            cache.tick()

        for mq in self.miss_queues:
            mq.tick()

        if self.frontend.canIssue():
            if self.coalescer.canAccept():
                self.coalescer.accept(self.frontend.issue())

        if self.coalescer.canIssue():
            self.coalescer.issue(self.miss_queues)

    def dump(self):
        self.frontend.dump()

        print "Miss queues:"
        for i in range(len(self.miss_queues)):
            print "====== %d ======" % i
            self.miss_queues[i].dump()
            print ""
