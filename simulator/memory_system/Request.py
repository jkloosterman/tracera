# A Request stores the information needed to emit Warps once
#  its memory comes back. Requests are coalesced with other
#  Requests and might have a limit as to how many warps
#  can be coalesced at once.
#
# A request is for a single cache line, and it stores tuples:
#   (base, size, <warp info>)

class Request(object):
    def __init__(self, cache_line, access_type):
        self.cache_line = cache_line
        self.access_type = access_type
        self.requesters = []
        self.has_memory = False

    # Note that this will modify warp.
    def addRequester(self, warp):
        self.requesters.append(warp)

    def bitset_or(self, bs_1, bs_2):
        assert(len(bs_1) == len(bs_2))
        
        ret = []
        for i in range(len(bs_1)):
            ret.append(bs_1[i] or bs_2[i])
        return ret

    def merge(self, other):
        for other_warp in other.requesters:
            found = None
            for warp in self.requesters:
                if (warp.ip == other_warp.ip and
                    warp.scoreboard == other_warp.scoreboard and
                    warp.thread_offset == other_warp.thread_offset):
                    found = warp
                    break
            if found is not None:
                found.active_threads = self.bitset_or(found.active_threads, other_warp.active_threads)
            else:
                self.requesters.append(other_warp)

    def finished(self):
        return self.has_memory and len(self.requesters) == 0

    def canGenerateWarp(self):
        return self.has_memory and len(self.requesters) > 0

    def generateWarp(self):
        return self.requesters.pop()

    def __repr__(self):
        return "<%x, req: %d>" % (self.cache_line, len(self.requesters))
