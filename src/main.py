#!/usr/bin/env python
#-*- coding: utf-8 -*-

DSN = "dbname='test_tree' user='kosqx' host='localhost' password='kos144'"

import psycopg2

class Tree:
    def get_roots(self):
        pass

    def get_roots_count(self):
        pass

    def get_parent(self, id):
        pass

    def get_ancestors(self, id):
        pass

    def get_ancestors_count(self, id):
        pass

    def get_childs(self, id):
        pass

    def get_childs_count(self, id):
        pass

    def get_descendants(self, id):
        pass

    def get_descendants_count(self, id):
        pass



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
    def __init__(self, db):
        self.db = db

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

    def get_childs(self, id):
        return self.db.run("SELECT * FROM simple WHERE parent = %s", [id])


    def get_descendants(self, id):
        pass



class FullTree(Tree):
    def __init__(self, db):
        self.db = db

    def create_table(self):
        #if self.db.run("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name='full_data'")[0]:
            #self.db.ddl("DROP TABLE full_data")
        #if self.db.run("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name='full_tree'")[0]:
            #self.db.ddl("DROP TABLE full_tree")
        self.db.drop_if_exists('full_data')
        self.db.drop_if_exists('full_tree')

        self.db.ddl("CREATE TABLE full_data(id serial PRIMARY KEY, name varchar(50))")
        self.db.ddl("CREATE TABLE full_tree(id serial PRIMARY KEY, top int, bottom int, distance int)")

    def insert(self, parent, name):
        pid = self.db.run('INSERT INTO full_data VALUES (DEFAULT, %s) RETURNING id', [name])[0][0]
        print 'pid', pid
        print '  parent', parent
        if parent is not None:

            for row in self.db.run('SELECT top, distance FROM full_tree WHERE bottom = %s', [parent]):
                print '  row', row
                self.db.run('INSERT INTO full_tree VALUES (DEFAULT, %s, %s, %s)', [row[0], pid, row[1] + 1])
            self.db.run('INSERT INTO full_tree VALUES (DEFAULT, %s, %s, %s)', [pid, pid, 0])
        else:
            self.db.run('INSERT INTO full_tree VALUES (DEFAULT, %s, %s, %s)', [None, pid, 0])
            self.db.run('INSERT INTO full_tree VALUES (DEFAULT, %s, %s, %s)', [pid, pid, 0])


    def get_roots(self):
        return self.db.run("SELECT d.id, d.name FROM full_data d JOIN full_tree t ON (d.id=t.bottom) WHERE t.top IS NULL AND t.distance = 0")

    def get_parent(self, id):
        return self.db.run("SELECT d.id, d.name FROM full_data d JOIN full_tree t ON (d.id=t.top) WHERE t.distance = 1 AND t.bottom = %s", [id])

    def get_ancestors(self, id):
        return self.db.run("SELECT d.id, d.name FROM full_data d JOIN full_tree t ON (d.id=t.top) WHERE t.distance > 0 AND t.bottom = %s ORDER BY t.distance ASC", [id])

    def get_childs(self, id):
        return self.db.run("SELECT d.id, d.name FROM full_data d JOIN full_tree t ON (d.id=t.bottom) WHERE t.top = %s AND t.distance = 1", [id])


    def get_descendants(self, id):
        pass

class RowObject(object):
    def __init__(self, data, names):
        self._data = data
        self._names = names
    def __getitem__(self, key):
        if key in self:
            return dict.__getitem__(self, key)
        else:
            return self.default

class Database(object):
    def _get_sql(self, sql):
        if isinstance(sql, basestring):
            return sql
        else:
            for i in self._short_db_names:
                if i in sql:
                    return sql[i]
            return sql['*']

    def _build_names(self):
        result = {}
        self._cur.description

    def execute(self, sql, data=None):
        asql = self._get_sql(sql)
        if data is not None:
            self._cur.execute(asql, data)
        else:
            self._cur.execute(asql)
        return self

    def executemany(self, sql, data):
        self._cur.executemany(self._get_sql(sql), data)

    def commit(self):
        self._db.commit()

    def list(self):
        result = []
        try:
            if self._cur.rowcount >= 0
                for i in self.cur.fetchall():
                    result.append(i)
        except:
            pass
        return result


class PostgresDB:
    def __init__(self):
        Database.__init__(self)
        self._short_db_names = ['pg', 'psql', 'postgres', 'postgresql']
        self.db = psycopg2.connect(DSN)
        self.cur = self.db.cursor()

    def run(self, sql, data=None):
        result = []
        try:
            if data is not None:
                self.cur.execute(sql, data)
            else:
                self.cur.execute(sql)
            for i in self.cur.fetchall():
                result.append(i)
        except psycopg2.ProgrammingError, e:
            print 'ProgrammingError', e
        return result

    def ddl(self, sql):
        self.cur.execute(sql)
        self.db.commit()


    def drop_if_exists(self, name, kind='table'):
        kind = kind.lower()
        print 'drop', kind
        if kind in ['table']:
            print 'aaa'
            r = self.run("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name = %s ", [name])
            print r
            if len(r) > 0:
                self.run('DROP TABLE "%s"' % name)
                self.commit()

def main():
    db = PostgresDB()
    #tree = SimpleTree(db)
    tree = FullTree(db)
    tree.create_table()
    for i in xrange(1,1000):
        parent = i / 10
        if parent == 0:
            parent = None
        tree.insert(parent, "%.4d" % i)
    db.commit()

    print 'roots: ', tree.get_roots()
    print 'parent:', tree.get_parent(100)
    print 'childs:', tree.get_childs(10)
    print 'ancest:', tree.get_ancestors(777)

    #print tree.get_ancestors(100)


if __name__ == '__main__':
    main()
