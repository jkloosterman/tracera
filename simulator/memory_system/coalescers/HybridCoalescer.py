from Coalescer import Coalescer

# Dispatch the oldest request to each warp.
class HybridCoalescer(Coalescer):
    def __init__(self, banking_policy, depth, name, stats):
        super(HybridCoalescer, self).__init__(banking_policy, name, stats)
        self.depth = depth
        self.request_deque = []
        self.stats.initialize_average("coalescer_queue_occupancy")
        self.stats.initialize_average("hybrid_queue_max_head_distance_avg")
        self.stats.initialize("hybrid_queue_max_head_distance_max")

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

    def issue(self, bank_caches):
#        print "ISSUE ==========="
#        self.dump()

        max_width = 0
        for warp in self.request_deque:
            if len(warp) > max_width:
                max_width = len(warp)

        num_issued = 0
        for bank in range(len(bank_caches)):
            # Find the first request that maps to this bank out of the set of
            # requests that are at the top of each lane of the deque.
            first_request = None
            first_idx = len(self.request_deque)
            first_lane = 0
            for lane in range(max_width):
                for idx, warp in enumerate(self.request_deque):
                    if lane < len(warp) and warp[lane] is not None:
                        if self.banking_policy.bank(warp[lane].cache_line) == bank \
                                and (idx < first_idx) \
                                and bank_caches[bank].can_accept_line(warp[lane].cache_line):
                            first_request = warp[lane]
                            first_lane = lane
                            first_idx = idx
                        break


            # If nothing matched, we can't issue to this bank this cycle.
            if first_request is None:
                continue
            else:
                self.request_deque[first_idx][first_lane] = None

            # Otherwise coalesce with all other requests to that line.
            self.coalesce_all(first_request, first_lane, first_idx)
            self.coalesce_stats(first_request)

            # Send the request off to the bank.
            bank_caches[bank].accept(first_request)
            num_issued += 1

        # If the first rows in the deque have no more requests, pop it.
        #self.dump()

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
        self.stats.increment_average("coalescer_queue_occupancy", len(self.request_deque))

        max_width = 0
        for warp in self.request_deque:
            if len(warp) > max_width:
                max_width = len(warp)

        heads = []
        for lane in range(max_width):
            for idx, warp in enumerate(self.request_deque):
                if lane < len(warp) and warp[lane] is not None:
                    heads.append(idx)
                    break
        
        if len(heads):
            min_head = min(heads)
            max_head = max(heads)
            head_distance = max_head - min_head

            self.stats.increment_average("hybrid_queue_max_head_distance_avg", head_distance)
            self.stats.increment_max("hybrid_queue_max_head_distance_max", head_distance)
