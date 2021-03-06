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


from chart import chart
from methods_sql import parse_methods
from sql_lexer import SqlLexer
from graph import dot2png, txt2dot

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
        
        'simple':      'Metoda krawędziowa',
        'nested':      'Metoda zagnieżdżonych zbiorów',
        'pathenum':    'Metoda zmaterializowanych ścieżek',
        'full':        'Metoda pełnych ścieżek',
        'with':        'Wspólne Wyrażenia Tabelowe',
        'connectby':   'CONNECT BY',
        'ltree':       'PostgreSQL ltree',
        'hierarchyid': 'SQL Server hierarchyid',
        
    }
    if value is None:
        return none
    elif value in names:
        return names[value]
    elif isinstance(value, (int, float)):
        return ('$%.3f$' % float(value)).replace('.', ',')
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
        
        if name[-1] != 'total':
            ## FIXME
            result[name] = value / 1000.0
        
    return result


def process_results(results, method, testdata):
    operation_order = ['create', 'insert', 'roots', 'parent', 'children', 'ancestors', 'descendants']
    database_order = ['postgresql', 'mysql', 'sqlite', 'oracle', 'db2', 'sqlserver']
    
    final = [[''] + operation_order]
    
    for db in database_order:
        line = [db]
        isok = False
        for op in operation_order:
            val = results.get((method, db, testdata, op), None)
            isok = isok or (val is not None)
            line.append(val)
        if isok:
            final.append(line)
    
    return final


def do_highlight(code, lexer_name):
    if lexer_name == 'sql':
        lexer = SqlLexer()
    else:
        lexer = get_lexer_by_name(lexer_name, stripall=True)
    
    #formatter = LatexFormatter(linenos=False, commandprefix='PYG', verboptions='frame=single,xleftmargin=5mm')
    #formatter = LatexFormatter(linenos=False, commandprefix='PYG', verboptions='frame=lines,xleftmargin=5mm')
    #formatter = LatexFormatter(linenos=False, commandprefix='PYG', verboptions='frame=leftline,xleftmargin=5mm')
    formatter = LatexFormatter(linenos=True, commandprefix='PYG', verboptions='xleftmargin=9mm')
    
    result = highlight(code, lexer, formatter)
    
    lines = result.splitlines()
    if len(lines[-2].strip()) == 0:
        lines[-2:-1] =  []
    return (u'\n'.join(lines)).encode('utf-8')

#--------------------------------------------------------------------
# Functions inserting data to tex



def code_pre(lines):
    code = ''.join(lines[1:])

    head = lines[0].strip()
    
    if head.endswith('[python]'):
        lexer_name = "python"
    elif head.endswith('[c]'):
        lexer_name = "c"
    elif head.endswith('[xml]'):
        lexer_name = "xml"
    else:
        lexer_name = "sql"
        
    return do_highlight(code, lexer_name)

    #if lines[0].endswith('[python]'):
        #lexer = get_lexer_by_name("python", stripall=True)
    #else:
        #lexer = get_lexer_by_name("sql", stripall=True)
    
    ##formatter = LatexFormatter(linenos=False, commandprefix='PYG', verboptions='frame=single,xleftmargin=5mm')
    #formatter = LatexFormatter(linenos=False, commandprefix='PYG', verboptions='frame=lines,xleftmargin=5mm')
    
    #result = highlight(code, lexer, formatter)
    
    #lines = result.splitlines()
    #if len(lines[-2].strip()) == 0:
        #lines[-2:-1] =  []
    #return (u'\n'.join(lines)).encode('utf-8')


def code_pre_style(line):
    return LatexFormatter(commandprefix='PYG').get_style_defs().encode('utf-8')

def code_method_sql(line):
    global methods

    name = line.split()[-1]
    if name in methods:
        code = ';\n\n'.join(methods[name])
        return do_highlight(code, 'sql')
    else:
        return "\n\n\\textcolor{red}{\\textbf{[[tu brakuje kodu źródłowego]]}}\n\n"
    
def code_method_python(line):
    global methods

    name = line.split()[-1]
    if name in methods:
        code = '\n\n'.join(methods[name])
        return do_highlight(code, 'python')
    else:
        return "\n\n\\textcolor{red}{\\textbf{[[tu brakuje kodu źródłowego: Python]]}}\n\n"

def do_code_results(line):
    global results
    global config
    
    parts = line.split()
    method = parts[-1]
    testdata = config['testdata']
    
    final = process_results(results, method, testdata)
    
    return final, method, testdata


def gen_results_table(final):
    lines = [
        '\\begin{tabular}{| r | ' + ('r ' * (len(final[0]) - 1)) + '  |}',
        '\\hline',
        ' & ' + ' & '.join(['\\begin{sideways}' + value2desc(i) + '\\end{sideways}' for i in final[0][1:]]) + r'\\',
        '\\hline',
    ]
    
    for db_line in final[1:]:
        line = []
        for op in db_line:
            line.append(value2desc(op))
        lines.append(' & '.join(line) + r' \\')
        
    lines.extend([
        '\\hline',
        '\\end{tabular}',
    ])
    
    return '\n'.join(lines)

