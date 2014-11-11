from Coalescer import Coalescer

class IntrawarpCoalescer(Coalescer):
    def __init__(self, banking_policy, name, stats):
        super(IntrawarpCoalescer, self).__init__(banking_policy, name, stats)
        self.bank_reqs = {}

    def canAccept(self):
        return len(self.bank_reqs) == 0

    def accept(self, requests):
        # Group by cache line
        lines = {}
        for r in requests:
            if r is None:
                continue
            if r.cache_line not in lines:
                lines[r.cache_line] = [r]
            else:
                lines[r.cache_line].append(r)

        # Determine the coalesced requests to go to each bank
        self.bank_reqs = {}
        for line, requests in lines.iteritems():
            # Coalesce the accesses in each line
            first = requests[0]

            for req in requests:
                if req == first:
                    continue
                first.merge(req)

            # Determine which bank we map to.
            bank = self.banking_policy.bank(line)

            if bank not in self.bank_reqs:
                self.bank_reqs[bank] = [first]
            else:
                self.bank_reqs[bank].append(first)

        max_bank_requests = 0
        for bank, requests in self.bank_reqs.iteritems():
            max_bank_requests = max(max_bank_requests, len(requests))
        if max_bank_requests > 1:
            self.stats.increment("intra_warp_bank_conflicts", max_bank_requests - 1)
            self.stats.increment("intra_warp_bank_conflicts_%d" % (max_bank_requests - 1), 1)
            self.stats.increment("intra_warp_bank_conflict_cycles", 1)

    def canIssue(self):
        return len(self.bank_reqs) > 0

    def issue(self, bank_caches):
        for i in range(len(bank_caches)):
            if i not in self.bank_reqs:
                continue
            if not bank_caches[i].can_accept_line(self.bank_reqs[i][-1].cache_line):
                continue
            
            bank_caches[i].accept(self.bank_reqs[i].pop())
            if len(self.bank_reqs[i]) == 0:
                del self.bank_reqs[i]
    
    def dump(self):
        print "Intrawarp Coalescer: %d banks with requests" % len(self.bank_reqs)
