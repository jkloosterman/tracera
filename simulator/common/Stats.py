# Collect statistics.

class Stats(object):
    def __init__(self):
        self.stats = {}
        self.stats["int_instructions"] = 0
        self.stats["fp_instructions"] = 0
        self.stats["load_instructions"] = 0
        self.stats["store_instructions"] = 0
        self.stats["total_instructions"] = 0

        self.averages = set()
        self.average_counts = {}

    def initialize(self, name):
        if name not in self.stats:
            self.stats[name] = 0

    def initialize_average(self, name):
        self.initialize(name)
        self.averages.add(name)
        self.average_counts[name] = 0

    def increment(self, name, amount):
        if name not in self.stats:
            self.stats[name] = amount
        else:
            self.stats[name] += amount

    def increment_max(self, name, amount):
        if name not in self.stats:
            self.stats[name] = amount
        else:
            self.stats[name] = max(self.stats[name], amount)

    def increment_average(self, name, amount):
        self.stats[name] += amount
        self.average_counts[name] += 1

    # Fixme to handle multiple cores better.
    def increment_core(self, core_idx, name, amount):
        self.increment("%s_%d" % (name, core_idx), amount)

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
            elif key in self.averages and self.average_counts[key] > 0:
                print "%s\t%f" % (key, float(self.stats[key]) / self.average_counts[key])
            else:
                print "%s\t%d" % (key, self.stats[key])

    def dump_csv_headers(self, fp):
        for key in sorted(self.stats):
            fp.write("%s\t" % key)

    def dump_csv(self, fp):
        for key in sorted(self.stats):
            if key == "ipc":
                fp.write("%.2f" % self.stats[key])
            elif key in self.averages and self.average_counts[key] > 0:
                fp.write("%f" % (float(self.stats[key]) / self.average_counts[key]))
            else:
                fp.write("%d" % self.stats[key])
            fp.write("\t")
        
    
