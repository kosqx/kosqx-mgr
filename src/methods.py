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


class Memory(Tree):
    def __init__(self):
        self._d = {}
    
    def create_table(self):
        pass
    
    def _get(self, i):
        return i, self._d[i]
    
    def insert(self, parent, name):
        l = len(self._d) + 1
        if parent is None:
            self._d[l] = (None, name)
        else:
            self._d[l] = (int(parent), name)
        return l
    
    def get_roots(self):
        #print self._d
        #return [self._value(i) for i in self._d if self._d[i][0] == None]
        return [self._get(i) for i in self._d if self._d[i] == None]

    def get_parent(self, id):
        i = self._d[int(id)][0]
        return (i, self._d[i])

    def get_ancestors(self, id):
        result = []
        i = id
        cnt = 0
        while i is not None and cnt < 10:
            result.append((i, self._d[i]))
            i = self._d[i][0]
            
            
            cnt+=1
        return result

    def get_children(self, id):
        return [self._get(i) for i in self._d if self._d[i][0] == id]
        

    def get_descendants(self, id):
        keys = set([id])
        result = [self._get(i) for i in keys]
        while keys:
            tmp = [i for i in self._d if self._d[i][0] in keys]
            result.extend([self._get(i) for i in tmp])
            keys = set(tmp)
        
        return result


