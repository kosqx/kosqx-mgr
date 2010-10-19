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
        self._count = 0
    
    def start(self, name, count=0):
        print '#', name, count
        self.stop()
        self._name = '%s:%s' % (self._prefix, name)
        self._time = time.time()
        self._count = count
        
    def _throughput(self, time, count):
        #print count, time
        if time > 0:
            return count / time
        else:
            return 0
    
    def stop(self):
        if self._time is not None:
            self._results.append((self._name, self._throughput(time.time() - self._time, self._count)))
        
    def lines(self):
        total = sum([t for n, t in self._results])
        self._results.append(('%s:total' % self._prefix, total))
        size = max([len(n) for n, t in self._results])
        return ['%s %5.3f' % (n.ljust(size), t)  for n, t  in self._results]
        
    def __str__(self):
        return '\n'.join(self.lines())


#def get_tree(database, tree_class):
#    if database in ('memory', 'mem'):
#        tree = methods.Memory()
#    else:
#
#    
#    return tree

def run_test(database, tree_class, testcases):
    def report_null(data):
        pass
    def report_print(data):
        if isinstance(data, list):
            for i in data:
                print repr(i)
        else:
            print repr(data)
    report = report_null
    #report = report_print
    
    print '## database', database, tree_class.__name__
    
    db = pada.connect(file='config/%s.cfg' % database)
    db.set_paramstyle('named')
    tree = tree_class(db)
    
    #tree = get_tree(database, tree_class)
    
    id2id = {}
    
    sw = Stopwatch([tree_class.tree_name, database, testcases['data']])
    
    sw.start('create', 1)
    tree.create_table()
    
    case = testcases.get('insert', [])
    sw.start('insert', len(case))
    for i, node in enumerate(case):
        #id2id[node['id']] = tree.insert(parent=node['parent'], name=node['name'][:99])
        id2id[node['id']] = tree.insert(
            parent=id2id.get(node['parent'], None),
            name=node['name'][:99]
        )
        
        if i % 1000 == 0:
            print '#', i
    db.commit()
    
    #print repr(testcases)
    case = int(testcases.get('roots', ['1'])[0])
    sw.start('roots', case)
    for i in xrange(case):
        report(tree.get_roots())
    
    case = testcases.get('parent', [])
    sw.start('parent', len(case))
    for i, idn in enumerate(case):
        report(tree.get_parent(id2id[idn]))
        if i % 1000 == 0:
            print '#', i
    
    case = testcases.get('children', [])
    sw.start('children', len(case))
    for i, idn in enumerate(case):
        report(tree.get_children(id2id[idn]))
        if i % 1000 == 0:
            print '#', i
    
    case = testcases.get('ancestors', [])
    sw.start('ancestors', len(case))
    for i, idn in enumerate(case):
        report(tree.get_ancestors(id2id[idn]))
        if i % 1000 == 0:
            print '#', i
    
    case = testcases.get('descendants', [])
    sw.start('descendants', len(case))
    for i, idn in enumerate(case):
        report(tree.get_descendants(id2id[idn]))
        if i % 1000 == 0:
            print '#', i
    
    sw.stop()
    
    return sw


def run_checkgen(testcases):
    def report_null(data):
        pass
    def report_print(data):
        if isinstance(data, list):
            for i in data:
                print repr(i)
        else:
            print repr(data)
    report = report_null
    #report = report_print
    
    tree = methods.Memory()
    
    id2id = {}
    
    sw = Stopwatch([])
    
    sw.start('create')
    tree.create_table()
    

    case = testcases.get('insert', [])
    sw.start('insert')
    for i, node in enumerate(testcases.get('insert', [])):
        id2id[node['id']] = tree.insert(parent=node['parent'], name=node['name'][:48])
        if i % 10000 == 0:
            print '#', i
    #db.commit()
    
    
    
    #print repr(testcases)
    case = int(testcases.get('roots', ['100'])[0])
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
    
    #sw.stop()
    
    #return sw


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
        #python main.py test postgresql example nested
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
        
    elif args[0] == 'checkgen':
        testcases = utils.read_tree('data/%s.xml' % args[1])
        run_checkgen(testcases)
        #utils.generate_test('data/%s.xml' % args[1], int(args[2]), int(args[3]))
    
    elif args[0] == 'sql':
        database, sql = args[1], args[2]
        
        db = pada.connect(file='config/%s.cfg' % database)
        db.execute(sql)
        print db.format_ascii()

if __name__ == '__main__':
    main()

