"""Contains miscellaneous functions for e.g. triggers"""

def number_between(start, end):
    def f(msg, storage):
        try:
            num = int(msg)
            return num >= start and num <= end
        except:
            return False
    return f
