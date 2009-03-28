#!/usr/bin/env python



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
    
    # TODO
    #def get_descendants_level(self, id, level):
        #pass

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

    def delete(self, id):
        pass

    def reparent(self, id, new_parent):
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
        if 'simple' in self.db.schema_list('table'):
            self.db.ddl({
                'oracle': ['DROP TABLE simple', 'DROP SEQUENCE simple_id_seq'],
                '*':      "DROP TABLE simple",
            })
        
        self.db.ddl({
                'sqlite': "CREATE TABLE simple(id INTEGER PRIMARY KEY AUTOINCREMENT, parent int, name varchar(50))",
                'oracle': [
                    'CREATE SEQUENCE simple_id_seq START WITH 1 INCREMENT BY 1 NOMAXVALUE',
                    'CREATE TABLE simple(id int, parent int, name varchar(50))',
                    ],
                'db2':    "CREATE TABLE simple(id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY (START WITH 1 INCREMENT BY 1), parent int, name varchar(50))", 
                'mssql':  "CREATE TABLE simple(id int IDENTITY PRIMARY KEY, parent int, name varchar(50))",
                '*':      """
                    CREATE TABLE simple(
                        id serial PRIMARY KEY, 
                        parent int REFERENCES simple(id) ON DELETE CASCADE, 
                        name varchar(50)
                    )""",
        })

    def insert(self, parent, name):
        """
            INSERT INTO simple (parent, name) 
                VALUES (:parent, :name)
        """
        pid = self.db.insert('simple', parent=parent, name=name)
        return pid

    def get_roots(self):
        return self.db.run("""
            SELECT * 
                FROM simple 
                WHERE parent IS NULL
            """
        )

    def get_parent(self, id):
        return self.db.run("""
            SELECT * 
                FROM simple 
                WHERE id = (
                    SELECT parent 
                        FROM simple 
                        WHERE id = :id
                )
            """, 
            dict(id=id)
        )

    def get_ancestors(self, id):
        result = []
        i = id
        while i is not None:
            a = self.db.run("SELECT id, parent, name FROM simple WHERE id = :id", dict(id=i))
            #print a

            result.append(a[0])
            i = a[0][1]
        return result

    def get_children(self, id):
        return self.db.run("""
            SELECT * 
                FROM simple 
                WHERE parent = :parent""", 
            dict(parent=id)
        )


    def get_descendants(self, id):
        result = []
        ids = [id]

        while True:
            a = self.db.run("SELECT id, parent, name FROM simple WHERE (%s)" % ' OR '.join(['parent = %d' % i for i in ids]))
            result.extend(a)
            ids = [i['id'] for i in a]
            if not ids:
                break
        
        return result


class Full(Tree):
    tree_name = 'full'
    tree_base = ['postgresql', 'mysql', 'sqlite', 'oracle', 'db2', 'sqlserver']
    
    def create_table(self):
        tables = self.db.schema_list('table')
        print tables
        if 'full_data' in tables:
            self.db.ddl({
                'oracle': ['DROP SEQUENCE full_data_id_seq', 'DROP TABLE full_data'],
                '*': 'DROP TABLE full_data',
            })
        if 'full_tree' in tables:
            self.db.execute('DROP TABLE full_tree')
        
        self.db.ddl({
                'sqlite': "CREATE TABLE full_data(id INTEGER PRIMARY KEY AUTOINCREMENT, name varchar(50))",
                'oracle': [
                    'CREATE SEQUENCE full_data_id_seq START WITH 1 INCREMENT BY 1 NOMAXVALUE',
                    'CREATE TABLE full_data(id int, name varchar(50))',
                    ],
                'db2':    "CREATE TABLE full_data(id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY (START WITH 1 INCREMENT BY 1), name varchar(50))", 
                'mssql':  "CREATE TABLE full_data(id int IDENTITY PRIMARY KEY, name varchar(50))",
                '*':      """
                    CREATE TABLE full_data(
                        id serial PRIMARY KEY, 
                        name varchar(50)
                    )""",
        })
        
        self.db.ddl("""
            CREATE TABLE full_tree(
                top_id int, 
                bottom_id int, 
                distance int
            )"""
        )
        
        self.db.ddl("""
            CREATE INDEX full_tree_idx_top_id    ON full_tree (top_id)""")
        self.db.ddl("""
            CREATE INDEX full_tree_idx_bottom_id ON full_tree (bottom_id)""")


    def insert(self, parent, name):
        pid = self.db.insert('full_data', name=name)

        if parent is not None:
            for row in self.db.run('SELECT top_id, distance FROM full_tree WHERE bottom_id = :parent', dict(parent=parent)):
                self.db.execute('INSERT INTO full_tree(top_id, bottom_id, distance) VALUES (:top_id, :bottom_id, :distance)', 
                    dict(top_id=row[0], bottom_id=pid, distance=row[1] + 1)
                )
        else:
            self.db.execute('INSERT INTO full_tree(top_id, bottom_id, distance) VALUES (:top_id, :bottom_id, :distance)', 
                dict(top_id=None, bottom_id=pid, distance=0)
            )
        self.db.execute('INSERT INTO full_tree(top_id, bottom_id, distance) VALUES (:top_id, :bottom_id, :distance)', 
            dict(top_id=pid, bottom_id=pid, distance=0)
        )


    def get_roots(self):
        return self.db.run("""
            SELECT d.id, d.name 
                FROM full_data d 
                    JOIN full_tree t 
                        ON (d.id=t.bottom_id) 
                WHERE t.top_id IS NULL AND t.distance = 0
            """
        )

    def get_parent(self, id):
        return self.db.run("""
            SELECT d.id, d.name 
                FROM full_data d 
                    JOIN full_tree t 
                        ON (d.id=t.top_id) 
                WHERE t.distance = 1 AND t.bottom_id = :id
            """, 
            dict(id=id)
        )

    def get_ancestors(self, id):
        #return self.db.run('''
            #SELECT d.id, d.name 
                #FROM full_data d 
                    #JOIN full_tree t 
                        #ON (d.id=t.top_id)
                #WHERE t.distance > 0 AND t.bottom_id = :id 
                #ORDER BY t.distance ASC
            #''', 
            #dict(id=id)
        #)
        return self.db.run("""
            SELECT d.id, d.name 
                FROM full_data d 
                    JOIN full_tree t 
                        ON (d.id=t.top_id)
                WHERE t.bottom_id = :id AND t.distance > 0 
            """, 
            dict(id=id)
        )

    def get_children(self, id):
        return self.db.run("""
            SELECT d.id, d.name 
                FROM full_data d 
                    JOIN full_tree t 
                        ON (d.id=t.bottom_id) 
                WHERE t.top_id = :id AND t.distance = 1""", 
            dict(id=id)
        )

    def get_descendants(self, id):
        return self.db.run("""
            SELECT d.id, d.name 
                FROM full_data d 
                    JOIN full_tree t 
                        ON (d.id=t.bottom_id) 
                WHERE t.top_id = :id AND t.distance > 0""", 
            dict(id=id)
        )


