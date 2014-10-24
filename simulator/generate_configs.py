#!/usr/bin/python
#
# Generate configuration files and Condor launch files
#  for a range of configurations.

import sys

begin_template = """
class Config:
    def __init__(self):
        self.on_simpool = True
"""

end_template = """
        self.pipelines = [
            { "width": self.warp_width, "type": "I", "stages": 3 },
            { "width": self.warp_width, "type": "F", "stages": 5 },
            { "width": self.warp_width, "type": "M" } ]
"""

params = [
    ("num_cores", [1]),
    ("warp_width", [4, 8, 16]),
    ("num_active_warps", [4, 16]),
    ("issue_width", [1, 3]),
    ("num_banks", [1, 2, 4]),
    ("line_size", [64]),
    ("mem_frontend_depth", [2]),
    ("dram_latency", [10, 50, 100]),
    ("miss_queue_size", [20])
]

if len(sys.argv) != 3:
    print "generate_configs.py <sqlite db> <loop id>"
    exit(1)

# Make sure we know the impact of starting all these jobs
num_configs = 1
for param in params:
    num_configs *= len(param[1])
print "This will launch %d simulations on the simpool. OK?" % num_configs
raw_input()

cur_config = 0
def create_recursive(text, idx):
    global cur_config

    for option in params[idx][1]:
        my_text = text[:]
        my_text += "\tself.%s = %s\n" % (params[idx][0], str(option))

        if idx == len(params) - 1:
            fp = open("configs/gen_%d.py" % cur_config, "w")
            
            my_text += "\tself.output_file = 'out/gen_%d.csv'\n" % cur_config
            fp.write(begin_template)
            fp.write(my_text)
            fp.write(end_template)
            fp.write("\n")

            cur_config += 1
        else:
            create_recursive(my_text, idx + 1)

sqlite_file = sys.argv[1]
loop_id = sys.argv[2]
text = "\tself.sqlite_file = '%s'\n\tself.loop_id = %s\n" % (sqlite_file, loop_id)
create_recursive(text, 0)

def create_condor_file():
    fp = open("submit.condor", "w")

    fp.write("Executable = /home/jklooste/michigan-workspace/october_2014/warp_assembly/simulator.py\n")
    fp.write("\n")

    for i in range(cur_config):
        fp.write("Log = logs/gen_%d.log\n" % i)
        fp.write("Output = logs/gen_%d.out\n" % i)
        fp.write("Error = logs/gen_%d.err\n" % i)
        fp.write("Getenv = true\n")
        fp.write("Arguments = configs/gen_%d.py\n" % i)
        fp.write("Queue\n")
        fp.write("\n")

    fp.close()

create_condor_file()