#####################################################################################################################################################
#####################################################################################################################################################


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
                'sqlite': "CREATE TABLE simple(id INTEGER PRIMARY KEY AUTOINCREMENT, parent int, name varchar(100))",
                'oracle': [
                    'CREATE SEQUENCE simple_id_seq START WITH 1 INCREMENT BY 1 NOMAXVALUE',
                    'CREATE TABLE simple(id int, parent int, name varchar(100))',
                    ],
                'db2':    "CREATE TABLE simple(id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY (START WITH 1 INCREMENT BY 1), parent int, name varchar(100))", 
                'mssql':  "CREATE TABLE simple(id int IDENTITY PRIMARY KEY, parent int, name varchar(100))",
                '*':      """
                    CREATE TABLE simple(
                        id     serial PRIMARY KEY, 
                        parent int REFERENCES simple(id) ON DELETE CASCADE, 
                        name   varchar(100)
                    )""",
        })

    def insert(self, parent, name):
        """
            INSERT INTO simple (parent, name) 
                VALUES (:parent, :name)
        """
        pid = self.db.insert_returning_id('simple', dict(parent=parent, name=name))
        return pid

    def get_roots(self):
        return self.db.execute_and_fetch("""
            SELECT * 
                FROM simple 
                WHERE parent IS NULL
            """
        )

    def get_parent(self, id):
        return self.db.execute_and_fetch("""
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
        # """
        result = []
        while id is not None:
            row = self.db.execute('''
                SELECT id, parent, name
                    FROM simple
                    WHERE id = :id
                ''',
                dict(id=id)
            ).fetch_one()
            result.append(row)
            id = row.parent
        return result
        # """

    def get_children(self, id):
        return self.db.execute_and_fetch("""
            SELECT * 
                FROM simple 
                WHERE parent = :parent
            """, 
            dict(parent=id)
        )

    def get_descendants(self, id):
        # """
        result = []
        ids = [id]
        
        while ids:
            rows = self.db.execute('''
                SELECT id, parent, name
                    FROM simple
                    WHERE (%s)''' % ' OR '.join(['parent = %d' % i for i in ids])
            ).fetch_all()
            result.extend(rows)
            ids = [row.id for row in rows]
        
        return result
        # """


# ---------------------------------------------------------------------------------------------------------------------------------------------------


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
            'sqlite': "CREATE TABLE nested_sets(id integer PRIMARY KEY AUTOINCREMENT, lft int, rgt int, name varchar(100))",
            'oracle': [
                    'CREATE SEQUENCE nested_sets_id_seq START WITH 1 INCREMENT BY 1 NOMAXVALUE',
                    'CREATE TABLE nested_sets(id int, lft int, rgt int, name varchar(100))',
                ],
            'db2': '''
                CREATE TABLE nested_sets(
                    id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY (START WITH 1 INCREMENT BY 1),
                    lft int,
                    rgt int,
                    name varchar(100)
                )''',
            'mssql': "CREATE TABLE nested_sets(id int IDENTITY PRIMARY KEY, lft int, rgt int, name varchar(100))",
            '*':     """
                CREATE TABLE nested_sets(
                    id   serial PRIMARY KEY, 
                    lft  int, 
                    rgt  int, 
                    name varchar(100)
                )""",
        })
        
    def insert(self, parent, name):
        # """
        if parent is None:
            right = self.db.execute('''
                SELECT max(rgt) AS max_rgt
                    FROM nested_sets
                '''
            ).fetch_single('max_rgt')
            right = right or 0
            pid = self.db.insert_returning_id(
                'nested_sets',
                dict(
                    lft=(right + 1),
                    rgt=(right + 2),
                    name=name
                )
            )
        else:
            right = self.db.execute('''
                SELECT rgt
                    FROM nested_sets
                    WHERE id = :parent
                ''',
                dict(parent=parent)
            ).fetch_single('rgt')
            self.db.execute('''
                UPDATE nested_sets
                    SET lft = lft + 2
                    WHERE lft >  :val
                ''',
                dict(val=right)
            )
            self.db.execute('''
                UPDATE nested_sets
                    SET rgt = rgt + 2
                    WHERE rgt >= :val
                ''',
                dict(val=right)
            )
            pid = self.db.insert_returning_id(
                'nested_sets',
                dict(
                    lft=(right),
                    rgt=(right + 1),
                    name=name
                )
            )
        
        return pid
        # """
    
    def get_roots(self):
        return self.db.execute_and_fetch("""
            SELECT result.*
                FROM nested_sets AS result
                    LEFT OUTER JOIN nested_sets AS box
                        ON (result.lft > box.lft AND result.rgt < box.rgt)
                WHERE
                    box.lft IS NULL
            """,
            dict(id=id)
        )
    
    def get_parent(self, id):
        """
            SELECT result.*
                FROM nested_sets AS box
                    JOIN nested_sets AS result
                        ON (box.lft BETWEEN result.lft + 1  AND result.rgt)
                WHERE
                    box.id = :id
                ORDER BY result.lft DESC
                LIMIT 1
        """
        
        return self.db.execute('''
            SELECT result.*
                FROM nested_sets AS box
                    JOIN nested_sets AS result
                        ON (box.lft BETWEEN result.lft + 1  AND result.rgt)
                WHERE
                    box.id = :id
                ORDER BY result.lft DESC
            ''',
            dict(id=id)
        ).fetch_one()
    
    def get_ancestors(self, id):
        return self.db.execute_and_fetch("""
            SELECT result.*
                FROM nested_sets AS box
                    JOIN nested_sets AS result
                        ON (box.lft BETWEEN result.lft AND result.rgt)
                WHERE
                    box.id = :id
                ORDER BY result.lft DESC
            """,
            dict(id=id)
        )
    
    def get_children(self, id):
        return self.db.execute_and_fetch("""
            SELECT result.*
                FROM nested_sets AS box
                    JOIN nested_sets AS result
                        ON (result.lft BETWEEN box.lft + 1 AND box.rgt)
                WHERE
                    box.id = :id AND
                    NOT EXISTS (
                        SELECT *
                            FROM nested_sets ns
                            WHERE
                                (ns.lft BETWEEN box.lft + 1 AND box.rgt) AND
                                (result.lft BETWEEN ns.lft + 1 AND ns.rgt)
                    )
            """,
            dict(id=id)
        )
    
    def get_descendants(self, id):
        return self.db.execute_and_fetch("""
            SELECT result.*
                FROM nested_sets AS box
                    JOIN nested_sets AS result
                        ON (result.lft BETWEEN box.lft + 1 AND box.rgt)
                WHERE
                    box.id = :id
                ORDER BY result.lft ASC
            """,
            dict(id=id)
        )


# ---------------------------------------------------------------------------------------------------------------------------------------------------


