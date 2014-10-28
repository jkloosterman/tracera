
class Config:
    def __init__(self):
	self.sqlite_file = '/home/jklooste/accelerator_bms/databases/parboil_sad.sqlite'
	self.loop_id = 261374
	self.num_cores = 1
	self.warp_width = 32
	self.num_active_warps = 8
	self.issue_width = 2
	self.num_banks = 4
	self.line_size = 64
	self.mem_frontend_depth = 1

	self.dram_latency = 10
        self.dram_ports = 4

#        self.cache_system = 'dram_only'

        self.cache_system = 'l1'
        self.l1_size = 16384
        self.l1_associativity = 4
        self.l1_latency = 1

	self.miss_queue_size = 50
	self.output_file = 'out/tau.csv'
        self.on_simpool = False
#       self.coalescer = 'intra_warp'
        self.coalescer = 'full_associative_oldest'

        self.pipelines = [
            { "width": 16, "type": "I", "stages": 2 },
            { "width": 16, "type": "I", "stages": 2 },
            { "width": 16, "type": "F", "stages": 6 },
            { "width": 16, "type": "M", "stages": 5 } ]

