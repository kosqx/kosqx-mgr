#!/usr/bin/env python
#-*- coding: utf-8 -*-

#DSN = "dbname='test_tree' user='kosqx' host='localhost' password='kos144'"

#import psycopg2

import pada

class Tree:
    def __init__(self, db):
        self.db = db
    
    def get_roots(self):
        pass

    def get_parent(self, id):
        pass

    def get_ancestors(self, id):
        pass

    def get_children(self, id):
        pass

    def get_descendants(self, id):
        pass

    def get_roots_count(self):
        return len(self.get_roots())
    def get_ancestors_count(self, id):
        return len(self.get_ancestors_count(id))
    def get_children_count(self, id):
        return len(self.get_children_count(id))
    def get_descendants_count(self, id):
        return len(self.get_descendants_count(id))



    def create_table(self):
        pass

    def insert(self, parent, name):
        pass

    def update(self, parent, name):
        pass

    def delete(self, id):
        pass

    def move(self, id, parent_to):
        pass


class SimpleTree(Tree):
    def create_table(self):
        if self.db.run("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name='simple'")[0]:
            self.db.ddl("DROP TABLE simple")
        self.db.ddl("CREATE TABLE simple(id serial PRIMARY KEY, parent int, name varchar(50))")

    def insert(self, parent, name):
        self.db.execute('INSERT INTO simple VALUES (DEFAULT, %s, %s)', [parent, name])

    def get_roots(self):
        return self.db.run("SELECT * FROM simple WHERE parent IS NULL")

    def get_parent(self, id):
        return self.db.run("SELECT * FROM simple WHERE id = %s", [id])

    def get_ancestors(self, id):
        result = []
        i = id
        while i is not None:
            a = self.db.run("SELECT * FROM simple WHERE id = %s", [i])
            print a

            result.append(a[0])
            i = a[0][1]
        return result

    def get_children(self, id):
        return self.db.run("SELECT * FROM simple WHERE parent = %s", [id])


    def get_descendants(self, id):
        pass



class FullTree(Tree):
    def create_table(self):
        tables = self.db.schema_list('table')
        if 'full_data' in tables:
            self.db.execute('DROP TABLE full_data')
        if 'full_tree' in tables:
            self.db.execute('DROP TABLE full_tree')

        self.db.ddl("CREATE TABLE full_data(id serial PRIMARY KEY, name varchar(50))")
        self.db.ddl("CREATE TABLE full_tree(id serial PRIMARY KEY, top int, bottom int, distance int)")

    def insert(self, parent, name):
        pid = self.db.run('INSERT INTO full_data VALUES (DEFAULT, %s) RETURNING id', [name])[0][0]
        print 'pid', pid
        print '  parent', parent
        if parent is not None:

            for row in self.db.run('SELECT top, distance FROM full_tree WHERE bottom = %s', [parent]):
                #print '  row', row
                self.db.execute('INSERT INTO full_tree VALUES (DEFAULT, %s, %s, %s)', [row[0], pid, row[1] + 1])
            self.db.execute('INSERT INTO full_tree VALUES (DEFAULT, %s, %s, %s)', [pid, pid, 0])
        else:
            self.db.execute('INSERT INTO full_tree VALUES (DEFAULT, %s, %s, %s)', [None, pid, 0])
            self.db.execute('INSERT INTO full_tree VALUES (DEFAULT, %s, %s, %s)', [pid, pid, 0])


    def get_roots(self):
        return self.db.run("SELECT d.id, d.name FROM full_data d JOIN full_tree t ON (d.id=t.bottom) WHERE t.top IS NULL AND t.distance = 0")

    def get_parent(self, id):
        return self.db.run("SELECT d.id, d.name FROM full_data d JOIN full_tree t ON (d.id=t.top) WHERE t.distance = 1 AND t.bottom = %s", [id])

    def get_ancestors(self, id):
        return self.db.run("SELECT d.id, d.name FROM full_data d JOIN full_tree t ON (d.id=t.top) WHERE t.distance > 0 AND t.bottom = %s ORDER BY t.distance ASC", [id])

    def get_children(self, id):
        return self.db.run("SELECT d.id, d.name FROM full_data d JOIN full_tree t ON (d.id=t.bottom) WHERE t.top = %s AND t.distance = 1", [id])

    def get_descendants(self, id):
        pass

class NestedSets(Tree):
    def create_table(self):
        tables = self.db.schema_list('table')
        if 'sets_data' in tables:
            self.db.execute('DROP TABLE sets_data')

        self.db.ddl("CREATE TABLE sets_data(id serial PRIMARY KEY, lft int, rgt int, name varchar(50))")
        
    def insert(self, parent, name):
        if parent is None:
            right = self.db.run('SELECT max(rgt) as max_rgt FROM sets_data')[0]['max_rgt']
            right = right or 0
            pid = self.db.run('INSERT INTO sets_data VALUES (DEFAULT, %s, %s, %s) RETURNING id', [right + 1, right + 2, name])[0][0]
        else:
            right = self.db.run('SELECT rgt FROM sets_data WHERE id = %s', [parent])[0]['rgt']
            #self.db.execute('UPDATE sets_data SET lft = lft + 2, rgt = rgt + 2 WHERE rgt > %s', [right])
            #self.db.execute('UPDATE sets_data SET rgt = rgt + 2 WHERE rgt = %s', [right])
            self.db.execute('UPDATE sets_data SET lft = lft + 2 WHERE lft >  %s', [right])
            self.db.execute('UPDATE sets_data SET rgt = rgt + 2 WHERE rgt >= %s', [right])
            self.db.execute('INSERT INTO sets_data VALUES (DEFAULT, %s, %s, %s)', [right, right + 1, name])
            
    def get_ancestors(self, id):
        return self.db.run("""
            SELECT d.id, d.name 
            FROM sets_data d 
            WHERE 
                d.lft < (SELECT d.lft FROM sets_data d WHERE d.id = %s) 
                AND 
                (SELECT d.rgt FROM sets_data d WHERE d.id = %s) < d.rgt 
            ORDER BY (d.rgt - d.lft) ASC""", [id, id])
            
    def get_descendants(self, id):
        return self.db.run("""
            SELECT d.id, d.name 
            FROM sets_data d 
            WHERE 
                d.lft > (SELECT d.lft FROM sets_data d WHERE d.id = %s) 
                AND 
                (SELECT d.rgt FROM sets_data d WHERE d.id = %s) > d.rgt 
            ORDER BY (d.rgt - d.lft) ASC""", [id, id])
            
    def get_roots(self):
        left = 0
        roots = []
        while True:
            data = self.db.run("""SELECT d.id, d.name, d.rgt as rgt FROM sets_data d WHERE d.lft = %s""", [left + 1])
            if len(data) == 0:
                break
            # TODO: co zrobić z niepotrzebnym left?
            roots.append(data[0])
            left = data[0]['rgt']
        return roots

def main():
    db = pada.connect(dsn="dialect='postgresql' dbname='test_tree' host='localhost' user='kosqx' password='kos144'")
    #tree = SimpleTree(db)
    #tree = FullTree(db)
    tree = NestedSets(db)
    tree.create_table()
    for i in xrange(1,1000):
        parent = i / 10
        if parent == 0:
            parent = None
        tree.insert(parent, "%.4d" % i)
    db.commit()

    print 'roots:   ', tree.get_roots()
    print 'parent:  ', tree.get_parent(100)
    print 'children:', tree.get_children(10)
    print 'ancest:  ', tree.get_ancestors(777)
    print 'ancest:  ', tree.get_descendants(8)

    #print tree.get_ancestors(100)


if __name__ == '__main__':
    main()
