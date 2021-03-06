from MemorySystem import MemorySystem
from Dram import Dram
from Frontend import Frontend
from BankingPolicy import *
from MemorySystem import MemorySystem
from Cache import Cache
from coalescers.IntrawarpCoalescer import IntrawarpCoalescer
from coalescers.FullAssociativeCoalescer import FullAssociativeCoalescer
from coalescers.UncoverCoalescer import UncoverCoalescer
from coalescers.UncoverSyncedCoalescer import UncoverSyncedCoalescer
from coalescers.HybridCoalescer import HybridCoalescer
from coalescers.SortCoalescer import SortCoalescer
from coalescers.GreedyCoalescer import GreedyCoalescer
from coalescers.NVidiaCoalescer import NVidiaCoalescer

class MemorySystemFactory(object):
    def __init__(self, config, stats):
        self.dram = Dram(config.dram_ports, config.dram_latency)
        self.config = config
        self.stats = stats

    def createMemorySystem(self, core_idx):
        frontend = Frontend(self.config.mem_frontend_depth, self.config.warp_width, self.config.line_size, self.stats)

        if self.config.cache_system == 'dram_only':
            associativity = 1
        else:
            associativity = self.config.l1_associativity
 
        if self.config.banking_policy == 'consecutive':
            banking_policy = BankingPolicyConsecutive(self.config.num_banks, self.config.line_size)
        elif self.config.banking_policy == 'prime':
            banking_policy = BankingPolicyPrime(self.config.num_banks, self.config.line_size)
        elif self.config.banking_policy == 'skew':
            banking_policy = BankingPolicySkew(self.config.num_banks, self.config.line_size)
        else:
            assert(false)

        core_name = "core_%d" % core_idx
        if self.config.coalescer == 'intra_warp':
            coalescer = IntrawarpCoalescer(banking_policy, core_name, self.stats)
        elif self.config.coalescer == 'full_associative':
            coalescer = FullAssociativeCoalescer(banking_policy, self.config.coalescer_depth, core_name, self.stats)
        elif self.config.coalescer == 'uncover':
            coalescer = UncoverCoalescer(banking_policy, self.config.coalescer_depth, core_name, self.stats)
        elif self.config.coalescer == 'uncover_synced':
            sync_distance = 8
            coalescer = UncoverSyncedCoalescer(banking_policy, self.config.coalescer_depth, sync_distance, core_name, self.stats)
        elif self.config.coalescer == 'hybrid':
            coalescer = HybridCoalescer(banking_policy, self.config.coalescer_depth, core_name, self.stats)
        elif self.config.coalescer == 'sort':
            coalescer = SortCoalescer(banking_policy, self.config.coalescer_depth, self.config.num_banks, core_name, self.stats)
        elif self.config.coalescer == 'greedy':
            coalescer = GreedyCoalescer(banking_policy, self.config.coalescer_depth, core_name, self.stats)
        elif self.config.coalescer == 'nvidia':
            coalescer = NVidiaCoalescer(self.config.line_size, self.config.line_size / 4, self.stats)
        else:
            print "MemorySystemFactory:"
            print "Unknown coalescer type '%s'." % self.config.coalescer
            print "Choices: 'intra_warp', 'full_associative', 'uncover', 'nvidia'"
            exit(1)

        # Allow any number of requests to L1 per cycle. The coalescer generates the
        #  limit.
        l1_ports = 10000
        l1_outstanding_requests = 10000

        if self.config.cache_system == 'dram_only':
            banks = [self.dram for i in range(self.config.num_banks)]
            cache_system_ticks = [self.dram]
        elif self.config.cache_system == 'l1':
            l1_bank_size = self.config.l1_size / self.config.num_banks
            banks = []
            for i in range(self.config.num_banks):
                cache = Cache(
                    self.dram, l1_bank_size, self.config.line_size,
                    self.config.l1_associativity, self.config.l1_latency, l1_ports, l1_outstanding_requests,
                    banking_policy, self.stats, "core_%d.l1_bank_%d" % (core_idx, i))
                banks.append(cache)
            cache_system_ticks = [self.dram] + banks
        elif self.config.cache_system == 'l2':
            # L2 has no banking
            l2_banking_policy = BankingPolicyConsecutive(1, self.config.line_size)
            l2 = Cache(
                self.dram, self.config.l2_size, self.config.line_size,
                self.config.l2_associativity, self.config.l2_latency, self.config.l2_ports,
                self.config.l2_outstanding_requests, l2_banking_policy, 
                self.stats, "core_%d.l2" % core_idx)

            # Distribute L1 size across banks
            l1_bank_size = self.config.l1_size / self.config.num_banks
            banks = []
            for i in range(self.config.num_banks):
                cache = Cache(
                    l2, l1_bank_size, self.config.line_size,
                    self.config.l1_associativity, self.config.l1_latency, l1_ports, l1_outstanding_requests,
                    banking_policy, self.stats, "core_%d.l1_bank_%d" % (core_idx, i))
                banks.append(cache)
            cache_system_ticks = [self.dram, l2] + banks
        else:
            print "MemorySystemFactory:"
            print "Unknown cache_system '%s'." % self.config.cache_system
            print "Choices: 'dram_only', 'l1', 'l2'"
            exit(1)

#        bank_miss_queue_size = self.config.miss_queue_size / self.config.num_banks
        bank_miss_queue_size = self.config.miss_queue_size
        return MemorySystem(frontend, coalescer, banks, bank_miss_queue_size, self.stats, core_idx, cache_system_ticks, self.config)
