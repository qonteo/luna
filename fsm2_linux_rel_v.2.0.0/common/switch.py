class switch(object):
    """
    Python switch implementation.
    """
    def __init__(self, value):
        self.value = value
        self.fall = False

    def __iter__(self):
        """
        Yield one self.match and finish.
        """
        yield self.match
        raise StopIteration

    def match(self, *args):
        """
        Realise the only success match.
        """
        if self.fall or not args:
            # for last case
            return True
        elif self.value in args:
            self.fall = True
            # for suitable case
            return True
        # for other cases
        return False
