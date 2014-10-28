from Core import *

class Simulator(object):
    def __init__(self, warp_assembly, memory_system_factory, config, stats):
        self.stats = stats
        self.num_warps = warp_assembly.get_num_warps()
        print "Number of warps:", self.num_warps
        self.warps_per_core = (self.num_warps + config.num_cores - 1) / config.num_cores

        # Note that this splits low-iteration loops into their own warp instead
        #  of doing them on their own.
        self.core_streams = self.chunks(list(warp_assembly.streams()), self.warps_per_core)

        self.cores = []
        for i in range(config.num_cores):
            core = Core(i, self.core_streams[i], memory_system_factory, config, stats)
            self.cores.append(core)

        self.num_cycles = 0
        self.stats.initialize("num_cycles")

    # from http://stackoverflow.com/questions/312443/how-do-you-split-a-list-into-evenly-sized-chunks-in-python
    def chunks(self, l, n):
        if n < 1:
            n = 1
        return [l[i:i + n] for i in xrange(0, len(l), n)]

    def finished(self):
        for core in self.cores:
            if not core.finished():
                return False
        return True

    def simulate(self):
        while not self.finished():
            for core in self.cores:
                if not core.finished():
                    core.tick()
            self.num_cycles += 1

            if self.num_cycles % 10000 == 0:
                print self.num_cycles
                for core in self.cores:
                    print core.status()

            self.stats.set("num_cycles", self.num_cycles)
            self.stats.set_ipc()


#            if self.num_cycles > 10:
#                break
        
        print "Cycles: ", self.num_cycles
        self.stats.set("num_cycles", self.num_cycles)
        self.stats.set_ipc()
        self.stats.dump()
        return self.num_cycles
