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
import time

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
    "run_id",
    "num_cores",
    "warp_width",
    "num_active_warps",
    "issue_width",
    "num_banks",
    "line_size",
    "mem_frontend_depth",
    "dram_latency",
    "dram_ports",
    "miss_queue_size",
    "coalescer",
    "l1_size",
    "coalescer_depth",
    "banking_policy"
]

def dump_config_csv(config, fp):
    for param in config_params:
        fp.write("%s\t" % str(getattr(config, param)))

def dump_config_csv_headers(config, fp):
    for param in config_params:
        fp.write("%s\t" % param)

def atomic_copy(src, dest, lockfile):
    proceed = False
    while not proceed:
        if os.path.exists(dest):
            if os.path.exists(lockfile):
                print "atomic_copy: waiting for copy of", dest, "to finish."
                time.sleep(5)
            else:
                print "atomic_copy:", dest, "ready"
                proceed = True
        else:
            try:
                print "atomic_copy: taking copy lock for", dest
                # Try taking the lock.
                fd = os.open(lockfile, os.O_CREAT | os.O_EXCL)

                # Perform the copy
                shutil.copy(src, dest)

                # Close the lock file
                os.close(fd)
                # And delete it.
                os.remove(lockfile)
                proceed = True
            except OSError:
                print "atomic_copy: lost race for copy lock for", dest
                time.sleep(5)

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
        sqlite_file_no_path = os.path.basename(sqlite_file)
        local_filename = os.path.join("/tmp", sqlite_file_no_path)
        lock_file_no_path = sqlite_file_no_path + ".lock"
        lock_filename = os.path.join("/tmp", lock_file_no_path)

        print "atomic copy of %s to %s, lockfile %s" % (sqlite_file, local_filename, lock_filename)
        atomic_copy(sqlite_file, local_filename, lock_filename)
        print "copy done."
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

    # Dump data for reproduceability
    with open(config.output_file, "w") as fp:
        dump_config_csv_headers(config, fp)
        stats.dump_csv_headers(fp)
        fp.write("\n")

        dump_config_csv(config, fp)
        stats.dump_csv(fp)

main()
