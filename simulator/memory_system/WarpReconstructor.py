# Module that holds Requests while they turn back into Warps.

class WarpReconstructor(object):
    def __init__(self):
        self.request = None

    def canAccept(self):
        return self.request is None

    def accept(self, request):
        self.request = request

    def canIssue(self):
        return self.request is not None

    def issue(self):
        warp = self.request.generateWarp()
        if not self.request.canGenerateWarp():
            self.request = None
        return warp
