# Collect statistics.

class Stats(object):
    def __init__(self):
        self.stats = {}
        self.stats["int_instructions"] = 0
        self.stats["fp_instructions"] = 0
        self.stats["load_instructions"] = 0
        self.stats["store_instructions"] = 0
        self.stats["total_instructions"] = 0

    def increment(self, name, amount):
        if name not in self.stats:
            self.stats[name] = amount
        else:
            self.stats[name] += amount

    def set(self, name, amount):
        self.stats[name] = amount

    def set_ipc(self):
        self.stats["total_instructions"] = self.stats["int_instructions"] + self.stats["fp_instructions"] \
            + self.stats["load_instructions"] + self.stats["store_instructions"]
        self.stats["ipc"] = float(self.stats["total_instructions"]) / float(self.stats["num_cycles"])

    def dump(self):
        for key in sorted(self.stats):
            if key == "ipc":
                print "%s\t%.2f" % (key, self.stats[key])
            else:
                print "%s\t%d" % (key, self.stats[key])

