from warp_stream import *
from assembly_objects import *

class WarpAssembly(object):
    def __init__(self, db, loop_id, warp_size):
        self.warp_size = warp_size
        self.loop = ParallelLoop(db, loop_id)

        num_iterations = self.loop.numIterations()
        self.num_warps = (num_iterations + warp_size - 1) / warp_size

    def get_num_warps(self):
        return self.num_warps

    def streams(self):
        for i in range(self.num_warps):
            yield WarpStream(self.loop, self.warp_size * i, self.warp_size)
