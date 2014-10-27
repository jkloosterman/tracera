# Warp scoreboard. Can ask for next instruction from
#  trace reconstructor, tracks whether we are ready to issue
#  a new warp.

from Warp import *

class Scoreboard(object):
    def __init__(self, warp_id, warp_width, warp_stream, stats):
        self.stats = stats
        self.warp_id = warp_id
        self.warp_width = warp_width
        self.warp_stream = warp_stream
        self.warp_iterator = self.warp_stream.instructions()
        self.current_instruction = None
        self.is_finished = False
        self.current_is_load = False
        self.ip = -1

        # issued_threads are the threads that are currently
        #  somewhere else in the core
        self.issued_threads = [False for x in range(warp_width)]

        # to_issue_threads are the threads that have not yet
        #  been issued.
        self.to_issue_threads = [False for x in range(warp_width)]

        # completes are the threads that have completed in
        #  the core. 0 means there are no completes outstanding.
        #  There can be >1 complete outstanding when a memory
        #   request is split.
        self.completes = [1 for x in range(warp_width)]

    def update(self):
        # This is slow. To make it faster, replace the arrays with
        #  bitsets or integers.

        if not self.instruction_complete() or self.is_finished:
            return

        # Get a new instruction
        try:
            self.current_instruction = self.warp_iterator.next()
            self.ip += 1
        except StopIteration:
            self.is_finished = True
            return

        # Reset bitsets
        self.issued_threads = [False for x in range(self.warp_width)]
        self.to_issue_threads = [False for x in range(self.warp_width)]
        self.completes = [1 for x in range(self.warp_width)]

        # Activate threads with real instructions
        num_active_threads = 0
        for i in range(len(self.current_instruction)):
            if self.current_instruction[i] is None:
                self.to_issue_threads[i] = False
            else:
                self.to_issue_threads[i] = True
                num_active_threads += 1

        # See if we are a load, and count instruction type
        for ins in self.current_instruction:
            if ins is None:
                continue
            elif ins == "I":
                self.stats.increment("int_instructions", 1)
                self.stats.increment("int_accesses", num_active_threads)
                self.current_is_load = False
                break
            elif ins == "F":
                self.stats.increment("fp_instructions", 1)
                self.stats.increment("fp_accesses", num_active_threads)
                self.current_is_load = False
                break
            elif ins[2] == "S":
                self.stats.increment("store_instructions", 1)
                self.stats.increment("store_accesses", num_active_threads)
                self.current_is_load = False
                break
            elif ins[2] == "L":
                self.stats.increment("load_instructions", 1)
                self.stats.increment("load_accesses", num_active_threads)
                self.current_is_load = True
                break
            else:
                assert(False and "Unknown instruction type.")


    def bitset_equal(self, a, b):
        assert(len(a) == len(b))
        for i in range(len(a)):
            if a[i] != b[i]:
                return False
        return True

    def all_issued(self):
        for v in self.to_issue_threads:
            if v:
                return False
        return True

    def instruction_complete(self):
        for i in range(self.warp_width):
            if self.issued_threads[i]:
                if self.completes[i] > 0:
                    return False

        return self.all_issued()

    def finished(self):
        return self.is_finished

    def can_issue(self):
        for t in self.to_issue_threads:
            if t:
                return True
        return False

    def issue_warp(self, width):
        # Create a Warp object up to @width wide
        assert(width <= self.warp_width)

        # Only issue in rounded chunks:
        #  [---|   ] OK.
        #  [ |---| ] not OK.
        chunk_offset = 0
        found = False
        while width * chunk_offset < self.warp_width:
            r = min(width * (chunk_offset + 1), self.warp_width)
            for i in range(width * chunk_offset, r):
                if self.to_issue_threads[i]:
                    found = True
                    break
            if found:
                break
            chunk_offset += 1
        
        start = width * chunk_offset
        end = min(width * (chunk_offset + 1), self.warp_width)
        instructions = self.current_instruction[start:end]
        active_threads = self.to_issue_threads[start:end]
        w = Warp(self.ip, self, instructions, active_threads, start)

        for i in range(start, end):
            if self.to_issue_threads[i]:
                self.issued_threads[i] = True

                # If this instruction is a load, make the next instruction
                #  dependent. If not, we can schedule the next instruction
                #  right away.
                if not self.current_is_load:
                    self.completes[i] = 0

            self.to_issue_threads[i] = False

        return w

    # Returns the type of the thing we can issue.
    def can_issue_type(self):
        for ins in self.current_instruction:
            if ins is None:
                continue
            elif ins == "I" or ins == "F":
                return ins
            else:
                return "M"
        assert(False and "Instruction has no type")

    def add_extra_complete(self, ip, thread_offset, thread, num_completes):
        assert(ip == self.ip)
        self.completes[thread_offset + thread] += num_completes

    def complete(self, warp):
        # We weren't waiting for this warp.
        if warp.ip != self.ip:
            return

        for i in range(len(warp.active_threads)):
            if warp.active_threads[i]:
                self.completes[warp.thread_offset + i] -= 1
        
    def dump(self):
        print "Scoreboard %d:" % self.warp_id
        print "Current instruction: ", self.current_instruction
        print "IP: ", self.ip
        print "issued_threads: ", self.issued_threads
        print "to_issue_threads: ", self.to_issue_threads
        print "completed_threads: ", self.completed_threads
