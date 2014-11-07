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

class NVidiaCoalescer(object):
    def __init__(self, line_size, num_banks, miss_queue):
        self.miss_queue = miss_queue
        self.bytes_per_bank = line_size / num_banks
        self.queue_size = 1
        self.line_size = line_size
        self.num_banks = num_banks
        self.n_requests = []

    def can_accept(self):
        return len(self.n_requests) < self.queue_size

    def accept(self, requests):
        # requests is a list of requests from a warp.
        # Group requests by cache line
        lines = {}
        for request in requests:
            if request.cache_line not in lines:
                lines[request.cache_line] = []
            lines[request.cache_line].append(request)

        # For each cache line, see which words need
        #  to be read.
        for line, request_list in lines.iteritems():
            words = [False for x in range(num_banks)]
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

            n_request = NVidiaRequest(words, merged_request)
            self.n_requests.append(n_request)

    def can_issue(self):
        return len(self.n_requests) > 0

    # Unlike the other coalescers, this returns a set of accesses
    #  that will go to one bank. The method has a different name
    #  to show it has different semantics.
    def nvidia_issue(self):
        assert(self.can_issue())
        issue = [self.n_requests.pop(0)]

        # Within a line, we're guaranteed no bank conflicts.
        # We can do as many lines in the queue, in order,
        #  until there are no bank conflicts.
        while len(self.n_requests):
            can_issue = True
            for req in issue:
                if req.is_bank_conflict(self.n_requests[0]):
                    can_issue = False
                    break

            if can_issue:
                issue.append(self.n_requests.pop(0))
            else:
                break
            
        return [x.request for x in issue]
