#!/usr/bin/env python
#-*- coding: utf-8 -*-

import re

def code_strip(data):
    lines = list(data)
    lines[0] = lines[0].split('"""', 1)[1]
    lines[-1] = lines[-1].rsplit('"""', 1)[0]
    
    lines = [i.rstrip() for i in lines]
    
    while lines[0] == '':
        lines = lines[1:]
    
    while lines[-1] == '':
        lines = lines[:-1]
        
    spaces = [len(i) - len(i.lstrip()) for i in lines]
    cut = min(spaces)
    lines = [i[(cut + s) / 2:] for i, s in zip(lines, spaces)]
    
    return '\n'.join(lines)
    

def parse_methods(filename):
    method = ''
    operation = ''
    data = []
    result = {}
    
    fin = open(filename)
    
    method_re = re.compile(r"^\s+tree_name\s*=\s*'(.*)'\s*$")
    operation_re = re.compile(r'^\s+def\s+([a-zA-Z0-9_]+)\(.*\):\s*$')
    
    
    for line in fin:
        me = method_re.match(line)
        if me:
            method = me.groups()[0]
        
        op = operation_re.match(line)
        if op:
            operation = op.groups()[0]
            if operation.startswith('get_'):
                operation = operation[4:]
            if operation == 'create_table':
                operation = 'create'
        
        if data:
            data.append(line)
            if '"""' in line:
                key = '%s.%s' % (method, operation)
                result[key] = result.get(key, []) + [code_strip(data)]
                data = []
        else:
            if '"""' in line and len(data) == 0:
                data.append(line)

        # tree_name = 'simple'
    
    
    fin.close()
    
    return result

if __name__ == '__main__':
    result = parse_methods('/home/kosqx/workspace/kosqx-mgr/src/methods.py')
    for i in sorted(result.keys()):
        print '-'*40, i
        print '\n\n'.join(result[i])
