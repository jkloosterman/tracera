#!/home/jklooste/pypy/bin/pypy -u
#
# Simulator, Mark 2
# @author John Kloosterman
# @date Oct. 16, 2014

import sqlite3
import sys
import imp
import json
import tempfile
import shutil
import os

from memory_system.MemorySystemFactory import MemorySystemFactory
from warp_assembly.warp_assembly import *
from simulator.simulator import *
from common.Stats import Stats

# Config files should be Python. That way they
#  can build memory systems and such.
def load_config(filename):
    config_mod = imp.load_source("config", filename)
        
    assert(hasattr(config_mod, 'Config'))
    return getattr(config_mod, 'Config')()

config_params = [
    "sqlite_file",
    "loop_id",
    "num_cores",
    "warp_width",
    "num_active_warps",
    "issue_width",
    "num_banks",
    "line_size",
    "mem_frontend_depth",
    "dram_latency",
    "miss_queue_size",
    "coalescer"
]
def dump_config_csv(config, fp):
    for param in config_params:
        fp.write("%s\t" % str(getattr(config, param)))

def main():
    if len(sys.argv) != 2:
        print "simulator.py <config file>"
        exit(1)

    # Load configuration
    config_file = sys.argv[1]
    config = load_config(config_file)

    sqlite_file = config.sqlite_file
    loop_id = config.loop_id
    warp_width = config.warp_width

    if config.on_simpool:
        local_filename = tempfile.mktemp(dir="/tmp")
        print "Copying sqlite file to", local_filename
        shutil.copy(sqlite_file, local_filename)
        print "Done."
    else:
        local_filename = sqlite_file

    db = sqlite3.connect(local_filename)

    # Set up and run the simulation
    stats = Stats()
    warp_assembly = WarpAssembly(db, loop_id, warp_width)
    memory_system_factory = MemorySystemFactory(config, stats)
    simulator = Simulator(warp_assembly, memory_system_factory, config, stats)
    num_cycles = simulator.simulate()

    db.close()
    if config.on_simpool:
        os.remove(local_filename)

    # Dump data for reproduceability
    with open(config.output_file, "w") as fp:
        dump_config_csv(config, fp)
        fp.write("%d\n" % num_cycles)

main()
