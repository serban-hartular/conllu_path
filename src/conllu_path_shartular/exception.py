
class ConlluException(Exception):
    def __init__(self, source: str, what : str, line_nr : int = None):
        self.source = source
        self.what = what
        self.line_nr = line_nr
    def __str__(self):
        return ('' if self.line_nr is None else 'line %d:' % self.line_nr) +\
            self.what + ' in ' + '"%s"' % self.source


    def __repr__(self):
        return str(self)