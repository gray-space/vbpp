__author__ = 'ggray'


class Switch(object):
    """A switch class that makes of for the fact that Python stubbornly refuses to implement a switch
       statement. More than one way to skin a python...
    """
       # Following is from http://code.activestate.com/recipes/410692/ to compensate
       # for Python's obstinant attitude about Switch/case statements

        # This class provides the functionality we want. You only need to look at
        # this if you want to know how this works. It only needs to be defined
        # once, no need to muck around with its internals.

        # Use it like this:
        #for case in Switch(c):
        #    if case('a'): pass # only necessary if the rest of the suite is empty
        #    if case('b'): pass
        #    # ...
        #    if case('y'): pass
        #    if case('z'):
        #        print "c is lowercase!"
        #        break
        #    if case('A'): pass
        #    # ...
        #    if case('Z'):
        #        print "c is uppercase!"
        #        break
        #    if case(): # default
        #        print "I dunno what c was!"

    def __init__(self, value):
        """
        Provides a Switch statement
        :param object :
        """
        self.value = value
        self.fall = False

    def __iter__(self):
        """Return the match method once, then stop"""
        yield self.match
        raise StopIteration

    def match(self, *args):
        """Indicate whether or not to enter a case suite"""
        if self.fall or not args:
            return True
        elif self.value in args:  # changed for v1.5, see below
            self.fall = True
            return True
        else:
            return False