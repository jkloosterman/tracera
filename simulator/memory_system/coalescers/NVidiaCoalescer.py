# A coalescer that behaves like the shared memory in
#  http://docs.nvidia.com/cuda/cuda-c-programming-guide/index.html#shared-memory-5-x__examples-of-strided-shared-memory-accesses
#
# This coalescer assumes the miss queue can accept any number
#   of requests per cycle. This mimics how any number of cache
#   lines can be accessed by the nVidia cache. The bank conflicts
#   within a line are handled by the coalescer.
#
# The 128-byte line is split across 32 4-byte banks. Each bank can access
#  one line per cycle.

class NVidiaRequest(object):
    def __init__(self, request, words):
        # The standard memory system request that will be used to notify
        #  the warp it can wake up.
        self.request = request
        self.words = words

    def is_bank_conflict(self, other):
        assert(len(self.words) == len(other.words))
        for i in range(len(self.words)):
            if self.words[i] and other.words[i]:
                return True
        return False

    def __repr__(self):
        count = 0
        for word in self.words:
            if word:
                count += 1
        return str(self.request.cache_line) + ": " + str(count)

class NVidiaCoalescer(object):
    def __init__(self, line_size, num_banks, stats):
        self.bytes_per_bank = line_size / num_banks
        self.queue_size = 1
        self.line_size = line_size
        self.num_banks = num_banks
        self.stats = stats
        self.n_requests = []

    def canAccept(self):
        return len(self.n_requests) < self.queue_size

    def accept(self, requests):
        # requests is a list of requests from a warp.
        # Group requests by cache line
        lines = {}
        for request in requests:
            if request is None:
                continue
            if request.cache_line not in lines:
                lines[request.cache_line] = []
            lines[request.cache_line].append(request)

        # For each cache line, see which words need
        #  to be read.
        n_requests = []
        for line, request_list in lines.iteritems():
            words = [False for x in range(self.num_banks)]
            for i in range(self.num_banks):
                min_address = line + (self.bytes_per_bank * i)
                max_address = line + (self.bytes_per_bank * (i + 1))

                for request in request_list:
                    low_address = request.address
                    high_address = request.address + request.size
                    if low_address >= min_address and high_address < max_address:
                        words[i] = True
                        break

            # Create a Request for all the warps
            merged_request = request_list[0]
            for i in range(1, len(request_list)):
                merged_request.merge(request_list[i])

            n_request = NVidiaRequest(merged_request, words)
            n_requests.append(n_request)
            self.n_requests.append(n_request)

        self.bank_conflict_histogram(n_requests)

    def bank_conflict_histogram(self, n_requests):
        # the number of bank conflicts is the maximum number of n_requests
        #  that have the same bit set.
        max_requests = 0
        num_words = len(n_requests[0].words)
        for i in range(num_words):
            num_requests = 0
            for req in n_requests:
                if req.words[i]:
                    num_requests += 1
            max_requests = max(max_requests, num_requests)

        self.stats.increment("nvidia_accepts", 1)
        self.stats.increment("nvidia_lines_%d" % (len(n_requests)), 1)
        if max_requests > 1:
            self.stats.increment("nvidia_bank_conflicts", max_requests - 1)
            self.stats.increment("nvidia_bank_conflicts_%d" % (max_requests - 1),1)
            self.stats.increment("nvidia_bank_conflict_accepts", 1)

    def canIssue(self):
        return len(self.n_requests) > 0

    def issue(self, bank_caches):
        assert(self.canIssue())
        assert(len(bank_caches) == 1 and "nVidia coalescer requires one bank.")
        
        if not bank_caches[0].can_accept_line(self.n_requests[0].request.cache_line):
            self.stats.increment("nvidia_cant_issue_first_line", 1)
            return
        issued = [self.n_requests[0]]
        bank_caches[0].accept(self.n_requests.pop(0).request)

        # Within a line, we're guaranteed no bank conflicts.
        # We can do as many lines in the queue, in order,
        #  until there are no bank conflicts.
        while len(self.n_requests) > 0:
            if not bank_caches[0].can_accept_line(self.n_requests[0].request.cache_line):
                self.stats.increment("nvidia_cant_issue_more_lines", 1)
                break

            can_issue = True

            # Check for bank conflicts with already-issued requests
            for req in issued:
                if req.is_bank_conflict(self.n_requests[0]):
                    can_issue = False
                    break

            if can_issue:
                issued.append(self.n_requests[0])
                bank_caches[0].accept(self.n_requests.pop(0).request)
            else:
                self.stats.increment("nvidia_cant_issue_bank_conflict", 1)
                break
        
        if len(self.n_requests) == 0:
            self.stats.increment("nvidia_cant_issue_all_issued", 1)

        self.stats.increment("nvidia_lines_issued_%d" % len(issued), 1)

    def dump(self):
        print "Nvidia coalescer:"
        print self.n_requests
