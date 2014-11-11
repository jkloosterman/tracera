from Coalescer import Coalescer

# Dispatch the oldest request to each warp.
class FullAssociativeCoalescer(Coalescer):
    def __init__(self, banking_policy, depth, name, stats):
        super(FullAssociativeCoalescer, self).__init__(banking_policy, name, stats)
        self.depth = depth
        self.request_deque = []

    def canAccept(self):
        return len(self.request_deque) < self.depth

    def accept(self, requests):
        self.request_deque.append(list(requests))

    def canIssue(self):
        return len(self.request_deque) > 0

    def coalesce_all(self, request, req_lane, req_idx):
        max_width = 0
        for warp in self.request_deque:
            if len(warp) > max_width:
                max_width = len(warp)

        num_coalesces = 0
        for lane in range(max_width):
            foundWarps = []
            for idx, warp in enumerate(self.request_deque):
                if lane < len(warp) and warp[lane] is not None and warp[lane].cache_line == request.cache_line:
                    if warp[lane].access_type == request.access_type:
                        if not (warp[lane].requesters[0].scoreboard.warp_id in foundWarps):
                            request.merge(warp[lane])
                            warp[lane] = None
                            num_coalesces += 1
                    else:
                        foundWarps.append(warp[lane].requesters[0].scoreboard.warp_id)

#        print "%d coalesces" % num_coalesces
#        print request

    def issue(self, bank_caches):
#        print "ISSUE ==========="
#        self.dump()

        num_issued = 0
        for i in range(len(bank_caches)):
            # Find the first request that maps to this bank.
            # Since the oldest warps are on top of the deque, this means
            #  old requests will be issued before new ones.
            first_request = None
            first_request_lane = 0
            first_request_idx = 0
            for warp_idx, warp in enumerate(self.request_deque):
                for j in range(len(warp)):
                    if warp[j] is None:
                        continue
                    if self.banking_policy.bank(warp[j].cache_line) == i and bank_caches[i].can_accept_line(warp[j].cache_line):
                        first_request = warp[j]
                        first_request_lane = j
                        first_request_idx = warp_idx
                        warp[j] = None
                        break
                if first_request is not None:
                    break
            
            # If nothing matched, we can't issue to this bank this cycle.
            if first_request is None:
                continue

            # Otherwise coalesce with all other requests to that line.
            self.coalesce_all(first_request, first_request_lane, first_request_idx)
            self.coalesce_stats(first_request)

            # Send the request off to the bank.
            bank_caches[i].accept(first_request)
            num_issued += 1

        # If the first rows in the deque have no more requests, pop it.
#        self.dump()

        num_pop = 0
        for warp in self.request_deque:
            all_none = True
            for request in warp:
                if request is not None:
                    all_none = False
                    break
            if not all_none:
                break
            else:
                num_pop += 1
        for i in range(num_pop):
            self.request_deque.pop(0)
 #       print "Num_pop:", num_pop
 #       print "END ISSUE ==============="
 #       print ""

    def dump(self):
        print "Buffer:"
        for warp in self.request_deque:
            print "Warp: ",
            for request in warp:
                if request is None:
                    print "[none]",
                else:
                    print request,
            print ""
        print ""

    def tick(self):
        pass