def code_results_table(line):
    final, method, testdata = do_code_results(line)
    return gen_results_table(final)
    
def code_results_chart(line):
    #global results
    #
    ##parts = line.split()
    ##method = parts[-2]
    ##testdata = parts[-1]
    #
    #data = process_results(results, method, testdata)
    
    final, method, testdata = do_code_results(line)
    
    #print data
    
    filename = 'img_chart_%s.png' % method
    chart(final, filename, value2desc)
    return r'\includegraphics[totalheight=0.4\textheight]{%s}' % filename
    #return r'\includegraphics[width=\textwidth]{%s}' % filename
    


def code_results_testdata(line):
    global config
    
    parts = line.split()
    config['testdata'] = parts[-1]
    
    return ''



def gen_summary():
    global results
    global config
    
    import random
    
    testdata = config['testdata']
    
    summary = {}
    for (method, db, data, op) in results:
        if data == testdata:
            summary[(method, op)] = summary.get((method, op), []) + [results[(method, db, data, op)]]
    
    
    #final = process_results(results, method, testdata)
    def rand_list(n, mul=1.0):
        return [random.random() * mul + 4 for i in xrange(n)]

    def do_list(method):
        grp = ['create', 'insert', 'roots', 'parent', 'children', 'ancestors', 'descendants']
        avg = lambda x: sum(x)/len(x)
        return [avg(summary[(method, i)]) for i in grp]
    
    
    final = [
        [None,         'create', 'insert', 'roots', 'parent', 'children', 'ancestors', 'descendants'],
    ]
    for i in ['simple', 'nested', 'pathenum', 'full', 'with', 'connectby', 'ltree', 'hierarchyid']:
        final.append([i] + do_list(i))
        
    return final

def code_summary_table(line):
    final = gen_summary()
    return gen_results_table(final)

def code_summary_chart(line):
    final = gen_summary()
    
    
    filename = 'img_chart_summary.png'
    chart(final, filename, value2desc)
    return r'\includegraphics[totalheight=0.4\textheight]{%s}' % filename
    #return r'\includegraphics[width=\textwidth]{%s}' % filename

def code_dot(lines):
    filename = 'img_graph_%s.png' % lines[0].split()[-1]
    dot2png('\n'.join(lines[1:]), filename)
    #return r'\includegraphics[width=0.8\textwidth]{%s}' % filename
    return '{%s}' % filename

def code_table(lines):
    filename = 'img_graph_%s.png' % lines[0].split()[-1]
    dot2png(txt2dot(lines[1:]), filename)
    return r'\includegraphics[width=0.8\textwidth]{%s}' % filename

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
    global methods
    methods = parse_methods('../src/methods.py')
    global config
    config = {}
    
    
    for i in results:
        if results[i] > 10000.:
            print i, results[i]
    
    tmpdir = tempfile.mkdtemp()
    abspath = os.path.abspath(args[0])
    
    os.chdir(abspath)
    
    shutil.copyfile('Makefile', os.path.join(tmpdir, 'Makefile'))
    files = glob.glob('*.tex') + sorted(glob.glob('tex/*.tex')) + glob.glob('tex/*.bib')
 
    os.chdir(tmpdir)
    
    process_files(files, abspath, [
        #(r'\\begin\{verbatim\}\[sql]\s*',   r'\\end\{verbatim\}', code_pre),
        #(r'\\begin\{verbatim\}\[sql]\s*',   r'\\end\{verbatim\}', code_pre),
        #(r'\\begin\{verbatim\}\[(?:sql|c|python|pythonsql)]\s*',   r'\\end\{verbatim\}', code_pre),
        (r'\\begin\{verbatim\}\[sql]\s*',     r'\\end\{verbatim\}', code_pre),
        (r'\\begin\{verbatim\}\[c]\s*',       r'\\end\{verbatim\}', code_pre),
        (r'\\begin\{verbatim\}\[python]\s*',  r'\\end\{verbatim\}', code_pre),
        (r'\\begin\{verbatim\}\[xml]\s*',     r'\\end\{verbatim\}', code_pre),
        (r'\\begin\{verbatim\}\[dot]\s*',     r'\\end\{verbatim\}', code_dot),
        (r'\\begin\{verbatim\}\[table]\s*',   r'\\end\{verbatim\}', code_table),
        (r'^%! *pygments-style',            None,                 code_pre_style),
        (r'^%! *method-sql',                None,                 code_method_sql),
        (r'^%! *method-python',             None,                 code_method_python),
        (r'^%! *result-table',              None,                 code_results_table),
        (r'^%! *result-chart',              None,                 code_results_chart),
        (r'^%! *result-testdata',           None,                 code_results_testdata),
        
        (r'^%! *summary-chart',             None,                 code_summary_chart),
        (r'^%! *summary-table',             None,                 code_summary_table),
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

