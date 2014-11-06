from MemorySystem import MemorySystem
from Dram import Dram
from Frontend import Frontend
from BankingPolicy import *
from MemorySystem import MemorySystem
from Cache import Cache
from coalescers.IntrawarpCoalescer import IntrawarpCoalescer
from coalescers.FullAssociativeCoalescer import FullAssociativeCoalescer
from coalescers.UncoverCoalescer import UncoverCoalescer
from coalescers.GreedyCoalescer import GreedyCoalescer

class MemorySystemFactory(object):
    def __init__(self, config, stats):
        self.dram = Dram(config.dram_ports, config.dram_latency)
        self.config = config
        self.stats = stats

    def createMemorySystem(self, core_idx):
        frontend = Frontend(self.config.mem_frontend_depth, self.config.warp_width, self.config.line_size)

        if self.config.cache_system == 'dram_only':
            associativity = 1
        else:
            associativity = self.config.l1_associativity
 
        if self.config.banking_policy == 'consecutive':
            banking_policy = BankingPolicyConsecutive(self.config.num_banks, self.config.line_size)
            cache_num_banks = self.config.num_banks
        elif self.config.banking_policy == 'chinese_remainder':
            banking_policy = BankingPolicyChineseRemainder(self.config.num_banks, self.config.line_size)
            cache_num_banks = 1
        else:
            assert(false)

        core_name = "core_%d" % core_idx
        if self.config.coalescer == 'intra_warp':
            coalescer = IntrawarpCoalescer(banking_policy, core_name, self.stats)
        elif self.config.coalescer == 'full_associative':
            coalescer = FullAssociativeCoalescer(banking_policy, self.config.coalescer_depth, core_name, self.stats)
        elif self.config.coalescer == 'uncover':
            coalescer = UncoverCoalescer(banking_policy, self.config.coalescer_depth, core_name, self.stats)
        elif self.config.coalescer == 'greedy':
            coalescer = GreedyCoalescer(banking_policy, self.config.coalescer_depth, core_name, self.stats)
        else:
            print "MemorySystemFactory:"
            print "Unknown coalescer type '%s'." % self.config.coalescer
            print "Choices: 'intra_warp', 'full_associative', 'uncover'"
            exit(1)

        if self.config.cache_system == 'dram_only':
            banks = [self.dram for i in range(self.config.num_banks)]
            cache_system_ticks = [self.dram]
        elif self.config.cache_system == 'l1':
            l1_bank_size = self.config.l1_size / self.config.num_banks
            banks = []
            for i in range(self.config.num_banks):
                cache = Cache(
                    self.dram, l1_bank_size, cache_num_banks, self.config.line_size,
                    self.config.l1_associativity, self.config.l1_latency,
                    self.stats, "core_%d.l1_bank_%d" % (core_idx, i))
                banks.append(cache)
            cache_system_ticks = [self.dram] + banks
        elif self.config.cache_system == 'l2':
            l2 = Cache(
                self.dram, self.config.l2_size, 1, self.config.line_size,
                self.config.l2_associativity, self.config.l2_latency,
                self.stats, "core_%d.l2" % core_idx)

            l1_bank_size = self.config.l1_size / self.config.num_banks
            banks = []
            for i in range(self.config.num_banks):
                cache = Cache(
                    l2, l1_bank_size, cache_num_banks, self.config.line_size,
                    self.config.l1_associativity, self.config.l1_latency,
                    self.stats, "core_%d.l1_bank_%d" % (core_idx, i))
                banks.append(cache)
            cache_system_ticks = [self.dram, l2] + banks
        else:
            print "MemorySystemFactory:"
            print "Unknown cache_system '%s'." % self.config.cache_system
            print "Choices: 'dram_only', 'l1', 'l2'"
            exit(1)

        return MemorySystem(frontend, coalescer, banks, self.config.miss_queue_size, self.stats, core_idx, cache_system_ticks)