class PathEnum(Tree):
    tree_name = 'pathenum'
    #tree_base = ['postgresql', 'mysql', 'sqlite', 'oracle', 'db2', 'sqlserver']
    tree_base = ['postgresql', 'mysql', 'sqlite', 'oracle', 'db2']
    
   
    def create_table(self):
        tables = self.db.schema_list('table')
        if 'pathenum' in tables:
            self.db.ddl({
                'oracle': ['DROP TABLE pathenum', 'DROP SEQUENCE pathenum_id_seq'],
                '*':      "DROP TABLE pathenum",
            })
            
        self.db.ddl({
            '*': """
                CREATE TABLE pathenum(
                    id   serial PRIMARY KEY, 
                    path varchar(100), 
                    name varchar(100)
                )""",
            'oracle': [
                    'CREATE SEQUENCE pathenum_id_seq START WITH 1 INCREMENT BY 1 NOMAXVALUE',
                    'CREATE TABLE pathenum(id int, path varchar(100), name varchar(100))',
                ],
            'mssql': '''
                CREATE TABLE nested_sets(
                    id int IDENTITY PRIMARY KEY,
                    path varchar(100),
                    name varchar(100)
                )
                ''',
            'db2': '''
                CREATE TABLE pathenum(
                    id   integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY (START WITH 1 INCREMENT BY 1), 
                    path varchar(100),
                    name varchar(100)
                )
                '''
        })
        
    def insert(self, parent, name):
        """
            INSERT INTO pathenum (path, name) VALUES (
                (SELECT path || id ||  '.' FROM pathenum WHERE id = :parent),
                :name
            )
        """
        if parent is None:
            #pid = self.db.execute('''
            #    INSERT INTO pathenum (path, name) VALUES (
            #        '',
            #        :name
            #    ) RETURNING id
            #    ''', dict(parent=parent, name=name)
            #).list()[0][0]
            pid = self.db.insert_returning_id('pathenum', dict(path='', name=name))
        else:
            #pid = self.db.execute('''
            #    INSERT INTO pathenum (path, name) VALUES (
            #        (SELECT path || id ||  '.' FROM pathenum WHERE id = :parent),
            #        :name
            #    ) RETURNING id
            #    ''', dict(parent=parent, name=name)
            #).list()[0][0]
            if self.db.is_dialect('mysql'):
                # FIXME: bardzo brzydki kod
                path = self.db.execute('''SELECT concat(path, id, '.') AS path FROM pathenum WHERE id = %s''' % parent).fetch_single('path')
                #print path
                pid = self.db.insert_returning_id('pathenum', dict(name=name, path=path))
                #pid = self.db.insert_returning_id('pathenum', dict(name=name), dict(
                #    path="(SELECT concat(path, id,  '.') FROM pathenum WHERE id = %s)" % parent)
                #)
            else:
                
                pid = self.db.insert_returning_id('pathenum', dict(name=name), dict(
                    path="(SELECT path || id ||  '.' FROM pathenum WHERE id = %s)" % parent)
                )
        return pid
    
    def get_roots(self):
        return self.db.execute_and_fetch("""
            SELECT *  
                FROM pathenum 
                WHERE path = ''
            """
        )

    def get_parent(self, id):
        return self.db.execute_and_fetch({
            '*': """
                    SELECT result.*
                        FROM
                            pathenum AS arg,
                            pathenum AS result
                        WHERE
                            arg.id = :id AND
                            (result.path || result.id || '.') = arg.path
                """,
            'mysql': '''
                    SELECT result.*
                        FROM
                            pathenum AS arg,
                            pathenum AS result
                        WHERE
                            arg.id = :id AND
                            concat(result.path, result.id, '.') = arg.path
                '''
            },
            dict(id=id)
        )

    def get_ancestors(self, id):
        #    SELECT p2.*
        #FROM pathenum p1, pathenum p2
        #WHERE p1.id = :id AND
        #    position(p2.path || p2.id IN p1.path) = 1
        
        if self.db.is_dialect('db2'):
            row = self.db.execute('''SELECT path, id FROM pathenum WHERE id = :id''', dict(id=id)).fetch_one()
            return self.db.execute_and_fetch('''
                SELECT *
                    FROM pathenum
                    WHERE path LIKE '%s'
                ''' % (row.path + str(row.id) + '%')
            )
            
            #return self.db.execute_and_fetch('''
            #    SELECT *
            #        FROM pathenum
            #        WHERE path LIKE :pattern
            #    ''',
            #    dict(pattern=(row.path + str(row.id) + '%'))
            #)
        
        return self.db.execute_and_fetch({
            '*': """
                SELECT result.*
                    FROM
                        pathenum AS arg,
                        pathenum AS result
                    WHERE
                        arg.id = :id AND
                        arg.path LIKE (result.path || result.id || '%')
                    ORDER BY result.path DESC
                """,
            # tutaj '%%' jest gdyz mysqldb uzywa domyslnie formatu %s
            'mysql': '''
                    SELECT result.*
                        FROM
                            pathenum AS arg,
                            pathenum AS result
                        WHERE
                            arg.id = :id AND
                            arg.path LIKE concat(result.path, result.id, '%%')
                        ORDER BY result.path DESC
                '''
            },
            dict(id=id)
        )
    
    def get_children(self, id):
        return self.db.execute_and_fetch({
            '*': """
                SELECT * 
                    FROM pathenum 
                    WHERE path = (
                        SELECT path || id ||  '.'
                            FROM pathenum 
                            WHERE id = :parent
                    )
                """,
            'mysql': '''
                SELECT * 
                    FROM pathenum 
                    WHERE path = (
                        SELECT concat(path, id, '.')
                            FROM pathenum 
                            WHERE id = :parent
                    )
                '''
            }, 
            dict(parent=id)
        )

    def get_descendants(self, id):
        
        if self.db.is_dialect('db2'):
            row = self.db.execute('''SELECT path, id FROM pathenum WHERE id = :id''', dict(id=id)).fetch_one()
            print row
            return self.db.execute_and_fetch('''
                SELECT *
                    FROM pathenum
                    WHERE path LIKE '%s'
                ''' % (row.path + str(row.id) + '%')
            )
        
        return self.db.execute_and_fetch({
            '*': """
                SELECT * 
                    FROM pathenum 
                    WHERE path LIKE (
                        SELECT path || id || '.' || '%'
                            FROM pathenum
                            WHERE id = :parent
                    )
                """,
            'mysql': '''
                SELECT * 
                    FROM pathenum 
                    WHERE path LIKE (
                        SELECT concat(path, id, '.', '%%')
                            FROM pathenum
                            WHERE id = :parent
                    )
                '''                
            },
            dict(parent=id)
        )


