#!/usr/bin/env python
#-*- coding: utf-8 -*-


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


#class Memory(Tree):
    #def __init__(self, db):
        #self._d = {}
    
    #def _by_ids(self,  ids):
        #return [self._value(i) for i in self._d if self._d[i][0] in ids]
    
    #def _value(self, key):
        #return key
    
    #def get_roots(self):
        #return [self._value(i) for i in self._d if self._d[i][0] == None]

    #def get_parent(self, id):
        #pass

    #def get_ancestors(self, id):
        #pass

    #def get_children(self, id):
        #pass

    #def get_descendants(self, id):
        #pass


class Simple(Tree):
    tree_name = 'simple'
    tree_base = ['postgresql', 'mysql', 'sqlite', 'oracle', 'db2', 'sqlserver']
    
    def create_table(self):
        #if self.db.run("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name='simple'")[0]:
        if 'simple' in self.db.schema_list('table'):
            self.db.ddl({
                #'oracle': ['DROP TRIGGER simple_id_trigger', 'DROP TABLE simple', 'DROP SEQUENCE simple_id_seq'],
                'oracle': ['DROP TABLE simple', 'DROP SEQUENCE simple_id_seq'],
                '*':      "DROP TABLE simple",
            })
        self.db.ddl({
                'sqlite': "CREATE TABLE simple(id INTEGER PRIMARY KEY AUTOINCREMENT, parent int, name varchar(50))",
                'oracle': [
                    'CREATE SEQUENCE simple_id_seq START WITH 1 INCREMENT BY 1 NOMAXVALUE',
                    'CREATE TABLE simple(id int, parent int, name varchar(50))',
                    #'CREATE TRIGGER simple_id_trigger BEFORE INSERT ON simple FOR EACH row BEGIN SELECT simple_id_seq.nextval INTO :new.id FROM dual; END; /',
                ],
                'db2':    "CREATE TABLE simple(id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY (START WITH 1 INCREMENT BY 1), parent int, name varchar(50))", 
                'mssql':  "CREATE TABLE simple(id int IDENTITY PRIMARY KEY, parent int, name varchar(50))",
                '*':      "CREATE TABLE simple(id serial PRIMARY KEY, parent int, name varchar(50))",
        })

    def insert(self, parent, name):
        #pid = self.db.insert_id('INSERT INTO simple(parent, name) VALUES (%s, %s)', [parent, name])
        pid = self.db.insert('simple', parent=parent, name=name)
        return pid

    def get_roots(self):
        return self.db.run("SELECT * FROM simple WHERE parent IS NULL")

    def get_parent(self, id):
        return self.db.run("SELECT * FROM simple WHERE id = %s", [id])

    def get_ancestors(self, id):
        result = []
        i = id
        while i is not None:
            a = self.db.run("SELECT id, parent, name FROM simple WHERE id = %s", [i])
            #print a

            result.append(a[0])
            i = a[0][1]
        return result

    def get_children(self, id):
        return self.db.run("SELECT * FROM simple WHERE parent = %s", [id])


    def get_descendants(self, id):
        result = []
        ids = [id]

        while True:
            #a = [] #self.db.run("SELECT id, parent, name FROM simple WHERE (%s)" % 'OR'.join([' parent = %d ' % i for i in ids]))
            a = self.db.run("SELECT id, parent, name FROM simple WHERE (%s)" % ' OR '.join(['parent = %d' % i for i in ids]))
            #a = self.db.run("SELECT id, parent, name FROM simple WHERE parent IN %s", [ids])
            #print a
            result.extend(a)
            ids = [i['id'] for i in a]
            if not ids:
                break
            
        return result


