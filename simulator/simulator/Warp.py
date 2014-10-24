class Warp:
    def __init__(self, ip, scoreboard, instruction, active_threads, thread_offset):
        self.ip = ip
        self.scoreboard = scoreboard
        self.instruction = instruction
        self.active_threads = active_threads
        self.thread_offset = thread_offset

    def complete(self):
        self.scoreboard.complete(self)

    def dump(self):
        print "Warp:", self.instruction, ", IP:", self.ip, ",", self.active_threads
