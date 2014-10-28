class CacheSet(object):
    def __init__(self, mem_side, associativity, hit_latency):
        self.mem_side = mem_side
        self.associativity = associativity
        self.hit_latency = hit_latency
        self.lines = []
        self.future_events = {}
        self.cur_tick = 0
        self.mshrs = {}

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
        else:
            return self.mem_side.can_accept_line(line)

    def accept(self, line):
        hit_idx = self.is_hit(line)
        if hit_idx > -1:
            self.lines.pop(hit_idx)
            self.lines.append(line)
            return self.hit_latency

        # A miss. Merge with request in MSHR
        if line in self.mshrs:
            return self.mshrs[line] - self.cur_tick

        # Or launch a new mem-side request.
        if self.mem_side.can_accept_line(line):
            latency = self.mem_side.accept(line)

            assert(latency > 0)
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

        if len(self.future_events) > 0:
            print "Cache set:"
            print "Cur_tick:", self.cur_tick
            print "Future events: ", self.future_events

        if self.cur_tick in self.future_events:
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
                

    
