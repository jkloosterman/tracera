from ZeroLatency import *

from Dram import Dram
from MissQueue import MissQueue
from WarpReconstructor import WarpReconstructor

collect_trace = False

def CreateMemorySystem(system_type):
    if system_type == "zero_latency":
        return ZeroLatency()
    else:
        print "Unknown memory system: ", system_type
        assert(False)

class MemorySystem(object):
    def __init__(self, frontend, coalescer, caches, miss_queue_size, stats, core_idx, cache_system_ticks, config):
        self.frontend = frontend
        self.coalescer = coalescer
        self.num_banks = len(caches)
        self.stats = stats
        self.core_idx = core_idx
        self.name = "core_%d.memory_system" % core_idx

        if collect_trace:
            filename = config.output_file + ".mem_trace"
            self.fp = open(filename, "w")

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
                self.stats.increment(self.name + ".coalescer_accept_cycles", 1)
                requests = self.frontend.issue()
                if collect_trace:
                    self.dump_requests(requests)
                self.coalescer.accept(requests)
            else:
                self.stats.increment(self.name + ".coalescer_stall_cycles", 1)

        if self.coalescer.canIssue():
            self.stats.increment(self.name + ".coalescer_issue_cycles", 1)
            self.coalescer.issue(self.miss_queues)

    def dump_requests(self, requests):
        first_non_none = None
        for request in requests:
            if request is not None:
                first_not_none = request
                break
        assert(first_not_none is not None)

        warp_id = first_not_none.requesters[0].scoreboard.warp_id
        if first_not_none.access_type == "L":
            load_store = "LD"
        else:
            load_store = "ST"

        self.fp.write("%d,%s" % (warp_id, load_store))
        for request in requests:
            if request is None:
                self.fp.write(",-1")
            else:
                self.fp.write(",%x" % request.cache_line)
        self.fp.write("\n")

    def dump(self):
        self.frontend.dump()
        self.coalescer.dump()

        print "Miss queues:"
        for i in range(len(self.miss_queues)):
            print "====== %d ======" % i
            self.miss_queues[i].dump()
            print ""
