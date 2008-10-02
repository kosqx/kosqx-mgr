#!/usr/bin/env python
#-*- coding: utf-8 -*-

DSN = "dbname='test_tree' user='kosqx' host='localhost' password='kos144'"

import psycopg2

class Tree:
    def get_roots(self, id):
        pass

    def get_roots_count(self, id):
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

    def get_roots(self, id):
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



class AscTree(Tree):
    def __init__(self, db):
        self.db = db

    def create_table(self):
        if self.db.run("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name='asc_data'")[0]:
            self.db.ddl("DROP TABLE asc_data")
        if self.db.run("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name='asc'")[0]:
            self.db.ddl("DROP TABLE asc_tree")

        self.db.ddl("CREATE TABLE asc(id serial PRIMARY KEY, name varchar(50))")
        self.db.ddl("CREATE TABLE asc(id serial PRIMARY KEY, top int, bottom int, distance int)")

    def insert(self, parent, name):
        self.db.execute('INSERT INTO asc VALUES (DEFAULT, %s, %s)', [parent, name])

    def get_roots(self, id):
        return self.db.run("SELECT * FROM asc WHERE parent IS NULL")

    def get_parent(self, id):
        return self.db.run("SELECT * FROM asc WHERE id = %s", [id])

    def get_ancestors(self, id):
        result = []
        i = id
        while i is not None:
            a = self.db.run("SELECT * FROM asc WHERE id = %s", [i])
            print a

            result.append(a[0])
            i = a[0][1]
        return result

    def get_childs(self, id):
        return self.db.run("SELECT * FROM asc WHERE parent = %s", [id])


    def get_descendants(self, id):
        pass



class PostgresDB:
    def __init__(self):
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
        except psycopg2.ProgrammingError:
            print 'ProgrammingError'
        return result

    def ddl(self, sql):
        self.cur.execute(sql)
        self.db.commit()

    def execute(self, sql, data):
        self.cur.execute(sql, data)

    def executemany(self, sql, data):
        self.cur.executemany(sql, data)

    def commit(self):
        self.db.commit()


def main():
    db = PostgresDB()
    tree = SimpleTree(db)
    tree.create_table()
    for i in xrange(1,10000):
        parent = i / 10
        if parent == 0:
            parent = None
        tree.insert(parent, "%.4d" % i)
    db.commit()

    print tree.get_childs(100)
    print 'roots:', tree.get_roots(100)
    print tree.get_ancestors(100)


if __name__ == '__main__':
    main()
