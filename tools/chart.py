#!/usr/bin/env python
#-*- coding: utf-8 -*-


import numpy as np
import matplotlib
matplotlib.use('GTK')
import matplotlib.pyplot as plt

import random

def value2desc(x):
    return x

def chart(data, filename):
    def none2zero(seq):
        return [0.0 if i is None else i for i in seq]
    
    maxval = max([max(i[1:]) for i in data[1:]])
    
    colors = {
        'postgresql': '#0094bb',
        'mysql':      '#e97b00',
        'sqlite':     '#80a796',
        'oracle':     '#f00000',
        'db2':        '#167018',
        'sqlserver':  '#000000',
    }
    
    N = len(data[0]) - 1
    
    ind = np.arange(N)
    width = 1.0 / N

    plt.subplot(111)
    
    rects = []
    for i, fordb in enumerate(data[1:]):
        rects.append(plt.bar(ind + width * i, none2zero(fordb[1:]), width, color=colors[fordb[0]]))


    plt.ylabel(u'Przepustowość (zapytań/s) \u00a0', clip_on=True)
    plt.xticks(ind + (width * N / 2), [value2desc(i) for i in data[0][1:]], fontsize=10)
    plt.ylim(ymax=maxval * 1.45)
    
    leg = plt.legend( [i[0] for i in rects], [value2desc(i[0]) for i in data[1:]], shadow=True, pad = 0.08)
    #borderpad=0, numpoints=2, 
    # matplotlib.text.Text instances
    for t in leg.get_texts():
        t.set_fontsize('small')    # the legend text fontsize
    
    # matplotlib.lines.Line2D instances
    for l in leg.get_lines():
        l.set_linewidth(1.5)
    
    #plt.show()
    plt.savefig(filename, dpi=150)
    plt.close()

      
if __name__ == '__main__':
    def rand_list(n, mul=1.0):
        return [random.random() * mul for i in xrange(n)]

    data = [
        [None,         'create', 'insert', 'roots', 'parent', 'children', 'ancestors', 'descendants'],
        ['postgresql', ] + rand_list(7, 2),
        ['mysql',      ] + rand_list(7, 2),
        ['sqlite',     ] + rand_list(7, 2),
        ['oracle',     ] + rand_list(7, 2),
        ['db2',        ] + rand_list(7, 2),
        ['sqlserver',  ] + rand_list(7, 2),
    ]
    
    chart(data, 'wykres.png')
