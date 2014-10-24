class MemoryTraceNode(object):
    def __init__(self, db, memory_trace_id, bb_sequence, mem_sequence):
#        print "MTN: ", memory_trace_id, bb_sequence, mem_sequence

        c = db.cursor()
        c.execute(
            "SELECT memoryTraceNodes.memoryTraceNodeId, type, size, base, coefficient, baseIteration "
            + "FROM memoryTraceNodes "
            + "JOIN memoryTraces USING (memoryTraceNodeId) "
            + "WHERE memoryTraceId = ? AND bbSequence = ? AND memoryTraces.sequence = ? ",
            (memory_trace_id, bb_sequence, mem_sequence))
        row = c.fetchone()

        if row is None:
            print "NON-EXISTENT MTN:"
            print "MemoryTraceId: ", memory_trace_id
            print "bb_sequence: ", bb_sequence
            print "mem_sequence: ", mem_sequence
            exit(1)

        self.db = db
        self.memory_trace_node_id = row[0]
        self.type = row[1]
        self.size = row[2]
        self.base = row[3]
        self.coefficient = row[4]
        self.base_iteration = row[5]

    def getAddress(self, iteration):
        if self.type == 0:
            # Constant
            return (self.base, self.size)
        elif self.type == 1:
            # Linear
            address = self.base + (self.coefficient * (iteration - self.base_iteration))
            return (address, self.size)
        elif self.type == 2:
            # Random
            c = self.db.cursor()
            c.execute(
                "SELECT address "
                "FROM memoryTraceNodeAddresses "
                "WHERE memoryTraceNodeId=? AND iteration=?",
                (self.memory_trace_node_id, iteration))

            row = c.fetchone()
            if row is None:
                print "NO SUCH RANDOM ADDRESS"
                print "MTN ID:", self.memory_trace_node_id,
                print "iteration:", iteration
                exit(1)

            return (row[0], self.size)
        else:
            assert(False and "Bad MemoryTraceNode type")
