#!/usr/bin/python

from assembly_objects import *
import itertools
import sqlite3
import sys
import json

# A WarpStream wraps around a loop and can be polled for
#  one instruction at a time.

class WarpStream(object):
    # warp_offset is in threads
    def __init__(self, loop, thread_offset, warp_size):
        self.loop = loop
        self.thread_offset = thread_offset
        self.warp_size = warp_size

    def instructions(self):
        self.warp = self.loop.getWarp(self.thread_offset, self.warp_size)
        for bb in self.warp.iter_bbs():
            yield bb

def warp_stream_main():
    if len(sys.argv) != 4:
        print "json_trace.py <sqlite db> <loop id> <num accesses>"
        exit(1)

    sqlite_file = sys.argv[1]
    loop_id = int(sys.argv[2])
    num_accesses = int(sys.argv[3])

    db = sqlite3.connect(sqlite_file)
    loop = ParallelLoop(db, loop_id)

    json_obj = []
    num_threads = 100 # loop.numIterations()
    for i in range(num_threads):
        if i % 1000 == 0:
            print "Thread %d of %d" % (i, num_threads)
        json_obj.append([])
        cur_accesses = 0
        warp_stream = WarpStream(loop, i, 1)
        for ins in warp_stream.instructions():
            if ins[0] != "I" and ins[0] != "F":
                json_obj[-1].append(ins[0])

    db.close()

    with open('out.json', 'w') as outfile:
        json.dump(json_obj, outfile)

if __name__ == "__main__":
    warp_stream_main()
