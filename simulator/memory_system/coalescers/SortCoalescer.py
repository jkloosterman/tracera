from Coalescer import Coalescer

class SortCoalescer(Coalescer):
    def __init__(self, banking_policy, depth, num_banks, name, stats):
        super(SortCoalescer, self).__init__(banking_policy, name, stats)
        self.depth = depth
        self.bank_deques = [[] for x in range(num_banks)]
        self.stats.initialize_average("coalescer_queue_occupancy")

    def canAccept(self):
        for deque in self.bank_deques:
            if len(deque) >= self.depth:
                return False
        return True

    def accept(self, requests):
        for req in requests:
            if req is None:
                continue
            bank = self.banking_policy.bank(req.cache_line)
            self.bank_deques[bank].append(req)

    def canIssue(self):
        for deque in self.bank_deques:
            if len(deque) > 0:
                return True
        return False

    def issue(self, bank_caches):
        for bank_idx, bank in enumerate(bank_caches):
            if len(self.bank_deques[bank_idx]) == 0:
                continue

            line = self.bank_deques[bank_idx][0].cache_line
            if not bank.can_accept_line(line):
                continue

            coalesces = []
            for idx, req in enumerate(self.bank_deques[bank_idx]):
                if req.cache_line == line:
                    coalesces.append(idx)
            
            req = self.bank_deques[bank_idx][0]
            # Reversed so that we can remove elements without changing
            #  other indices.
            for idx in reversed(coalesces):
                if idx == 0:
                    continue
                req.merge(self.bank_deques[bank_idx].pop(idx))
            self.bank_deques[bank_idx].pop(0)

            self.coalesce_stats(req)
            bank.accept(req)
            
    def tick(self):
        for deque in self.bank_deques:
            self.stats.increment_average("coalescer_queue_occupancy", len(deque))
