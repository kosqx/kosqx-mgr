
import sys
import subprocess

class Data:
    def __str__(self):
        return str(self.__dict__)


def txt2dot(file):
    result = []
    out = []
    data = None
    
    for line in file:
        line = line.strip()
        if line.startswith('#'):
            pass
        elif line == "":
            if data is not None:
                result.append(data)
            data = None
        elif line.startswith('>'):
            data = Data()
            tmp = line[1:].split()
            data.name = tmp[0]
            data.parent = tmp[1]
            data.record = []
        else:
            data.record.append([i.strip() for i in line.split('|')])
    
    if data is not None:
        result.append(data)

    def make_table(table):
        result = []
        result.append('<table border="0"  cellborder="1" cellspacing="0">')
        for row in table:
            result.append('<tr>')
            for cell in row:
                result.append('<td>%s</td>' % cell)
            result.append('</tr>')
        result.append('</table>')
    
        return ''.join(result)
    
    out.append("""
    digraph G {
        graph [fontsize=30 rankdir=TB];
        /*node [color=lightblue2, style=filled, fontsize=10];*/
        ratio = auto;
    """)
    
    for node in result:
        out.append('    %s [label=<%s>, shape=none];' % (node.name, make_table(node.record)) )
    for node in result:
        if node.parent != "_":
            out.append("    %s -> %s;" % (node.parent, node.name))
    out.append("}")
    
    return '\n'.join(out)


def dot2png(data, name):
    p = subprocess.Popen('dot -Tpng -o' + name, shell=True, close_fds=True, stdin=subprocess.PIPE).communicate(data)[0]


if __name__ == '__main__':
    fin = open(sys.argv[1])
    lines = fin.readlines()
    dot2png(txt2dot(lines), sys.argv[2])
    fin.close()

