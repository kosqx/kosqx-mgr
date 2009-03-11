#!/usr/bin/env python
#-*- coding: utf-8 -*-

import sys
import time

import pada


import methods
import utils

class Stopwatch():
    def __init__(self, prefix=''):
        self._results = []
        self._prefix = ':'.join(prefix)
        self._time = None
        self._name = ''
    
    def start(self, name):
        self.stop()
        self._name = '%s:%s' % (self._prefix, name)
        self._time = time.time()
        
    def stop(self):
        if self._time is not None:
            self._results.append((self._name, time.time() - self._time))
        
    def lines(self):
        total = sum([t for n, t in self._results])
        self._results.append(('%s:total' % self._prefix, total))
        size = max([len(n) for n, t in self._results])
        return ['%s %5.3f' % (n.ljust(size), t)  for n, t  in self._results]
        
    def __str__(self):
        return '\n'.join(self.lines())


def run_test(database, tree_class, data):
    db = pada.connect(file='config/%s.cfg' % database)
    db.set_paramstyle('format')
    tree = tree_class(db)
    
    sw = Stopwatch([tree_class.tree_name, database, data])
    
    sw.start('create')
    tree.create_table()
    
    sw.start('insert')    
    testcases = utils.read_tree('data/%s.xml' % data, tree.insert)
    db.commit()
    
    sw.start('roots')
    tree.get_roots()
    
    sw.start('parent')
    for idn in testcases.get('parent', []):
        tree.get_parent(idn)
    
    sw.start('children')
    for idn in testcases.get('children', []):
        tree.get_children(idn)
    
    sw.start('ancestors')
    for idn in testcases.get('ancestors', []):
        tree.get_ancestors(idn)
    
    sw.start('descendants')
    for idn in testcases.get('descendants', []):
        tree.get_descendants(idn)
    
    sw.stop()
    
    return sw


def find_methods():
    bases = {'postgresql': {}, 'mysql': {}, 'sqlite': {}, 'oracle': {}, 'db2': {}, 'sqlserver': {}}
    
    for name in dir(methods):
        obj = getattr(methods, name)
        if hasattr(obj, 'tree_name'):
            tree_name = getattr(obj, 'tree_name')
            tree_base = getattr(obj, 'tree_base', ['postgresql', 'mysql', 'sqlite', 'oracle', 'db2', 'sqlserver'])
            
            for i in tree_base:
                bases[i][tree_name] = obj
    
    return bases

def main():
    args = sys.argv[1:]
    
    if args[0] == 'test':
        bases = find_methods()
        database = args[1]
        for i in bases[database]:
            print run_test(database, bases[database][i], args[2])
    
    elif args[0] == 'generate':
        utils.generate_test('data/%s.xml' % args[1], int(args[2]), int(args[3]))

if __name__ == '__main__':
    main()