# ---------------------------------------------------------------------------------------------------------------------------------------------------


class Full(Tree):
    tree_name = 'full'
    tree_base = ['postgresql', 'mysql', 'sqlite', 'oracle', 'db2', 'sqlserver']
    
    def create_table(self):
        tables = self.db.schema_list('table')
        #print tables
        if 'full_data' in tables:
            self.db.ddl({
                'oracle': ['DROP SEQUENCE full_data_id_seq', 'DROP TABLE full_data'],
                '*': 'DROP TABLE full_data',
            })
        if 'full_tree' in tables:
            self.db.execute('DROP TABLE full_tree')
        
        self.db.ddl({
                'sqlite': "CREATE TABLE full_data(id INTEGER PRIMARY KEY AUTOINCREMENT, name varchar(100))",
                'oracle': [
                    'CREATE SEQUENCE full_data_id_seq START WITH 1 INCREMENT BY 1 NOMAXVALUE',
                    'CREATE TABLE full_data(id int, name varchar(100))',
                    ],
                'db2':    "CREATE TABLE full_data(id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY (START WITH 1 INCREMENT BY 1), name varchar(100))", 
                'mssql':  "CREATE TABLE full_data(id int IDENTITY PRIMARY KEY, name varchar(100))",
                '*':      """
                    CREATE TABLE full_data(
                        id   serial PRIMARY KEY, 
                        name varchar(100)
                    )""",
        })
        
        self.db.ddl("""
            CREATE TABLE full_tree(
                top_id    int,
                bottom_id int,
                distance  int
            )"""
        )
        
        #self.db.ddl("CREATE INDEX full_tree_idx_top_id    ON full_tree (top_id)")
        #self.db.ddl("CREATE INDEX full_tree_idx_bottom_id ON full_tree (bottom_id)")


    def insert(self, parent, name):
        #pid = self.db.insert_returning_id('full_data', dict(name=name))
        #""
        #    INSERT INTO simple (parent, name) 
        #        VALUES (:parent, :name)
        #        RETURNING id
        #""
        #
        #self.db.execute(""
        #    INSERT INTO full_tree(top_id, bottom_id, distance)
        #        SELECT top_id, :new, distance + 1
        #            FROM full_tree
        #    
        #    "", 
        #            dict(new=0, bottom_id=pid, distance=row[1] + 1)
        #        )

        # """
        
        pid = self.db.insert_returning_id('full_data', dict(name=name))
        
        if parent is not None:
            for row in self.db.execute_and_fetch('SELECT top_id, distance FROM full_tree WHERE bottom_id = :parent', dict(parent=parent)):
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
        
        return pid
        
        # """
    
    def get_roots(self):
        return self.db.execute_and_fetch("""
            SELECT d.*
                FROM full_data d 
                    JOIN full_tree t 
                        ON (d.id = t.bottom_id) 
                WHERE t.top_id IS NULL AND t.distance = 0
            """
        )
    
    def get_parent(self, id):
        return self.db.execute_and_fetch("""
            SELECT d.*
                FROM full_data d 
                    JOIN full_tree t 
                        ON (d.id = t.top_id) 
                WHERE t.distance = 1 AND t.bottom_id = :id
            """,
            dict(id=id)
        )
    
    def get_ancestors(self, id):
        return self.db.execute_and_fetch("""
            SELECT d.*
                FROM full_data d 
                    JOIN full_tree t 
                        ON (d.id = t.top_id)
                WHERE t.bottom_id = :id AND t.distance >= 0 
                ORDER BY t.distance ASC
            """, 
            dict(id=id)
        )

    def get_children(self, id):
        return self.db.execute_and_fetch("""
            SELECT d.*
                FROM full_data d 
                    JOIN full_tree t 
                        ON (d.id = t.bottom_id) 
                WHERE t.top_id = :id AND t.distance = 1
            """, 
            dict(id=id)
        )

    def get_descendants(self, id):
        return self.db.execute_and_fetch("""
            SELECT d.*
                FROM full_data d 
                    JOIN full_tree t 
                        ON (d.id = t.bottom_id) 
                WHERE t.top_id = :id AND t.distance > 0
            """, 
            dict(id=id)
        )


