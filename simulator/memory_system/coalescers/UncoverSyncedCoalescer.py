from Coalescer import Coalescer

class UncoverSyncedCoalescer(Coalescer):
    def __init__(self, banking_policy, depth, sync_distance, name, stats):
        super(UncoverSyncedCoalescer, self).__init__(banking_policy, name, stats)
        self.depth = depth
        self.request_deque = []
        self.stats.initialize_average("coalescer_queue_occupancy")
        self.stats.initialize_average("uncover_synced_queue_max_head_distance_avg")
        self.stats.initialize("uncover_synced_queue_max_head_distance_max")

        self.sync_distance = sync_distance
        self.sync_mode = False

    def canAccept(self):
        return len(self.request_deque) < self.depth

    def accept(self, requests):
        self.request_deque.append(list(requests))

    def canIssue(self):
        return len(self.request_deque) > 0

    def coalesce_top(self, request):
        max_width = 0
        for warp in self.request_deque:
            if len(warp) > max_width:
                max_width = len(warp)

        num_coalesces = 0
        for lane in range(max_width):
            for idx, warp in enumerate(self.request_deque):
                if lane < len(warp) and warp[lane] is not None:
                    if warp[lane].cache_line == request.cache_line and warp[lane].access_type == request.access_type:
                        request.merge(warp[lane])
                        warp[lane] = None
                        num_coalesces += 1
                    break
#        print "%d coalesces" % num_coalesces
#        print request

    def issue(self, bank_caches):
#        print "ISSUE ==========="
#        self.dump()

        max_width = 0
        for warp in self.request_deque:
            if len(warp) > max_width:
                max_width = len(warp)

        # We are currently resyncing.
        non_issuable_lanes = set()
        if self.sync_mode:
            heads = []
            for lane in range(max_width):
                for idx, warp in enumerate(self.request_deque):
                    if lane < len(warp) and warp[lane] is not None:
                        heads.append((idx, lane))
                        break

            max_head = max(heads)[0]
            non_issuable_lanes = set([x[1] for x in heads if x[0] == max_head])
#            print "Sync mode: max:", max_head, "non issuable lanes:", non_issuable_lanes
            if len(non_issuable_lanes) == len(heads):
#                print "SYNC MODE DONE ********************"
                self.sync_mode = False

        num_issued = 0
        for bank in range(len(bank_caches)):
            # Find the first request that maps to this bank out of the set of
            # requests that are at the top of each lane of the deque.
            first_request = None
            first_idx = len(self.request_deque)
            first_lane = 0
            for lane in range(max_width):
                if lane in non_issuable_lanes:
                    continue
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
            self.coalesce_top(first_request)
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

            if head_distance >= self.sync_distance:
                self.sync_mode = True

            self.stats.increment_average("uncover_synced_queue_max_head_distance_avg", head_distance)
            self.stats.increment_max("uncover_synced_queue_max_head_distance_max", head_distance)

        if self.sync_mode:
            self.stats.increment("uncover_synced_sync_cycles", 1)
        else:
            self.stats.increment("uncover_synced_non_sync_cycles", 1)
