#!/usr/bin/env python
# -*- coding: utf-8 -*-

def processbar(percent, stage=0):
    edge = chr(9474)
    #pl = range(9601, 9609)
    pl = range(9615, 9607, -1)

    num = int(min(1, abs(percent)) * 200)
    s0 = num // len(pl)
    s1 = num % len(pl)
    m = 200 // len(pl)
    ss0 = chr(pl[-1]) * s0
    ss1 = chr(pl[s1 - 1]) if s1 > 0 else ''
    ss2 = ' ' * (25 - s0) if s1 == 0 else ' ' * (m - 1 - s0)
    return ''.join([edge, ss0, ss1, ss2, edge])

if __name__ == '__main__':
    import time

    l = 300
    print('')
    for i in range(l+1):
        time.sleep(0.05)
        print('\r {} {}'.format(processbar(i / l), i), end='')

    print('')

