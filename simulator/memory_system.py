#!/usr/bin/python
#
# Independent driver for memory system.
#
# @author John Kloosterman
# @date Oct. 21, 2014

from warp_assembly.warp_stream import WarpStream
from warp_assembly.assembly_objects import ParallelLoop

from memory_system.MemorySystem import MemorySystem
from memory_system.Frontend import Frontend
from memory_system.BankingPolicy import *
from memory_system.Dram import Dram
from memory_system.coalescers.DefaultCoalescer import *

import sys
import sqlite3

class FakeWarp(object):
    def __init__(self):
        self.instruction = []
        self.active_threads = []
        self.ip = -1
        self.scoreboard = None
        self.thread_offset = 0

class FakeCache(object):
    def __init__(self, bank):
        self.bank = bank
    def canAccept(self):
        return True
    def accept(self, request):
        print "Bank %d:" % self.bank, request

def build_warp(instruction, ip):
    warp = FakeWarp()
    warp.instruction = instruction
    warp.active_threads = [x is not None for x in instruction]
    warp.ip = ip
    return warp

def simulate(frontend, mem_instructions):
    ip = 0

    dram = Dram(4, 5)
    banking_policy = BankingPolicyConsecutive(4, 64)
    coalescer = DefaultCoalescer(banking_policy)
    caches = [dram for i in range(4)]
    memory_system = MemorySystem(frontend, coalescer, caches)

    while ip < len(mem_instructions):
        print "============================ CYCLE =========="

        if memory_system.canAccept():
            warp = build_warp(mem_instructions[ip], ip)
            print "Instruction:", mem_instructions[ip]
            memory_system.accept(warp)
            ip += 1
            
        while memory_system.canIssue():
            print "** Finished:", memory_system.issue(), "**"

        memory_system.tick()
        memory_system.dump()
        print "============================ END =========="

def main():
    if len(sys.argv) != 5:
        print "memory_system.py <sqlite db> <loop id> <warp id> <warp size>"
        exit(1)

    sqlite_file = sys.argv[1]
    loop_id = int(sys.argv[2])
    warp_id = int(sys.argv[3])
    warp_size = int(sys.argv[4])

    print "Loop Id: %d, warp size: %d" % (loop_id, warp_size)

    db = sqlite3.connect(sqlite_file)
    loop = ParallelLoop(db, loop_id)
    warp_stream = WarpStream(loop, warp_id, warp_size)

    frontend = Frontend(4, warp_size, 64)

    mem_instructions = []
    for ins in warp_stream.instructions():
        is_mem = True
        for i in ins:
            if i == "F" or i == "I":
                is_mem = False
                break
        if is_mem:
            mem_instructions.append(ins)

    simulate(frontend, mem_instructions)

    db.close()

main()
