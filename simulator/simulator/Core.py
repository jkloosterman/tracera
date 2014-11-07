from Scoreboard import *
from Pipeline import *
from WarpScheduler import *

import sys

class Core(object):
    def __init__(self, core_idx, warp_streams, memory_system_factory, config, stats):
        self.core_idx = core_idx
        self.tick_count = 0
        self.next_warp_id = 0
        self.stats = stats

        # Elements are deleted from warp_streams
        self.warp_streams = warp_streams
        self.config = config

        # Initialize scoreboards
        self.num_scoreboards = min(config.num_active_warps, len(self.warp_streams))
        warp_width = config.warp_width
        self.scoreboards = [None for x in range(self.num_scoreboards)]

        # Initialize pipelines
        self.initialize_pipelines(memory_system_factory, config)
        self.scheduler = WarpSchedulerRR(
            self.scoreboards, self.register_read_pipelines, config.issue_width,
            "core_%d" % core_idx, stats)

    def initialize_pipelines(self, memory_system_factory, config):
        self.register_read_pipelines = []
        self.register_write_pipelines = []
        self.pipelines = []

        for pipeline in config.pipelines:
#            if pipeline["type"] == "I" or pipeline["type"] == "F" or pipeline["type"] == "M":
            if pipeline["type"] == "I" or pipeline["type"] == "F":
                p = Pipeline(pipeline["stages"], pipeline["width"], pipeline["type"])
                self.pipelines.append(p)
            elif pipeline["type"] == "M":
                p = memory_system_factory.createMemorySystem(self.core_idx)
                self.pipelines.append(p)
            else:
                assert(False and "Unknown pipeline type: " + pipeline.type)

            rr_p = Pipeline(1, pipeline["width"], pipeline["type"])
            self.register_read_pipelines.append(rr_p)
            rw_p = Pipeline(1, pipeline["width"], pipeline["type"])
            self.register_write_pipelines.append(rw_p)


    def finished(self):
        for i in range(self.num_scoreboards):
            if self.scoreboards[i] is not None and not self.scoreboards[i].finished():
                return False
        return len(self.warp_streams) == 0
    
    def update_scoreboards(self):
        for i in range(self.num_scoreboards):
            if self.scoreboards[i] is None or self.scoreboards[i].finished():
                if len(self.warp_streams) > 0:
                    self.scoreboards[i] = Scoreboard(self.next_warp_id, self.config.warp_width, self.warp_streams.pop(0), self.stats)
                    self.next_warp_id += 1

        for i in range(self.num_scoreboards):
            if self.scoreboards[i] is not None:
                self.scoreboards[i].update()

    def status(self):
        self.stats.dump()
        return "Core %d: %d warps remaining." % (self.core_idx, len(self.warp_streams))
    

    def dump(self):
        print "************** BEGIN CYCLE %d, core %d *******************" % (self.tick_count, self.core_idx)
        
        print "Scoreboards:"
        print "============"
        for scoreboard in self.scoreboards:
            if scoreboard is None:
                print "[Null scoreboard]"
            else:
                scoreboard.dump()
            print ""

        print ""
        print "Reg. Read Pipelines:"
        print "===================="
        for pipe in self.register_read_pipelines:
            pipe.dump()
            print ""

        print ""
        print "Pipelines:"
        print "=========="
        for pipe in self.pipelines:
            pipe.dump()
            print ""

        print ""
        print "Reg. Write Pipelines:"
        print "===================="
        for pipe in self.register_write_pipelines:
            pipe.dump()
            print ""

        print "************** END CYCLE *******************"
        
    def tick(self):
        # Work backwards through the pipe.

        # Complete warps
        for pipe in self.register_write_pipelines:
            if pipe.can_complete():
                warp = pipe.complete()
                warp.complete()

        # Register write pipelines
        for i in range(len(self.register_write_pipelines)):
            if self.pipelines[i].can_complete() and self.register_write_pipelines[i].can_accept():
                self.register_write_pipelines[i].accept(self.pipelines[i].complete())
        
        # Advance pipelines
        for pipe in self.pipelines:
            pipe.tick()

        # Move warps from register read to pipelines
        for i in range(len(self.register_read_pipelines)):
            if self.register_read_pipelines[i].can_complete() and self.pipelines[i].can_accept():
                self.pipelines[i].accept(self.register_read_pipelines[i].complete())

        # Issue warps
        self.scheduler.schedule()

        # Create new scoreboards
        self.update_scoreboards()

        # Show what we're up to
#        if self.tick_count > 100000:
#            self.dump()
#            exit(1)

        # self.dump()
        self.tick_count += 1
