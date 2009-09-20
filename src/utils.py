#!/usr/bin/env python
#-*- coding: utf-8 -*-

import random


from xml.sax.saxutils import escape, quoteattr

class WellFormedError(Exception):
    """ Exception WellFormedError
    """
    pass


class XmlWriter(object):
    """ Simple class usefull for writing well-formated XML 
        TODO: processing instuctions (<? ?>), comments (<!-- -->), DTD (?)
    """

    def __init__(self, afile, indent='  '):
        self._file = afile
        self._indent = indent
        self._stack = []

    def prolog(self, version='1.0', encoding='UTF-8', standalone=''):
        """ Write prolog into document
            TODO: test if this is just beginning of document
        """

        if standalone == '':
            result = '<?xml version="%s" encoding="%s"?>\n' % (
                    version, encoding)
        else:
            result = '<?ml version="%s" encoding="%s" standalone="%s"?>\n' % (
                    version, encoding, standalone)
        self._file.write(result)

    def start_element(self, name, attributes={}, close=False, order=None):
        """ Write beggining of tag with optional atributes
        """
        
        if order is None:
            keyorder = attributes
        else:
            keyorder = list(order) + [k for k in attributes if k not in order]
        
        attr = ['%s=%s' % (key, quoteattr(str(attributes[key]))) 
                for key in keyorder if attributes[key] != None]
        indent = self._make_indent()
        if close:
            end = '/>\n'
        else:
            end = '>\n'
            self._stack.append(name)
        
        space = ['', ' '][bool(attr)]
        
        self._file.write(indent + '<' + name + space + ' '.join(attr) + end)

    def end_element(self):
        """ Write end of tag
        """

        if len(self._stack) == 0:
            raise WellFormedError, 'attempt to end not started element'
        name = self._stack.pop()
        self._file.write(self._make_indent() + '</%s>\n' % name)

    def text(self, data):
        """ Write specifed text, it is splited into lines.
        """

        if len(self._stack) == 0:
            raise WellFormedError, 'attempt to write text outside any element'
        indent = self._make_indent()
        for line in data.splitlines():
            self._file.write(indent + escape(line) + '\n')

    def _make_indent(self):
        """ Generate indentation string for current deep of xml tree.
        """

        return self._indent * len(self._stack)

class MakeData:
    def __init__(self):
        self._d = 0
        
    def __call__(self):
        nums = ['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine']
        self._d += 1
            
        return ' '.join([nums[int(c)] for c in str(self._d)])

def generate_tree(xml, level, n, idn, data):
    if level > 0:
        for i in xrange(n):
            idn += 1
            xml.start_element('node', dict(id=idn, name=data()), order=['id'])
            idn = generate_tree(xml, level - 1, n, idn, data)
            xml.end_element()
    else:
        for i in xrange(n):
            idn += 1
            xml.start_element('node', dict(id=idn, name=data()), order=['id'], close=True)
    return idn

import sys

def generate_test(filename, level, n):

    f = open(filename, 'w')
    xml = XmlWriter(f, indent='\t')
    data = MakeData()
 
    xml.start_element('test')
    xml.start_element('data')
    
    num = generate_tree(xml, level, n, 0, data)
    
    xml.end_element()
    xml.start_element('testcases')
    
    cases = [
        ('parent',      0.1),
        ('ancestors',   0.1),
        ('children',    0.1),
        ('descendants', 0.1),
    ]
    
    for method, fract in cases:
        xml.start_element('case', dict(method=method))
        xml.text(' '.join([str(random.randint(1, num)) for i in xrange(int(num * fract))]))
        xml.end_element()
    
    xml.end_element()
    xml.end_element()
    
    f.close()


from xml.sax import make_parser 
from xml.sax.handler import ContentHandler 
 
class TestHandler(ContentHandler): 
    def __init__ (self): 
        self._stack = []
        self._stack_id = []
        self._cases = {'insert': []}
        self._case = None

    def startElement(self, name, attrs):
        attr = {}
        for i in attrs.keys():
            attr[str(i)] = attrs[i].encode('utf-8')
        
        #if name == 'node':
        #    idn = str(attr.pop('id'))
        #    parent = self._stack_id[-1] if self._stack_id else None
        #    idx = self._handler(parent=parent, **attr)
        #    self._dict[idn] = idx
        #    self._stack_id.append(idx)
        
        if name == 'node':
            idn = str(attr['id'])
            parent = self._stack_id[-1] if self._stack_id else None
            self._cases['insert'].append(dict(id=idn, parent=parent, name=attr['name']))
            self._stack_id.append(idn)
        
        elif name == 'case':
            self._case = str(attr['method'])

        self._stack.append(name)

    def endElement(self, name):
        self._stack.pop()
        if name == 'node':
            self._stack_id.pop()
        if name == 'case':
            self._case = None

    def characters (self, ch):
        if self._case is not None:
            #print self._dict
            lst = [str(i) for i in ch.split()]
            self._cases[self._case] = self._cases.get(self._case, []) + lst

def read_tree(filename):
    parser = make_parser()
    test_handler = TestHandler()
    parser.setContentHandler(test_handler)
    
    fin = open(filename)
    parser.parse(fin)
    fin.close()
    
    return test_handler._cases


def h(**k):
    #print 'asdf', k
    return str(k['name'])

if __name__ == '__main__':
    generate_test('data_test.xml', 2, 3)
    print read_tree('data_test.xml', h)

