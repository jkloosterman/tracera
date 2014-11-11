class Coalescer(object):
    def __init__(self, banking_policy, name, stats):
        self.banking_policy = banking_policy
        self.name = name
        self.stats = stats
        self.stats.initialize_average("requesters_per_request")

    def coalesce_stats(self, request):
        # record # coalesces, # requestors (since we need to store all those)
        self.stats.increment("intra_warp_coalesces", request.intra_warp_coalesces)
        self.stats.increment("inter_request_coalesces", request.inter_request_coalesces)
        self.stats.increment("inter_instruction_coalesces", request.inter_instruction_coalesces)
        self.stats.increment("inter_warp_coalesces", request.inter_warp_coalesces)
        self.stats.increment_average("requesters_per_request", len(request.requesters))
        self.stats.increment_max("requesters_per_request_max", len(request.requesters))
