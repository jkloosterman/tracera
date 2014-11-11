# A Request stores the information needed to emit Warps once
#  its memory comes back. Requests are coalesced with other
#  Requests and might have a limit as to how many warps
#  can be coalesced at once.
#
# A request is for a single cache line, and it stores tuples:
#   (base, size, <warp info>)

class Request(object):
    def __init__(self, cache_line, address, size, access_type):
        self.cache_line = cache_line
        self.address = address
        self.size = size
        self.access_type = access_type
        self.requesters = []
        self.has_memory = False
        
        # intra-warp: same (warp, ip, thread_offset)
        # inter-request: same (warp, ip), different thread_offset
        # inter-instruction: same warp, different ip
        # inter-warp: different warp
        self.intra_warp_coalesces = 0
        self.inter_request_coalesces = 0
        self.inter_instruction_coalesces = 0
        self.inter_warp_coalesces = 0

    # Note that this will modify warp.
    def addRequester(self, warp):
        self.requesters.append(warp)

    def bitset_or(self, bs_1, bs_2):
        assert(len(bs_1) == len(bs_2))
        
        ret = []
        for i in range(len(bs_1)):
            ret.append(bs_1[i] or bs_2[i])
        return ret

    def bitset_num_set(self, bs):
        num_set = 0
        for bit in bs:
            if bit:
                num_set += 1
        return num_set

    # Note that this doesn't merge the address and size
    #  fields. No memory system needs that currently.
    def merge(self, other):
        for other_warp in other.requesters:
            other_num_set = self.bitset_num_set(other_warp.active_threads)

            found = None
            for warp in self.requesters:
                if (warp.ip == other_warp.ip and
                    warp.scoreboard == other_warp.scoreboard and
                    warp.thread_offset == other_warp.thread_offset):
                    found = warp
                    break

            if found is not None:
                found.active_threads = self.bitset_or(found.active_threads, other_warp.active_threads)
                self.intra_warp_coalesces += other_num_set
            else:
                found_stats = False
                for warp in self.requesters:
                    if (warp.ip == other_warp.ip and
                        warp.scoreboard == other_warp.scoreboard):
                        self.inter_request_coalesces += other_num_set
                        found_stats = True
                        break
                        
                if not found_stats:
                    for warp in self.requesters:
                        if warp.scoreboard == other_warp.scoreboard:
                            self.inter_instruction_coalesces += other_num_set
                            found_stats = True
                            break

                if not found_stats:
                    self.inter_warp_coalesces += other_num_set

                self.requesters.append(other_warp)

    def finished(self):
        return len(self.requesters) == 0

    def canGenerateWarp(self):
        return len(self.requesters) > 0

    def generateWarp(self):
        return self.requesters.pop()

    def __repr__(self):
        return "<%x, req: %d>" % (self.cache_line, len(self.requesters))
