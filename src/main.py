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
        print '#', name
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


def run_test(database, tree_class, testcases):
    def report_null(data):
        pass
    def report_print(data):
        print data
    report = report_null
    #report = report_print
    
    print '## database', database, tree_class.__name__
    
    if database in ('memory', 'mem'):
        tree = methods.Memory()
    else:
        db = pada.connect(file='config/%s.cfg' % database)
        db.set_paramstyle('named')
        tree = tree_class(db)
    
    id2id = {}
    
    sw = Stopwatch([tree_class.tree_name, database, testcases['data']])
    
    sw.start('create')
    tree.create_table()
    

    sw.start('insert')
    for i, node in enumerate(testcases.get('insert', [])):
        id2id[node['id']] = tree.insert(parent=node['parent'], name=node['name'][:48])
        if i % 10000 == 0:
            print '#', i
    db.commit()
    
    
    
    #print repr(testcases)
    case = int(testcases.get('roots', ['1'])[0])
    sw.start('roots')
    for i in xrange(case):
        report(tree.get_roots())
    
    case = testcases.get('parent', [])
    sw.start('parent')
    for idn in case:
        report(tree.get_parent(id2id[idn]))
    
    case = testcases.get('children', [])
    sw.start('children')
    for idn in case:
        report(tree.get_children(id2id[idn]))
    
    case = testcases.get('ancestors', [])
    sw.start('ancestors')
    for idn in case:
        report(tree.get_ancestors(id2id[idn]))
    
    case = testcases.get('descendants', [])
    sw.start('descendants')
    for idn in case:
        report(tree.get_descendants(id2id[idn]))
    
    sw.stop()
    
    return sw


def find_methods():
    bases = {'postgresql': {}, 'mysql': {}, 'sqlite': {}, 'oracle': {}, 'db2': {}, 'sqlserver': {}, 'memory': {}}
    
    for name in dir(methods):
        obj = getattr(methods, name)
        if hasattr(obj, 'tree_name'):
            tree_name = getattr(obj, 'tree_name')
            tree_base = getattr(obj, 'tree_base', ['postgresql', 'mysql', 'sqlite', 'oracle', 'db2', 'sqlserver'])
            
            for i in (tree_base + ['memory']):
                bases[i][tree_name] = obj
    
    return bases

def main():
    args = sys.argv[1:]
    
    if args[0] == 'test':
        bases = find_methods()
        database = args[1]
        testcases = utils.read_tree('data/%s.xml' % args[2])
        testcases['data'] = args[2]
        if len(args) == 4:
            print run_test(database, bases[database][args[3]], testcases)
        else:
            for i in bases[database]:
                print run_test(database, bases[database][i], testcases)
    
    elif args[0] == 'generate':
        utils.generate_test('data/%s.xml' % args[1], int(args[2]), int(args[3]))
        
    elif args[0] == 'check':
        utils.generate_test('data/%s.xml' % args[1], int(args[2]), int(args[3]))
    
    elif args[0] == 'sql':
        database, sql = args[1], args[2]
        
        db = pada.connect(file='config/%s.cfg' % database)
        db.execute(sql)
        print db.format_ascii()

if __name__ == '__main__':
    main()

