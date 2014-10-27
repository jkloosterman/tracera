from MemorySystem import MemorySystem
from Dram import Dram
from Frontend import Frontend
from BankingPolicy import BankingPolicyConsecutive
from MemorySystem import MemorySystem
from coalescers.IntrawarpCoalescer import IntrawarpCoalescer
from coalescers.FullAssociativeOldestCoalescer import FullAssociativeOldestCoalescer

class MemorySystemFactory(object):
    def __init__(self, config, stats):
        self.dram = Dram(config.num_banks, config.dram_latency)
        self.banking_policy = BankingPolicyConsecutive(config.num_banks, config.line_size)
        self.config = config
        self.stats = stats

    def createMemorySystem(self, core_idx):
        frontend = Frontend(self.config.mem_frontend_depth, self.config.warp_width, self.config.line_size)

        if self.config.coalescer == 'intra_warp':
            coalescer = IntrawarpCoalescer(self.banking_policy)
        elif self.config.coalescer == 'full_associative_oldest':
            coalescer = FullAssociativeOldestCoalescer(self.banking_policy, 8)
        else:
            print "MemorySystemFactory:"
            print "Unknown coalescer type '%s'."
            print "Choices: 'intra_warp', 'full_associative_oldest'"
            exit(1)


        caches = [self.dram for i in range(self.config.num_banks)]

        return MemorySystem(frontend, coalescer, caches, self.config.miss_queue_size, self.stats, core_idx)
