#!/usr/bin/python
# Object-oriented version of the other mess.

import sqlite3
import sys
import itertools
from lcs import *
from memory_trace import *

class Loop(object):
    def __init__(self, db, loop_id):
        self.db = db
        self.loop_id = loop_id

    def buildTrace(self, iteration, trace_id, mem_trace_id):
        c = self.db.cursor()
        c.execute(
            "SELECT type, CASE "
            + "WHEN traces.type = 0 THEN basicBlockId "
            + "ELSE childLoopId"
            +" END "
            + "FROM traces "
            + "WHERE traces.traceId = ? "
            + "ORDER BY traces.sequence ASC",
            (trace_id,))

        ret = []
        bb_sequence = 0
        for row in c:
            if row[0] == 0:
                ret.append(BasicBlock(self.db, row[1], iteration, trace_id, mem_trace_id, bb_sequence))
            else:
                ret.append(SequentialLoop(self.db, row[1]))
            bb_sequence += 1
        return ret

    def numIterations(self):
        c = self.db.cursor()
        c.execute("SELECT COUNT(*) FROM loops WHERE loopId=?", (self.loop_id,))
        return c.fetchone()[0]

class ParallelLoop(Loop):
    def __init__(self, db, loop_id):
        super(ParallelLoop, self).__init__(db, loop_id)

    def getWarp(self, thread_offset, warp_size):
        c = self.db.cursor()
        
        c.execute(
            "SELECT traceId, memoryTraceId FROM loops "
            + "WHERE loopId=? AND iteration >= ? AND iteration < ?"
            + "ORDER BY iteration ASC",
            (self.loop_id, thread_offset, thread_offset + warp_size))

        # XXX: get this correct before trying to cache it to speed it up.
#        print "PLoop: thread_offset: %d, warp_size: %d" % (thread_offset, warp_size)
#        print "PLoop: loop_id: %d, first iteration %d, end iteration %d" % (self.loop_id, thread_offset, thread_offset + warp_size)
        trace_ids = [(x[0], x[1]) for x in c]
#        unique_trace_ids = list(set(trace_ids))
#
#        trace_map = {}
#        for trace_id in unique_trace_ids:
#            trace_map[trace_id] = self.buildTrace(trace_id[0], trace_id[1])
#        traces = [trace_map[x] for x in trace_ids]

        traces = []
        for i, trace_id in enumerate(trace_ids):
            traces.append(self.buildTrace(thread_offset + i, trace_id[0], trace_id[1]))

#        print "Trace IDs: ", trace_ids
#        print "Traces: ", traces
        warp = merge_traces(traces)
#        print "Warp: ", warp

        # Replace -1s with stalls
        for w in warp:
            for i in range(len(w)):
                if w[i] == -1:
                    w[i] = Stall()

        return Warp(self.db, warp, thread_offset)
        
class SequentialLoop(Loop):
    def __init__(self, db, loop_id):
        super(SequentialLoop, self).__init__(db, loop_id)
        self.traces = None

    def getTraceIds(self):
        if self.traces is not None:
            return self.traces

        c = self.db.cursor()
        c.execute("SELECT traceId FROM loops WHERE loopId=? ORDER BY iteration ASC", (self.loop_id,))
        self.traces = [x[0] for x in c]
        return self.traces

    def getMemTraceIds(self):
        c = self.db.cursor()
        c.execute("SELECT traceId, memoryTraceId FROM loops WHERE loopId=? ORDER BY iteration ASC", (self.loop_id,))
        return [(x[0], x[1]) for x in c]

    def getInstructions(self, outer_iteration_id):
        # We don't care about our outer iteration ID at all.

        trace_ids = self.getMemTraceIds()

        traces = []
        for i, trace_id in enumerate(trace_ids):
            traces.append(self.buildTrace(i, trace_id[0], trace_id[1]))

        instructions = []
        # Each entry in traces is an iteration.
        for i in range(len(traces)):
            for bb in traces[i]:
                instructions += bb.getInstructions(i)

        return instructions

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.getTraceIds() == other.getTraceIds()
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return "SeqLoop %d" % self.loop_id

# Global component cache
bbComponentCache = {}

class BasicBlock:
    def __init__(self, db, bb_id, iteration, trace_id, mem_trace_id, bb_sequence):
        self.db = db
        self.bb_id = bb_id
        self.iteration = iteration
        self.trace_id = trace_id
        self.mem_trace_id = mem_trace_id
        self.bb_sequence = bb_sequence

    def getComponentIds(self):
        c = self.db.cursor()
        c.execute(
            "SELECT componentId FROM basicBlocks "
            + "WHERE basicBlockId=? ORDER BY sequence ASC ",
            (self.bb_id,))
        return [x[0] for x in c]

    def insertAddresses(self, instructions, iteration):
        mem_sequence = 0

#        print "insertAddresses: ", instructions, iteration, self.bb_id, self.bb_sequence

        for i in range(len(instructions)):
            if instructions[i] == "L" or instructions[i] == "S":
#                print "bb:", self.bb_id, "iteration:", self.iteration, "trace_id:", self.trace_id, "mem_trace_id:", self.mem_trace_id
                mtn = MemoryTraceNode(self.db, self.mem_trace_id, self.bb_sequence, mem_sequence)
                mem_sequence += 1
                address, size = mtn.getAddress(iteration)
                instructions[i] = (address, size, instructions[i])

    def getInstructions(self, iteration):
        global bbComponentCache

        if self.bb_id not in bbComponentCache:
            c = self.db.cursor()
            componentIds = self.getComponentIds()
        
            ins = []
            for component in componentIds:
                c.execute("SELECT CASE "
                          + "WHEN type = 1 THEN 'L' "
                          + "WHEN type = 2 THEN 'S' "
                          + "ELSE chunk END "
                          + "FROM basicBlockComponents "
                          + "LEFT JOIN chunks USING (chunkId) "
                          + "WHERE componentId=?",
                          (component,))
                ins += list(c.fetchone()[0])
            bbComponentCache[self.bb_id] = ins
        else:
            ins = bbComponentCache[self.bb_id]

        ins_copy = ins[:]
        self.insertAddresses(ins_copy, iteration)
        return ins_copy
        
    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.bb_id == other.bb_id
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return "BB %d" % self.bb_id

class Stall:
    def getInstructions(self, iteration):
        return []

    def __repr__(self):
        return "stall"

class Warp:
    def __init__(self, db, trace_warp, thread_offset):
        self.db = db
        self.trace_warp = trace_warp
        self.trace_idx = 0
        self.thread_offset = thread_offset

    def iter_bbs(self):
#        print "Offset:", self.thread_offset

        for bb in self.trace_warp:
#            print "BB", bb

            instructions = []
            for i in range(len(bb)):
                instructions.append(bb[i].getInstructions(self.thread_offset + i))

            for ins in itertools.izip_longest(*instructions):
                yield ins
