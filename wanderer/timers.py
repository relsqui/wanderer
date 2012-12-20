class Timer(object):
    """
    Calls a function after a specified interval. Arguments:
        timeout     (milliseconds)
        action      (function)
        *arguments  (will be passed to function)

    New Timers automatically add themselves to the list of timers when instantiated and remove themselves when they expire.
    """

    def __init__(self, timeout, action, *arguments):
        super(Timer, self).__init__()
        self.counter = timeout
        self.action = action
        self.arguments = arguments
        all_timers.append(self)

    def update(self, loop_time):
        "Decrement the counter; if it runs out, fire the action and self-destruct."
        self.counter -= loop_time
        if self.counter <= 0:
            self.action(*self.arguments)
            all_timers.remove(self)

    def cancel(self):
        "Destroy the timer without firing the action."
        if self in all_timers:
            all_timers.remove(self)

all_timers = []
