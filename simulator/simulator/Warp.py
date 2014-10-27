class Warp:
    def __init__(self, ip, scoreboard, instruction, active_threads, thread_offset):
        self.ip = ip
        self.scoreboard = scoreboard
        self.instruction = instruction
        self.active_threads = active_threads
        self.thread_offset = thread_offset

    def add_extra_completes(self, thread, num_completes):
        self.scoreboard.add_extra_complete(self.ip, self.thread_offset, thread, num_completes)

    def complete(self):
        self.scoreboard.complete(self)

    def dump(self):
        print "Warp:", self.instruction, ", IP:", self.ip, ",", self.active_threads