class NestedSets(Tree):
    tree_name = 'nested'
    tree_base = ['postgresql', 'mysql', 'sqlite', 'oracle', 'db2', 'sqlserver']
    
   
    def create_table(self):
        tables = self.db.schema_list('table')
        if 'nested_sets' in tables:
            self.db.ddl({
                'oracle': ['DROP TABLE nested_sets', 'DROP SEQUENCE nested_sets_id_seq'],
                '*':      "DROP TABLE nested_sets",
            })

        self.db.ddl({
            'sqlite': "CREATE TABLE nested_sets(id integer PRIMARY KEY AUTOINCREMENT, lft int, rgt int, name varchar(50))",
            'oracle': [
                    'CREATE SEQUENCE nested_sets_id_seq START WITH 1 INCREMENT BY 1 NOMAXVALUE',
                    'CREATE TABLE nested_sets(id int, lft int, rgt int, name varchar(50))',
                ],
            'db2': "CREATE TABLE nested_sets(id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY (START WITH 1 INCREMENT BY 1), lft int, rgt int, name varchar(50))",
            'mssql': "CREATE TABLE nested_sets(id int IDENTITY PRIMARY KEY, lft int, rgt int, name varchar(50))",
            '*':     """
                CREATE TABLE nested_sets(
                    id serial PRIMARY KEY, 
                    lft int, 
                    rgt int, 
                    name varchar(50)
                )""",
        })
        
    def insert(self, parent, name):
        if parent is None:
            right = self.db.run('SELECT max(rgt) as max_rgt FROM nested_sets')[0]['max_rgt']
            right = right or 0
            pid = self.db.insert('nested_sets', lft=(right + 1), rgt=(right + 2), name=name)
        else:
            right = self.db.run('SELECT rgt FROM nested_sets WHERE id = %s', [parent])[0]['rgt']
            self.db.execute('UPDATE nested_sets SET lft = lft + 2 WHERE lft >  :val', dict(val=right))
            self.db.execute('UPDATE nested_sets SET rgt = rgt + 2 WHERE rgt >= %s', dict(val=right))
            pid = self.db.insert('nested_sets', lft=(right), rgt=(right + 1), name=name)
        
        return pid
    
    def get_ancestors(self, id):
        return self.db.run("""
            SELECT d.id, d.name 
                FROM nested_sets d 
                WHERE 
                    d.lft < (SELECT d.lft FROM nested_sets d WHERE d.id = :id) 
                    AND 
                    (SELECT d.rgt FROM nested_sets d WHERE d.id = :id) < d.rgt 
                ORDER BY (d.rgt - d.lft) ASC
            """, dict(id=id))
    
    def get_descendants(self, id):
        return self.db.run("""
            SELECT d.id, d.name 
                FROM nested_sets d 
                WHERE 
                    d.lft > (SELECT d.lft FROM nested_sets d WHERE d.id = :id) 
                    AND 
                    (SELECT d.rgt FROM nested_sets d WHERE d.id = :id) > d.rgt 
                ORDER BY (d.rgt - d.lft) ASC""", dict(id=id))
    
    def get_roots(self):
        left = 0
        roots = []
        while True:
            data = self.db.run("""
                SELECT d.id, d.name, d.rgt as rgt 
                    FROM nested_sets d 
                    WHERE d.lft = :left""", 
                dict(left=left + 1)
            )
            if len(data) == 0:
                break
            roots.append(data[0])
            left = data[0]['rgt']
        return roots

