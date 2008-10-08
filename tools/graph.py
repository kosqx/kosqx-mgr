
import sys

result = {}
file = open(sys.argv[1])

#name   = None
#value  = None
#record = None

data = None

class Data:
    pass
    def __str__(self):
        return str(self.__dict__)

for line in file:
    line = line.strip()
    if line.startswith('#'):
        pass
    elif line == "":
        if data is not None:
            result[data.name] = data
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
    result[data.name] = data

#print result

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

print """
digraph G {
    graph [fontsize=30 labelloc="t" label="" splines=true overlap=false rankdir=TB];
    /*node [color=lightblue2, style=filled, fontsize=10];*/
    ratio = auto;

"""

for node in result:
    print '    %s [label=<%s>, shape=none];' % (node, make_table(result[node].record))
for node in result:
    if result[node].parent != "_":
        #result[node]
        print "    %s -> %s;" % (result[node].parent, node)
print "}"