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

    def coalesce_all(self, request, lane, idx):
        # Do a first scan to find any stores to the line in the thread.
        # We can only coalesce requests that come before
        #  the store in the thread.
        store_idx = -1
        if request.access_type == "S":
            store_idx = idx
        else:
            for i, warp in enumerate(self.request_deque):
                if len(warp) > lane:
                    if warp[lane] is None:
                        continue
                    if warp[lane].cache_line != request.cache_line:
                        continue
                    if warp[lane].access_type == "S":
                        store_idx = i
                        break

        num_coalesces = 0
        for warp_idx, warp in enumerate(self.request_deque):
            for i in range(len(warp)):
                # Don't coalesce past stores in the same thread
                if store_idx >= 0 and warp_idx > store_idx and i == lane:
                    continue
                if warp[i] is None:
                    continue
                if warp[i].cache_line == request.cache_line and warp[i].access_type == request.access_type:
                    request.merge(warp[i])
                    warp[i] = None
                    num_coalesces += 1
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
