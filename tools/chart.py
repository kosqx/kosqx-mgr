#!/usr/bin/env python
#-*- coding: utf-8 -*-


import numpy as np
import matplotlib
matplotlib.use('Gdk')
#matplotlib.use('cairo')
import matplotlib.pyplot as plt

import random

def value2desc(x, *kw):
    return x

def chart(data, filename, value2desc=value2desc):
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
        
        'simple':     '#010202',
        'nested':     '#ee2e2f',
        'pathenum':   '#008c48',
        'full':       '#185aa9',
        'with':       '#f47d23',
        'connectby':  '#662c91',
        'ltree':      '#a21d21',
        'hierarchyid':'#b43894',
    }
    
    N = len(data[0]) - 1
    M = len(data) - 1
    
    ind = np.arange(N)
    width = 1.0 / N
    bwidth = 1.0 / (M + 1)
    
    #print '==' * 200, N, M

    
    plt.gca().yaxis.grid(True)
    plt.gca().xaxis.grid(False)
    plt.subplots_adjust(left=0.06, bottom=0.04, right=0.99, top=0.99)
    plt.subplot(111)

    
    rects = []
    for i, fordb in enumerate(data[1:]):
        rects.append(plt.bar(ind + bwidth * i + (bwidth/2), none2zero(fordb[1:]), bwidth, color=colors[fordb[0]]))
    
    
    plt.ylabel(u'Przepustowość [zapytań/ms].', size=16)
    #plt.ylabel(u'Czas (s).', size=16)
    plt.xticks(ind + (width * N / 2), [value2desc(i) for i in data[0][1:]], fontsize=16)
    plt.ylim(ymax=maxval * (1.06 + 0.075 * M))
    
    leg = plt.legend([i[0] for i in rects], [value2desc(i[0]) for i in data[1:]], shadow=True, borderpad=0.3)

    #for t in leg.get_texts():
        #t.set_fontsize('small') 
    
    #for l in leg.get_lines():
        #l.set_linewidth(1.5)
    
    show_data = False
    if show_data:
        for rect in rects:
            for r in rect:
                height = r.get_height()
                plt.text(r.get_x() + r.get_width() * 0.6, height + 0.02 * maxval, '%.2f\r' % height, 
                        ha='center', va='bottom', rotation='vertical', size=14, lod=True
                )
    
    plt.savefig(filename, dpi=150)
    plt.close()


if __name__ == '__main__':
    def rand_list(n, mul=1.0):
        return [random.random() * mul + 4 for i in xrange(n)]

    data = [
        [None,         'create', 'insert', 'roots', 'parent', 'children', 'ancestors', 'descendants'],
        ['postgresql', ] + rand_list(7, 20),
        ['mysql',      ] + rand_list(7, 20),
        ['sqlite',     ] + rand_list(7, 20),
        ['oracle',     ] + rand_list(7, 20),
        ['db2',        ] + rand_list(7, 20),
        ['sqlserver',  ] + rand_list(7, 20),
    ]
    
    chart(data, 'wykres.png')
