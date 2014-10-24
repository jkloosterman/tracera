# Pipeline that just introduces delay
#
# Sequencing:
#  1) complete last stage
#  2) advance
#  3) if can_accept, insert something new

class Pipeline(object):
    def __init__(self, num_stages, width, op_type):
        self.num_stages = num_stages
        self.stages = [None for x in range(num_stages)]
        self.width = width
        self.op_type = op_type

    def get_width(self):
        return self.width

    def get_type(self):
        return self.op_type

    def can_accept(self):
        return self.stages[0] is None

    def accept(self, warp):
        assert(self.can_accept())
        self.stages[0] = warp

    def can_complete(self):
        return self.stages[-1] is not None

    def complete(self):
        assert(self.can_complete())

        completed_warp = self.stages[-1]
        self.stages[-1] = None
        return completed_warp
    
    def tick(self):
        # If nobody took our last stage, we stall
        if self.stages[-1] is not None:
            return

        for i in range(self.num_stages - 1):
            self.stages[-1 - i] = self.stages[-2 - i]
        self.stages[0] = None

    def dump(self):
        print "Pipeline (type: %s, width: %d, stages %d)" % (self.op_type, self.width, self.num_stages)
        for stage in self.stages:
            if stage is None:
                print "[empty]"
            else:
                stage.dump()
