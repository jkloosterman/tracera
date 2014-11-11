import copy
import itertools
from Request import *

class Frontend(object):
    def __init__(self, queue_depth, warp_width, line_size, stats):
        self.queue_depth = queue_depth
        self.warp_width = warp_width
        self.line_size = line_size
        self.queue = []
        self.stats = stats

    def canAccept(self):
        return len(self.queue) < self.queue_depth

    def canIssue(self):
        return len(self.queue) > 0

    def cacheLine(self, address):
        return address & ~(self.line_size - 1)

    def splitCacheLines(self, access):
        address, size, ac_type = access
        lines = []
        remaining_size = size
        
        line = self.cacheLine(address)
        next_line = line + self.line_size
        cur_size = min(next_line - address, remaining_size)
        lines.append((line, address, cur_size, ac_type))
        remaining_size -= cur_size

        while address + size >= next_line:
            line = next_line
            next_line += self.line_size
            cur_size = min(self.line_size, remaining_size)
            lines.append((line, line, cur_size, ac_type))
            remaining_size -= cur_size

        return lines

    # This takes in the Warp creating the access,
    #  and the array of accesses, which are tuples
    #  (base, size, read/write)
    def accept(self, warp):
        distinct_lines = set()
        requests = []

#        assert(len(warp.instruction) == self.warp_width)
        for i in range(len(warp.instruction)):
            # split request into cache lines
            lines = []
            if warp.active_threads[i]:
                lines = self.splitCacheLines(warp.instruction[i])
                if len(lines) > 1 and lines[0][1] == "L":
                    # Notify the scoreboard that it needs to wait for
                    #  extra requests to come back.
                    # Note we do this just for loads, not for stores,
                    #  because stores are independent anyways.
                    warp.add_extra_completes(i, len(lines) - 1)
                for line in lines:
                    distinct_lines.add(line)

            # Create Requests
            thread_requests = []
            for line in lines:
                r = Request(line[0], line[1], line[2], line[3])

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

        # Add number of lines to histogram
        self.stats.increment("lines_per_warp_%d" % len(distinct_lines), 1)

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

# def test():
#     fe = Frontend(2, 16, 128)

#     access = (0x10, 128, "R")
#     print fe.splitCacheLines(access)

# test()
