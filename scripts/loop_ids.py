#!/usr/bin/python

import sys
import sqlite3

if len(sys.argv) != 3:
    print "loop_ids.py <sqlite db> <static id>"
    exit(1)

db = sqlite3.connect(sys.argv[1])
c = db.cursor()

c.execute("SELECT loopId FROM loops WHERE staticId=? LIMIT 1", (sys.argv[2],))
print c.fetchone()[0]
