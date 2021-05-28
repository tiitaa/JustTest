#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os, sys
try:
    # python3
    from functools import reduce
except ImportError:
    pass

class travdir:
    def __init__(self, base=os.path.curdir, deep=-1):
        self.base = base
        if type(base) is str:
            self.base = [base]
        self.deep = deep

        # python2
        self.next = self.__next__

    def __iter__(self):
        self.d = [ self.base ]         # dirs list
        self.i = [ iter(self.d[-1]) ]  # traversal iter
        self.p = ''                    # parent dir str
        self.pl = list()               # parent dirs list
        return self

    def __next__(self):
        try:
            n = next(self.i[-1])
            i = os.path.join(self.p, n)
            if os.path.isdir(i) and (self.deep < 1 or len(self.i) <= self.deep):
                try:
                    self.d.append(os.listdir(i))
                    self.i.append(iter(self.d[-1]))
                    self.pl.append(n)
                    self.p = self.pstr()
                except BaseException as err:
                    sys.stderr.write('{}: {}\n'.format(err.strerror, i))
            return i
        except StopIteration:
            if len(self.i) < 2:
                raise StopIteration
            self.d.pop()
            self.i.pop()
            self.pl.pop()
            self.p = self.pstr()
            return next(self)

    def pstr(self):
        if len(self.pl) == 0:
            return ''
        return reduce(os.path.join, self.pl)


if __name__ == '__main__':
    for i in travdir(['c:\\', 'd:\\', 'e:\\'], 2):
        print(i)

