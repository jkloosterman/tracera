# The cache line keeps track of what will go into it in the future.

class CacheLine(object):
    def __init__(self, mem_side, associativity, hit_latency):
        self.mem_side = mem_side
        self.associativity = associativity
        self.hit_latency = hit_latency
        self.lines = []
        self.future_events = {}
        self.cur_tick = 0

    def is_hit(self, line):
        hit_idx = -1
        for i in range(len(self.lines)):
            if line == lines[i]:
                hit_idx = i
                break
        return hit_idx

    def can_accept_line(self, line):
        if is_hit(line) > -1:
            return True
        else:
            return self.mem_side.can_accept_line(line)

    def accept(self, line):
        hit_idx = is_hit(line)
        if hit_idx:
            self.lines.pop(i)
            self.lines.append(i)
            return hit_latency

        # A miss.
        if self.mem_side.can_accept_line(line):
            latency = self.mem_side.accept(line)

            assert(latency > 0)
            data_tick = self.cur_tick + latency
            
            if data_tick in self.future_events:
                self.future_events[data_tick].append(line)
            else:
                self.future_events[data_tick] = [line]
            return data_tick
        else:
            assert(False and "We promised to accept something that we can't.")

    def tick(self):
        pass

    