class Full(Tree):
    #tree_name = 'full'
    tree_base = ['postgresql', 'mysql', 'sqlite', 'oracle', 'db2', 'sqlserver']
    
    def create_table(self):
        tables = self.db.schema_list('table')
        if 'full_data' in tables:
            self.db.execute('DROP TABLE full_data')
        if 'full_tree' in tables:
            self.db.execute('DROP TABLE full_tree')

        self.db.ddl("CREATE TABLE full_data(id serial PRIMARY KEY, name varchar(50))")
        self.db.ddl("CREATE TABLE full_tree(id serial PRIMARY KEY, top int, bottom int, distance int)")

    def insert(self, parent, name):
        #if self.db.is_dialect('postgresql'):
            #pid = self.db.run('INSERT INTO full_data VALUES (DEFAULT, %s) RETURNING id', [name])[0][0]
        #if self.db.is_dialect('mysql'):
            #self.db.execute('INSERT INTO full_data VALUES (DEFAULT, %s)', [name])
            #pid = self.db.run('SELECT LAST_INSERT_ID()')[0][0]
        pid = self.db.insert_id('INSERT INTO full_data(name) VALUES (%s)', [name])
        #print 'pid', pid
        #print '  parent', parent
        if parent is not None:

            for row in self.db.run('SELECT top, distance FROM full_tree WHERE bottom = %s', [parent]):
                #print '  row', row
                self.db.execute('INSERT INTO full_tree(top, bottom, distance) VALUES (%s, %s, %s)', [row[0], pid, row[1] + 1])
            self.db.execute('INSERT INTO full_tree(top, bottom, distance) VALUES (%s, %s, %s)', [pid, pid, 0])
        else:
            self.db.execute('INSERT INTO full_tree(top, bottom, distance) VALUES (%s, %s, %s)', [None, pid, 0])
            self.db.execute('INSERT INTO full_tree(top, bottom, distance) VALUES (%s, %s, %s)', [pid, pid, 0])


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
    #tree_name = 'nested'
    tree_base = ['postgresql', 'mysql', 'sqlite', 'oracle', 'db2', 'sqlserver']
    
    def create_table(self):
        tables = self.db.schema_list('table')
        if 'sets_data' in tables:
            self.db.execute('DROP TABLE sets_data')

        self.db.ddl({
            'sqlite': "CREATE TABLE sets_data(id integer PRIMARY KEY AUTOINCREMENT, lft int, rgt int, name varchar(50))",
            '*':      "CREATE TABLE sets_data(id serial PRIMARY KEY, lft int, rgt int, name varchar(50))",
        })
        
    def insert(self, parent, name):
        if parent is None:
            right = self.db.run('SELECT max(rgt) as max_rgt FROM sets_data')[0]['max_rgt']
            right = right or 0
            #pid = self.db.run('INSERT INTO sets_data VALUES (DEFAULT, %s, %s, %s) RETURNING id', [right + 1, right + 2, name])[0][0]
            pid = self.db.insert_id('INSERT INTO sets_data(lft, rgt, name) VALUES (%s, %s, %s)', [right + 1, right + 2, name])
        else:
            right = self.db.run('SELECT rgt FROM sets_data WHERE id = %s', [parent])[0]['rgt']
            #self.db.execute('UPDATE sets_data SET lft = lft + 2, rgt = rgt + 2 WHERE rgt > %s', [right])
            #self.db.execute('UPDATE sets_data SET rgt = rgt + 2 WHERE rgt = %s', [right])
            self.db.execute('UPDATE sets_data SET lft = lft + 2 WHERE lft >  %s', [right])
            self.db.execute('UPDATE sets_data SET rgt = rgt + 2 WHERE rgt >= %s', [right])
            #self.db.execute('INSERT INTO sets_data VALUES (DEFAULT, %s, %s, %s)', [right, right + 1, name])
            pid = self.db.insert_id('INSERT INTO sets_data(lft, rgt, name) VALUES (%s, %s, %s)', [right, right + 1, name])
        
        return pid
            
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

#class Trie(Tree):
    #pass
    
#class LTree(Tree):
    #pass
    
#class ConnectBySimple(Tree):
    #pass