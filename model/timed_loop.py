import time, threading

# Adapted from https://stackoverflow.com/a/48709380

class TimedLoop:
    def __init__(self, interval, fn, *args, **kwargs):
        self.interval = interval
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.stopEvent = threading.Event()
        thread = threading.Thread(target=self._setInterval)
        thread.start()

    def _setInterval(self):
        # immediately execute once
        self.fn(*self.args, **self.kwargs)
        nextTime = time.time() + self.interval
        while not self.stopEvent.wait(nextTime - time.time()) :
            nextTime += self.interval
            self.fn(*self.args, **self.kwargs)

    def cancel(self):
        self.stopEvent.set()