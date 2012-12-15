class Timer(object):
    def __init__(self, timeout, action, *arguments):
        super(Timer, self).__init__()
        self.counter = timeout
        self.action = action
        self.arguments = arguments
        all_timers.append(self)

    def update(self, loop_time):
        self.counter -= loop_time
        if self.counter <= 0:
            self.action(*self.arguments)
            all_timers.remove(self)

all_timers = []