#####################################################################################################################################################
#####################################################################################################################################################


class With(Simple):
    tree_name = 'with'
    tree_base = ['db2', 'sqlserver', 'postgresql']

    def get_ancestors(self, id):
        # WITH RECURSIVE temptab(node_level, id, parent, name) AS
        return self.db.execute_and_fetch({
            'postgresql': """
                WITH RECURSIVE temptab(node_level, id, parent, name) AS
                (
                    SELECT 0, root.id, root.parent, root.name
                        FROM simple root
                        WHERE root.id = :id
                UNION ALL
                    SELECT t.node_level + 1, s.id, s.parent, s.name
                        FROM simple s, temptab t
                        WHERE s.id = t.parent
                )
                SELECT node_level, id, parent, name FROM temptab
                """,
            '*': """
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
                SELECT node_level, id, parent, name FROM temptab
                """
            
            },
            dict(id=id)
        )

    def get_descendants(self, id):
        # WITH RECURSIVE temptab(level, id, parent, name) AS
        return self.db.execute_and_fetch({
            'postgresql':"""
                WITH RECURSIVE temptab(level, id, parent, name) AS
                (
                    SELECT 0, root.id, root.parent, root.name
                        FROM simple root
                        WHERE root.id = :id
                UNION ALL
                    SELECT t.level + 1, s.id, s.parent, s.name
                        FROM simple s, temptab t
                        WHERE s.parent = t.id
                )
                SELECT level, id, parent, name FROM temptab
                """,
            '*':"""
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
                SELECT level, id, parent, name FROM temptab
                """,
            },
            dict(id=id)
        )


# ---------------------------------------------------------------------------------------------------------------------------------------------------


class ConnectBy(Simple):
    tree_name = 'connectby'
    tree_base = ['oracle']

    def get_ancestors(self, id):
        return self.db.execute_and_fetch("""
            SELECT level, id, parent, name 
                FROM simple 
                START WITH id = :id 
                CONNECT BY id = PRIOR parent
            """, 
            dict(id=id)
        )

    def get_descendants(self, id):
        return self.db.execute_and_fetch("""
            SELECT level, id, parent, name 
                FROM simple 
                START WITH id = :id 
                CONNECT BY parent = PRIOR id
            """, 
            dict(id=id)
        )


# ---------------------------------------------------------------------------------------------------------------------------------------------------


