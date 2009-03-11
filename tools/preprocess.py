#!/usr/bin/env python
#-*- coding: utf-8 -*-

import sys
import re
import os
import os.path
import glob
import tempfile
import shutil


from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import LatexFormatter

import numpy as np
import matplotlib
matplotlib.use('GTK')
import matplotlib.pyplot as plt

#--------------------------------------------------------------------
# Util functions

def write_file(path, data):
    def makepath(path):
        from os import makedirs
        from os.path import normpath,dirname,exists,abspath
    
        dpath = normpath(dirname(path))
        if not exists(dpath):
            makedirs(dpath)
        return normpath(abspath(path))

    fout = open(makepath(path), 'w')
    fout.write(data)
    fout.close()


def value2desc(value, none=' --- '):
    names = {
        'postgresql': 'PostgreSQL',
        'mysql':      'MySQL',
        'sqlite':     'SQLite',
        'oracle':     'Oracle',
        'db2':        'IBM DB2',
        'sqlserver':  'SQL Server',
        
        'create':      'Utworzenie',
        'insert':      'Wstawianie',
        'roots':       'Korzenie',
        'parent':      'Rodzic',
        'children':    'Dzieci',
        'ancestors':   'Przodkowie',
        'descendants': 'Potomkowie',
    }
    if value is None:
        return none
    elif value in names:
        return names[value]
    elif isinstance(value, (int, float)):
        return ('$%.2f$' % float(value)).replace('.', ',')
    else:
        return value


def read_results(filename):
    result = {}
    
    fin = open(filename)
    for line in fin:
        if line.startswith('#') or line.strip() == '':
            continue
        
        parts = line.split()
        name = tuple(parts[0].split(':'))
        value = float(parts[1])
        
        result[name] = value
        
    return result


def process_results(results, method, testdata):
    operation_order = ['create', 'insert', 'roots', 'parent', 'children', 'ancestors', 'descendants']
    database_order = ['postgresql', 'mysql', 'sqlite', 'oracle', 'db2', 'sqlserver']
    
    final = [[''] + operation_order]
    
    for db in database_order:
        line = [db]
        for op in operation_order:
            line.append(results.get((method, db, testdata, op), None))
        final.append(line)
    
    return final


#--------------------------------------------------------------------
# Chart create

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


#--------------------------------------------------------------------
# Functions inserting data to tex

def code_pre(lines):
    code = ''.join(lines[1:])

    lexer = get_lexer_by_name("sql", stripall=True)
    formatter = LatexFormatter(linenos=True, commandprefix='PYG')
    
    result = highlight(code, lexer, formatter)
    
    lines = result.splitlines()
    if len(lines[-2].strip()) == 0:
        lines[-2:-1] =  []
    return (u'\n'.join(lines)).encode('utf-8')


def code_pre_style(line):
    return LatexFormatter(commandprefix='PYG').get_style_defs().encode('utf-8')


def code_results_table(line):
    global results
    
    parts = line.split()
    method = parts[-2]
    testdata = parts[-1]
    
    operation_order = ['create', 'insert', 'roots', 'parent', 'children', 'ancestors', 'descendants']
    database_order = ['postgresql', 'mysql', 'sqlite', 'oracle', 'db2', 'sqlserver']
    
    
    lines = [
        '\\begin{tabular}{| r | ' + ('r ' * len(operation_order)) + '  |}',
        '\\hline',
        ' & ' + ' & '.join(['\\begin{sideways}' + value2desc(i) + '\\end{sideways}' for i in operation_order]) + r'\\',
        '\\hline',
    ]
    
    ' & '.join([value2desc(i) for i in [''] + database_order]) + r'\\'
    
    for db in database_order:
        line = []
        line.append(value2desc(db))
        for op in operation_order:
            line.append(value2desc(results.get((method, db, testdata, op), None)))
        lines.append(' & '.join(line) + r' \\')
        
    lines.extend([
        '\\hline',
        '\\end{tabular}',
    ])
    
    return '\n'.join(lines)


def code_results_chart(line):
    global results
    
    parts = line.split()
    method = parts[-2]
    testdata = parts[-1]
    data = process_results(results, method, testdata)
    
    print data
    
    filename = 'img_chart_%s.png' % method
    chart(data, filename)
    
    return r'\includegraphics[width=\textwidth]{%s}' % filename


#--------------------------------------------------------------------
# Main functions

def process_tex(infile, outfile, rules):
    result = []
    fin = open(infile)
    
    block_in = False
    block_regexp = ''
    block_data = []
    block_code = None
    
    for line in fin:
        if block_in:
            if block_regexp.match(line):
                tmp = block_code(block_data)
                result.append(tmp)
                block_in = False
            else:
                block_data.append(line)
            continue
        for rule in rules:
            if rule[0].match(line):
                if rule[1] is None:
                    tmp = rule[2](line)
                    result.append(tmp)
                else:
                    block_in = True
                    block_regexp = rule[1]
                    block_code = rule[2]
                    block_data = [line]
                break
        else:
            result.append(line)
    
    fin.close()
    
    write_file(outfile, ''.join(result))


def process_files(files, abspath, rules_in):
    def to_regexp(s):
        if s is None:
            return None
        else:
            return re.compile(s)
    
    rules = [(to_regexp(i[0]), to_regexp(i[1]), i[2]) for i in rules_in]
    
    for tex in files:
        print 'file:', tex
        infile = os.path.join(abspath, tex)
        process_tex(infile, tex, rules)


def main(args):
    global results
    results = read_results('../src/results.txt')
    
    tmpdir = tempfile.mkdtemp()
    abspath = os.path.abspath(args[0])
    
    os.chdir(abspath)
    
    shutil.copyfile('Makefile', os.path.join(tmpdir, 'Makefile'))
    files = glob.glob('*.tex') + glob.glob('tex/*.tex')
 
    os.chdir(tmpdir)
    
    process_files(files, abspath, [
        (r'\\begin\{verbatim\}\[sql\]', r'\\end\{verbatim\}', code_pre),
        (r'^%! *pygments-style',        None,                 code_pre_style),
        (r'^%! *result-table',          None,                 code_results_table),
        (r'^%! *result-chart',          None,                 code_results_chart),
    ])
    
    os.system('make pdf')
    result_pdf = glob.glob('*.pdf')[0]
    os.chdir(abspath)
    os.system('pwd')
    shutil.copyfile(os.path.join(tmpdir, result_pdf), result_pdf)

#--------------------------------------------------------------------
# Start point

if __name__ == '__main__':
    main(sys.argv[1:])
