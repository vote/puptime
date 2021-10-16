import time
import itertools


class safe_while(object):
    """
    A helper to remove boiler plate code that deals with `while` loops
    that need a given number of tries and some seconds to sleep between each
    one of those tries.

    The most simple example possible will try 10 times sleeping for 6 seconds:

        >>> with safe_while() as proceed:
        ...    while proceed():
        ...        # repetitive code here
        ...        print("hello world")
        ...
        Traceback (most recent call last):
        ...
        MaxWhileTries: reached maximum tries (5) after waiting for 75 seconds

    Yes, this adds yet another level of indentation but it allows you to
    implement while loops exactly the same as before with just 1 more
    indentation level and one extra call. Everything else stays the same,
    code-wise. So adding this helper to existing code is simpler.

    :param sleep:     The amount of time to sleep between tries. Default 6
    :param increment: The amount to add to the sleep value on each try.
                      Default 0.
    :param tries:     The amount of tries before giving up. Default 10.
    :param action:    The name of the action being attempted. Default none.
    :param _raise:    Whether to raise an exception (or log a warning).
                      Default True.
    :param _sleeper:  The function to use to sleep. Only used for testing.
                      Default time.sleep
    """

    def __init__(
        self, sleep=6, increment=0, tries=10, action=None, _raise=True, _sleeper=None
    ):
        self.sleep = sleep
        self.increment = increment
        self.tries = tries
        self.counter = 0
        self.sleep_current = sleep
        self.action = action
        self._raise = _raise
        self.sleeper = _sleeper or time.sleep

    def _make_error_msg(self):
        """
        Sum the total number of seconds we waited while providing the number
        of tries we attempted
        """
        total_seconds_waiting = sum(
            itertools.islice(itertools.count(self.sleep, self.increment), self.tries)
        )
        msg = "reached maximum tries ({tries})" + " after waiting for {total} seconds"
        if self.action:
            msg = "'{action}' " + msg

        msg = msg.format(
            action=self.action, tries=self.tries, total=total_seconds_waiting,
        )
        return msg

    def __call__(self):
        self.counter += 1
        if self.counter == 1:
            return True
        if self.counter > self.tries:
            error_msg = self._make_error_msg()
            if self._raise:
                raise MaxWhileTries(error_msg)
            else:
                log.warning(error_msg)
                return False
        self.sleeper(self.sleep_current)
        self.sleep_current += self.increment
        return True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False