class PlSql(Simple):
    tree_name = 'plsql'
    tree_base = ['postgresql']
    
    
    '''
    
    CREATE TYPE tree_item  IS object (id integer, parent integer, name varchar2(100));
    CREATE TYPE tree_items IS table OF tree_item;
    
    
    
    CREATE OR REPLACE FUNCTION tree_ancestors(start_id integer) RETURN
        tree_items
    IS
        tree_items_list tree_items := tree_items();
        cid integer := start_id;
        tmp simple%ROWTYPE;
    BEGIN
        WHILE cid IS NOT NULL LOOP
            SELECT id, parent, name
                INTO tmp FROM simple WHERE simple.id = cid;
            
            cid := tmp.parent;
            tree_items_list.extend;
            tree_items_list(tree_items_list.last) := tree_item(tmp.id, tmp.parent, tmp.name);
        END LOOP;
        RETURN tree_items_list;
    END;
    
    SELECT * FROM table (tree_ancestors(8));
    

#########################################################


IF EXISTS (
    SELECT 1
    FROM INFORMATION_SCHEMA.ROUTINES
    WHERE
        ROUTINE_NAME = 'tree_ancestors' AND
        ROUTINE_SCHEMA = 'dbo' AND
        ROUTINE_TYPE = 'FUNCTION'
)
BEGIN
    DROP FUNCTION dbo.tree_ancestors
END
GO

CREATE FUNCTION tree_ancestors (@start_id Int)
RETURNS @TreeItemsList TABLE(id Int)
AS
BEGIN
    DECLARE @cid Int = @start_id;
    
    WHILE @cid IS NOT NULL
    BEGIN
        INSERT INTO @TreeItemsList (id)
            SELECT @cid;
        
        SELECT @cid = parent
            FROM simple
            WHERE id = @cid
    END
    RETURN
END
GO


select * from dbo.tree_ancestors(8);









IF EXISTS (
    SELECT 1
    FROM INFORMATION_SCHEMA.ROUTINES
    WHERE
        ROUTINE_NAME = 'tree_ancestors' AND
        ROUTINE_SCHEMA = 'dbo' AND
        ROUTINE_TYPE = 'FUNCTION'
)
BEGIN
    DROP FUNCTION dbo.tree_ancestors
END
GO

CREATE FUNCTION tree_ancestors (@start_id Int)
RETURNS @TreeItemsList TABLE(id Int)
AS
  BEGIN
    DECLARE @cid Int = @start_id;
    
    INSERT INTO @TreeItemsList (ID)
     SELECT @cid;
    
    SELECT @cid = parent
     FROM simple
     WHERE id = @start_id
     
    INSERT INTO @TreeItemsList (ID)
     SELECT @cid;
     
    INSERT INTO @TreeItemsList (ID)
     SELECT parent
     FROM simple
     WHERE id = @start_id
   RETURN
  END
GO


CREATE FUNCTION fnProductListBySubCategory (@SubID Int)
RETURNS @ProdList Table
  (  ID Int
  ,  Name nVarChar(50)
  ,  ListPrice Money
  )
AS
  BEGIN
   IF @SubID IS NULL
    BEGIN
     INSERT INTO @ProdList (ID, Name)
     SELECT ID, First_Name
     FROM Employee
    END
   ELSE
    BEGIN
     INSERT INTO @ProdList (ID, Name)
     SELECT ID, First_Name
     FROM Employee
     WHERE ID = @SubID
    END
   RETURN
  END
GO

    
    '''
    
    
    
    def get_postgresql_ancestors_create(self):
        return """
            CREATE OR REPLACE FUNCTION tree_ancestors(
                start_id int
            ) RETURNS SETOF int AS $$
            DECLARE
                cid int := start_id;
            BEGIN
                WHILE cid IS NOT NULL LOOP
                    RETURN NEXT cid;
                    SELECT parent INTO cid FROM tree WHERE tree.id = cid;
                END LOOP;
            END;
            $$ LANGUAGE plpgsql strict;
        """
        
    def get_postgresql_descendants_create(self):
        return """
            CREATE OR REPLACE FUNCTION tree_descendants(
                start_id int
            ) RETURNS SETOF int AS $$
            DECLARE
                rec RECORD;
                current INT[];
                build INT[];
                tmp INT;
            BEGIN
                build := ARRAY[0];
                current := ARRAY[0, start_id];
                WHILE current > ARRAY[0] LOOP
                    build := ARRAY[0];
                    FOR i IN 2..array_upper(current, 1) LOOP
                        tmp := current[i];
                        FOR rec IN SELECT * FROM tree WHERE parent = tmp LOOP
                            RETURN NEXT rec.id;
                            build := build || rec.id;
                        END LOOP;
                    END LOOP;
                    current := build;
                END LOOP;
            END;
            $$ LANGUAGE plpgsql strict;
        """
        
    def get_postgresql_ancestors(self):
        return """
            SELECT id, parent, value
                FROM tree_ancestors(:id) AS t
                    JOIN tree ON t = tree.id;
        """
        
    def get_postgresql_descendants(self):
        return """
            SELECT id, parent, value
                FROM tree_descendants(:id) AS t 
                    JOIN tree ON t = tree.id;
        """
        
    
    def get_oracle_ancestors_create(self):
        return """
            CREATE TYPE tree_item  IS object (id integer, parent integer, name varchar2(100));
            CREATE TYPE tree_items IS table OF tree_item;
            
            CREATE OR REPLACE FUNCTION tree_ancestors(start_id integer) RETURN
                tree_items
            IS
                tree_items_list tree_items := tree_items();
                cid integer := start_id;
                tmp simple%ROWTYPE;
            BEGIN
                WHILE cid IS NOT NULL LOOP
                    SELECT id, parent, name
                        INTO tmp FROM simple WHERE simple.id = cid;
                    
                    cid := tmp.parent;
                    tree_items_list.extend;
                    tree_items_list(tree_items_list.last) := tree_item(tmp.id, tmp.parent, tmp.name);
                END LOOP;
                RETURN tree_items_list;
            END;
        """
        
    def get_oracle_descendants_create(self):
        return """
            SELECT 1 FROM dual;
        """
        
    def get_oracle_ancestors(self):
        return """
            SELECT * FROM table(tree_ancestors(:id));
        """
        
    def get_oracle_descendants(self):
        return """
            SELECT * FROM table(tree_descendants(:id));
        """
    
    
    def get_sqlserver_ancestors_create(self):
        return """
            CREATE FUNCTION tree_ancestors (@start_id Int)
            RETURNS @TreeItemsList TABLE(id Int)
            AS
            BEGIN
                DECLARE @cid Int = @start_id;
                
                WHILE @cid IS NOT NULL
                BEGIN
                    INSERT INTO @TreeItemsList (id)
                        SELECT @cid;
                    
                    SELECT @cid = parent
                        FROM simple
                        WHERE id = @cid
                END
                RETURN
            END
            GO
        """
        
    def get_sqlserver_descendants_create(self):
        return """
            SELECT 1;
        """
        
    def get_sqlserver_ancestors(self):
        return """
            SELECT * FROM tree_ancestors(:id);
        """
        
    def get_sqlserver_descendants(self):
        return """
            SELECT * FROM tree_descendants(:id);
        """
    
    def __init__(self, db):
        super(PlSql, self).__init__(db)
        
        self.db.ddl({
            'postgresql': [
                self.get_postgresql_ancestors_create(),
                self.get_postgresql_descendants_create(),
            ],
            'oracle': [
                self.get_oracle_ancestors_create(),
                self.get_oracle_descendants_create(),
            ],
            'sqlserver': [
                self.get_sqlserver_ancestors_create(),
                self.get_sqlserver_descendants_create(),
            ],
        })
        
    '''
SELECT * FROM tree_ancestors(111);
SELECT t FROM tree_ancestors(111) AS t;
SELECT count(*) FROM tree_ancestors(111);
SELECT id, parent, value FROM tree_ancestors(111) AS t JOIN tree ON t = tree.id;

SELECT * FROM tree_descendants(1);
SELECT t FROM tree_descendants(1) AS t;
SELECT count(*) FROM tree_descendants(1);
SELECT id, parent, value FROM tree_descendants(1) AS t JOIN tree ON t = tree.id;
  '''


