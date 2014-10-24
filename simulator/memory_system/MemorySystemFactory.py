from MemorySystem import MemorySystem
from Dram import Dram
from Frontend import Frontend
from BankingPolicy import BankingPolicyConsecutive
from MemorySystem import MemorySystem
from coalescers.DefaultCoalescer import DefaultCoalescer

class MemorySystemFactory(object):
    def __init__(self, config):
        self.dram = Dram(config.num_banks, config.dram_latency)
        self.banking_policy = BankingPolicyConsecutive(config.num_banks, config.line_size)
        self.config = config

    def createMemorySystem(self):
        frontend = Frontend(self.config.mem_frontend_depth, self.config.warp_width, self.config.line_size)
        coalescer = DefaultCoalescer(self.banking_policy)
        caches = [self.dram for i in range(self.config.num_banks)]

        return MemorySystem(frontend, coalescer, caches, self.config.miss_queue_size)
