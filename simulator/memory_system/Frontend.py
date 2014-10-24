import copy
import itertools
from Request import *

class Frontend(object):
    def __init__(self, queue_depth, warp_width, line_size):
        self.queue_depth = queue_depth
        self.warp_width = warp_width
        self.line_size = line_size
        self.queue = []

    def canAccept(self):
        return len(self.queue) < self.queue_depth

    def canIssue(self):
        return len(self.queue) > 0

    def cacheLine(self, address):
        return address & ~(self.line_size - 1)

    def splitCacheLines(self, access):
        address, size, ac_type = access
        lines = []

        line = self.cacheLine(address)
        next_line = line + self.line_size
        lines.append((line, ac_type))

        while address + size >= next_line:
            line = next_line
            next_line += self.line_size
            lines.append((line, ac_type))
        
        return lines

    # This takes in the Warp creating the access,
    #  and the array of accesses, which are tuples
    #  (base, size, read/write)
    def accept(self, warp):
        requests = []

#        assert(len(warp.instruction) == self.warp_width)
        for i in range(len(warp.instruction)):
            # split request into cache lines
            lines = []
            if warp.active_threads[i]:
                lines = self.splitCacheLines(warp.instruction[i])

            # Create Requests
            thread_requests = []
            for line in lines:
                r = Request(line[0], line[1])

                # We need a separate copy for each so that the Requests
                #  can change the active threads without causing side-effects
                w = copy.copy(warp)
                w.active_threads = [False for x in warp.instruction]
                w.active_threads[i] = True
                r.addRequester(w)
                thread_requests.append(r)

            requests.append(thread_requests)
                
 #       assert(len(requests) == self.warp_width)
        request = list(itertools.izip_longest(*requests))
        self.queue += request

    def issue(self):
        return self.queue.pop(0)

    def dump(self):
        print "Memory system frontend:"
        print "======================="
        print "Queue depth: %d" % self.queue_depth
        
        for q in self.queue:
            print "[",
            for request in q:
                print request,
            print "]"
