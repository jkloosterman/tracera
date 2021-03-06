class CacheSet(object):
    def __init__(self, cache, mem_side, associativity, hit_latency, stats, name):
        self.cache = cache
        self.mem_side = mem_side
        self.associativity = associativity
        self.hit_latency = hit_latency
        self.lines = []
        self.future_events = {}
        self.cur_tick = 0
        self.mshrs = {}
        self.stats = stats
        self.name = name

        self.stats.initialize(self.name + ".hits")
        self.stats.initialize(self.name + ".mshr_merges")
        self.stats.initialize(self.name + ".misses")
        self.stats.initialize("total_hits")
        self.stats.initialize("total_mshr_merges")
        self.stats.initialize("total_misses")

    def is_hit(self, line):
        hit_idx = -1
        for i in range(len(self.lines)):
            if line == self.lines[i]:
                hit_idx = i
                break
        return hit_idx

    def can_accept_line(self, line):
        if self.is_hit(line) > -1:
            return True
        elif line in self.mshrs:
            return True
        elif not self.cache.has_outstanding_request():
            return False
        else:
            return self.mem_side.can_accept_line(line)

    def accept(self, line):
        hit_idx = self.is_hit(line)
        if hit_idx > -1:
            self.stats.increment(self.name + ".hits", 1)
            self.stats.increment("total_hits", 1)
            self.lines.pop(hit_idx)
            self.lines.append(line)
            return self.hit_latency

        # A miss. Merge with request in MSHR
        if line in self.mshrs:
            self.stats.increment(self.name + ".mshr_merges", 1)
            self.stats.increment("total_mshr_merges", 1)
            return self.mshrs[line] - self.cur_tick

        # Or launch a new mem-side request.
        if self.mem_side.can_accept_line(line):
            self.stats.increment(self.name + ".misses", 1)
            self.stats.increment("total_misses", 1)
            latency = self.mem_side.accept(line)

            assert(latency > 0)
            self.cache.outstanding_request_add()
            data_tick = self.cur_tick + latency
            
            if data_tick in self.future_events:
                self.future_events[data_tick].append(line)
            else:
                self.future_events[data_tick] = [line]

            self.mshrs[line] = data_tick
            return latency
        else:
            assert(False and "We promised to accept something that we can't.")

    def tick(self):
        self.cur_tick += 1

#        if len(self.future_events) > 0:
#            print "Cache set:"
#            print "Cur_tick:", self.cur_tick
#            print "Future events: ", self.future_events

        if len(self.future_events) > 0 and self.cur_tick in self.future_events:
            lines = self.future_events[self.cur_tick]
            del self.future_events[self.cur_tick]

            for line in lines:
                hit_idx = self.is_hit(line)
                assert(hit_idx == -1)
                
                # Remove the oldest, put us at the back.
                if len(self.lines) == self.associativity:
                    self.lines.pop(0)
                self.lines.append(line)
                del self.mshrs[line]
                self.cache.outstanding_request_finished()
                

    
