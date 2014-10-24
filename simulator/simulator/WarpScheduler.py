class WarpSchedulerOutput(object):
    def get_width(self):
        raise NotImplementedError()
    def get_type(self):
        raise NotImplementedError()
    def can_accept(self):
        raise NotImplementedError()
    def accept(self, warp):
        raise NotImplementedError()

class WarpScheduler(object):
    def __init__(self, scoreboards, outputs, issue_width):
        self.scoreboards = scoreboards
        self.outputs = outputs
        self.issue_width = issue_width

    def accepting_outputs(self):
        for output in self.outputs:
            if output is not None and output.can_accept():
                yield output

    def accepting_outputs_type(self, op_type):
        for output in self.accepting_outputs():
            if output.get_type() == op_type:
                yield output

    def ready_scoreboards(self):
        for scoreboard in self.scoreboards:
            if scoreboard is not None and scoreboard.can_issue():
                yield scoreboard

    def issue(self, scoreboard, output):
        output_width = output.get_width()
        w = scoreboard.issue_warp(output_width)
        output.accept(w)

class WarpSchedulerRR(WarpScheduler):
    def __init__(self, scoreboards, outputs, issue_width):
        super(WarpSchedulerRR, self).__init__(scoreboards, outputs, issue_width)
        self.curScoreboard = 0

    def schedule(self):
        attempted_issue = 0
        num_issued = 0

        while attempted_issue < len(self.scoreboards):
            if self.scoreboards[self.curScoreboard] is not None and self.scoreboards[self.curScoreboard].can_issue():
                op_type = self.scoreboards[self.curScoreboard].can_issue_type()
                type_outputs = list(self.accepting_outputs_type(op_type))
                if len(type_outputs) > 0:
                    self.issue(self.scoreboards[self.curScoreboard], type_outputs[0])
                    num_issued += 1
                    if num_issued == self.issue_width:
                        break

            self.curScoreboard = (self.curScoreboard + 1) % len(self.scoreboards)
            attempted_issue += 1
