#!/usr/bin/python

from assembly_objects import *
import itertools
import sqlite3
import sys

# A WarpStream wraps around a loop and can be polled for
#  one instruction at a time.

class WarpStream(object):
    def __init__(self, loop, warp_offset, warp_size):
        self.loop = loop
        self.warp_offset = warp_offset
        self.warp_size = warp_size
        self.warp = self.loop.getWarp(warp_offset, warp_size)

    def instructions(self):
        for bb in self.warp.iter_bbs():
            yield bb        

def warp_stream_main():
    if len(sys.argv) != 5:
        print "warp_stream.py <sqlite db> <loop id> <warp id> <warp size>"
        exit(1)

    sqlite_file = sys.argv[1]
    loop_id = int(sys.argv[2])
    warp_id = int(sys.argv[3])
    warp_size = int(sys.argv[4])

    print "Loop Id: %d, warp size: %d" % (loop_id, warp_size)

    db = sqlite3.connect(sqlite_file)
    loop = ParallelLoop(db, loop_id)
    warp_stream = WarpStream(loop, warp_id, warp_size)

    for ins in warp_stream.instructions():
        print ins

    db.close()

if __name__ == "__main__":
    warp_stream_main()