#####################################################################################################################################################
#####################################################################################################################################################


class Ltree(Tree):
    tree_name = 'ltree'
    tree_base = []
    #tree_base = ['postgresql']
    
   
    def create_table(self):
        tables = self.db.schema_list('table')
        if 'ltreetab' in tables:
            self.db.ddl("DROP TABLE ltreetab")

        self.db.ddl("""
            CREATE TABLE ltreetab(
                id   serial PRIMARY KEY, 
                path ltree, 
                name varchar(100)
            )
            """
        )
        
    def insert(self, parent, name):
        """
            INSERT INTO ltreetab (path, name) VALUES (
                text2ltree('' || currval('ltreetab_path_seq')),
                :name
            ) RETURNING id
        """
        if parent is None:
            pid = self.db.execute('''
                INSERT INTO ltreetab (path, name) VALUES (
                    text2ltree('' || currval('ltreetab_id_seq')),
                    :name
                ) RETURNING id
                ''',
                dict(parent=parent, name=name)
            ).fetch_single()
        else:
            pid = self.db.execute('''
                INSERT INTO ltreetab (path, name) VALUES (
                    (SELECT path FROM ltreetab WHERE id = :parent) ||
                        ('' ||currval('ltreetab_id_seq')),
                    :name
                ) RETURNING id
                ''',
                dict(parent=parent, name=name)
            ).fetch_single()
        
        return pid
    
    def get_roots(self):
        return self.db.execute_and_fetch("""
            SELECT *  
                FROM ltreetab 
                WHERE path ~ '*{1}'
            """
        )

    def get_parent(self, id):
        return self.db.execute_and_fetch("""
            SELECT * 
                FROM ltreetab 
                WHERE path = (
                    SELECT subpath(path, 0, -1) 
                        FROM ltreetab 
                        WHERE id = :id
                )
            """, 
            dict(id=id)
        )

    def get_ancestors(self, id):
        return self.db.execute_and_fetch("""
            SELECT * 
                FROM ltreetab 
                WHERE path @> (
                    SELECT path
                        FROM ltreetab
                        WHERE id = :id
                )
            """,
            dict(id=id)
        )

    def get_children(self, id):
        return self.db.execute_and_fetch("""
            SELECT * 
                FROM ltreetab 
                WHERE path ~ ((
                    SELECT ltree2text(path) 
                        FROM ltreetab 
                        WHERE id = :parent
                ) || '.*{1}')::lquery
            """, 
            dict(parent=id)
        )


    def get_descendants(self, id):
        return self.db.execute_and_fetch("""
            SELECT * 
                FROM ltreetab 
                WHERE path <@ (
                    SELECT path
                        FROM ltreetab
                        WHERE id = :parent
                )
            """, 
            dict(parent=id)
        )


