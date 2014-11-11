class MissQueue(object):
    def __init__(self, size, cache, stats, name):
        self.size = size
        self.cache = cache
        self.queue = [None for x in range(self.size)]
        self.future_events = {}
        self.cur_tick = 0
        self.ready_idxs = []
        self.stats = stats
        self.name = name
        self.stats.initialize_average(self.name + ".requests")
        self.stats.initialize_average(self.name + ".latency")
        self.stats.initialize_average("miss_queue_occupancy")
        self.stats.initialize_average("miss_queue_ready")
        self.stats.initialize_average("miss_queue_outstanding")
        self.stats.initialize_average("total_avg_latency")

    def can_accept_line(self, line):
        hasSlot = False
        for q in self.queue:
            if q is None:
                hasSlot = True
                break

        return hasSlot and self.cache.can_accept_line(line)

    def accept(self, request):
        assert(self.can_accept_line(request.cache_line))
        latency = self.cache.accept(request.cache_line)
        self.stats.increment_average(self.name + ".requests", 1)
        self.stats.increment_average(self.name + ".latency", latency)
        self.stats.increment_average("total_avg_latency", latency)

        idx = self.addToQueue(request)
        if latency == 0:
            self.ready_idxs.append(idx)
        else:
            ready_tick = self.cur_tick + latency

            if ready_tick in self.future_events:
                self.future_events[ready_tick].append(idx)
            else:
                self.future_events[ready_tick] = [idx]
            
    def canIssue(self):
        return len(self.ready_idxs) > 0
    
    def issue(self):
        idx = self.ready_idxs.pop(0)
        request = self.queue[idx]
        self.queue[idx] = None
        
        return request

    # This should do MSHR coalescing!
    def addToQueue(self, request):
        # find the first empty slot.
        idx = -1
        for i in range(self.size):
            if self.queue[i] is None:
                idx = i
                break
        assert(idx >= 0)

        self.queue[idx] = request
        return idx

    def tick(self):
        self.cur_tick += 1

        occupancy = 0
        for slot in self.queue:
            if slot is not None:
                occupancy += 1

        future_events = 0
        for tick, events in self.future_events.iteritems():
            future_events += len(events)

        self.stats.increment_average("miss_queue_occupancy", occupancy)
        self.stats.increment_average("miss_queue_ready", len(self.ready_idxs))
        self.stats.increment_average("miss_queue_outstanding", future_events)

        if self.cur_tick in self.future_events:
            self.ready_idxs += self.future_events[self.cur_tick]
            del self.future_events[self.cur_tick]

    def dump(self):
        print "cur_tick:", self.cur_tick
        print "Size:", self.size
        print "Ready:", self.ready_idxs
        print "Future events:", self.future_events
        for i in range(self.size):
            print i, self.queue[i]