#class Trie(Tree):
    #pass
    
#class LTree(Tree):
    #pass


class ConnectBy(Simple):
    tree_name = 'connectby'
    tree_base = ['oracle']

    def get_ancestors(self, id):
        return self.db.run("""
            SELECT level, id, parent, name 
                FROM simple 
                START WITH id = :id 
                CONNECT BY id = PRIOR parent""", 
            dict(id=id)
        )

    def get_descendants(self, id):
        return self.db.run("""
            SELECT level, id, parent, name 
                FROM simple 
                START WITH id = :id 
                CONNECT BY parent = PRIOR id""", 
            dict(id=id)
        )


class With(Simple):
    tree_name = 'with'
    tree_base = ['db2', 'sqlserver']

    def get_ancestors(self, id):
        return self.db.run("""
            WITH temptab(node_level, id, parent, name) AS
            (
                SELECT 0, root.id, root.parent, root.name
                    FROM simple root
                    WHERE root.id = :id
            UNION ALL
                SELECT t.node_level + 1, s.id, s.parent, s.name
                    FROM simple s, temptab t
                    WHERE s.id = t.parent
            )
            SELECT node_level, id, parent, name FROM temptab""",
            dict(id=id)
        )

    def get_descendants(self, id):
        return self.db.run("""
            WITH temptab(level, id, parent, name) AS
            (
                SELECT 0, root.id, root.parent, root.name
                    FROM simple root
                    WHERE root.id = :id
            UNION ALL
                SELECT t.level + 1, s.id, s.parent, s.name
                    FROM simple s, temptab t
                    WHERE s.parent = t.id
            )
            SELECT level, id, parent, name FROM temptab""",
            dict(id=id)
        )


class HierarchyId(Tree):
    tree_name = 'hierarchyid'
    tree_base = ['sqlserver']
    
    def create_table(self):
        if 'herid' in self.db.schema_list('table'):
            self.db.ddl("DROP TABLE herid")
        
        self.db.ddl("""
            CREATE TABLE herid (
                id int IDENTITY PRIMARY KEY,
                node hierarchyid,
                name varchar(50)
            )
        """)
        
        self.db.execute("""
            INSERT INTO herid (node, name) 
                VALUES (hierarchyid::GetRoot(), 'ROOT')""")

    def insert(self, parent, name):
        ''' http://technet.microsoft.com/en-us/library/bb677212.aspx '''
        if parent is None:
            parent = 1
            
        self.db.execute(u"""
                INSERT INTO herid (node, name) VALUES (
                    (SELECT node 
                        FROM herid 
                        WHERE id = :parent
                    ).GetDescendant(
                        (SELECT max(node) node 
                            FROM herid 
                            WHERE node.GetAncestor(1) = (
                                SELECT node 
                                    FROM herid 
                                    WHERE id = :parent
                            )
                        ), 
                        NULL
                    ), 
                    :name)
                """.encode('ascii'),
                dict(parent=parent, name=name)
        )
        ##self.db.execute(u'''
            ##WITH temp1 (node) AS (
                ##SELECT node FROM herid WHERE id = :parent
            ##),
            ##temp2 (node) AS (
                ##SELECT max(node) node FROM herid WHERE node.GetAncestor(1) = temp1.node
            ##)
            ##INSERT INTO herid (node, name) VALUES (temp1.node.GetDescendant(temp2.node, NULL), NULL)
            ##'''.encode('ascii'),
            ##dict(parent=parent)
        ##)
        pid = self.db.execute('SELECT id FROM herid WHERE id = @@IDENTITY').list()[0][0]
        return pid

    def get_roots(self):
        return self.db.run("""
            SELECT * 
                FROM herid 
                WHERE node.GetLevel() = 1""")

    def get_parent(self, id):
        return self.db.run("""
            SELECT * 
                FROM herid 
                WHERE node = (
                    SELECT node.GetAncestor(1) 
                        FROM herid 
                        WHERE id = :id
                )""", 
            dict(id=id)
        )

    def get_ancestors(self, id):
        return self.db.run("""
            SELECT * 
                FROM herid 
                WHERE (
                    SELECT node FROM herid WHERE id = :id
                ).IsDescendant(node)
                """,
            dict(id=id)
        )

    def get_children(self, id):
        return self.db.run("""
            SELECT * 
                FROM herid 
                WHERE node.GetAncestor(1) = (
                    SELECT node 
                        FROM herid 
                        WHERE id = :parent
                )""", 
            dict(parent=id)
        )


    def get_descendants(self, id):
        return self.db.run("""
            SELECT * 
                FROM herid 
                WHERE node.IsDescendant((
                    SELECT node FROM herid WHERE id = :parent
                ))""", 
            dict(parent=id)
        )