# ---------------------------------------------------------------------------------------------------------------------------------------------------


class HierarchyId(Tree):
    tree_name = 'hierarchyid'
    tree_base = []
    #tree_base = ['sqlserver']
    
    def create_table(self):
        if 'herid' in self.db.schema_list('table'):
            self.db.ddl("DROP TABLE herid")
        
        self.db.ddl("""
            CREATE TABLE herid (
                id   int IDENTITY PRIMARY KEY,
                node hierarchyid,
                name varchar(100)
            )
            """
        )
        
        self.db.execute("""
            INSERT INTO herid (node, name) 
                VALUES (hierarchyid::GetRoot(), 'ROOT')
            """
        )

    def insert(self, parent, name):
        ''' http://technet.microsoft.com/en-us/library/bb677212.aspx '''
        if parent is None:
            parent = 1
        
        self.db.execute("""
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
            """,
            dict(parent=parent, name=name)
        )
        pid = self.db.execute('SELECT id FROM herid WHERE id = @@IDENTITY').list()[0][0]
        return pid

    def get_roots(self):
        return self.db.execute_and_fetch("""
            SELECT * 
                FROM herid 
                WHERE node.GetLevel() = 1
            """
        )

    def get_parent(self, id):
        return self.db.execute_and_fetch("""
            SELECT * 
                FROM herid 
                WHERE node = (
                    SELECT node.GetAncestor(1) 
                        FROM herid 
                        WHERE id = :id
                )
            """, 
            dict(id=id)
        )

    #def get_ancestors(self, id):
        #return self.db.execute_and_fetch('''
            #SELECT *
                #FROM herid
                #WHERE (
                    #SELECT node n1 FROM herid WHERE id = :id
                #).IsDescendant(node)
                #''',
            #dict(id=id)
        #)

    def get_ancestors(self, id):
        return self.db.execute_and_fetch("""
            SELECT *
                FROM herid
                WHERE node.IsDescendantOf((SELECT node n1 FROM herid WHERE id = :id))
            """,
            dict(id=id)
        )

    def get_children(self, id):
        return self.db.execute_and_fetch("""
            SELECT * 
                FROM herid 
                WHERE node.GetAncestor(1) = (
                    SELECT node 
                        FROM herid 
                        WHERE id = :parent
                )
            """, 
            dict(parent=id)
        )


    def get_descendants(self, id):
        return self.db.execute_and_fetch("""
            SELECT * 
                FROM herid 
                WHERE node.IsDescendant((
                    SELECT node FROM herid WHERE id = :parent
                ))
            """, 
            dict(parent=id)
        )


