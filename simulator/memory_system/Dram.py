class Dram(object):
    def __init__(self, num_ports, latency):
        self.num_ports = num_ports
        self.latency = latency
        self.accepted_this_cycle = 0

    def canAccept(self):
        return self.accepted_this_cycle < self.num_ports

    def accept(self, line):
        self.accepted_this_cycle += 1
        return self.latency

    def tick(self):
        self.accepted_this_cycle = 0
