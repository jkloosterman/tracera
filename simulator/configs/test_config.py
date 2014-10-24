# Example configuration file.

class Config:
    def __init__(self):
        self.sqlite_file = "/home/jklooste/accelerator_bms/databases/parboil_sad.sqlite"
        self.loop_id = 3
        self.output_file = "out.csv"

        self.num_cores = 1
        self.warp_width = 4
        self.num_active_warps = 4
        self.issue_width = 2

        self.num_banks = 4
        self.line_size = 64
        self.mem_frontend_depth = 4
        self.dram_latency = 5
        self.miss_queue_size = 20

        self.pipelines = [
            { "width": self.warp_width, "type": "I", "stages": 3 },
            { "width": self.warp_width, "type": "F", "stages": 5 },
            { "width": self.warp_width, "type": "M" } ]
