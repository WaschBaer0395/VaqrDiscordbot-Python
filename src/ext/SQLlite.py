import os
import sqlite3
import traceback
from sqlite3 import Error


class SqlLite():

    def __init__(self, filename):
        self.conn = None
        self.cursor = None
        self.create_connection(filename)

    def create_connection(self, filename):
        """ create a database connection to the SQLite database
                specified by the db_file
            :param filename: database filename ( without file extension )
        """
        self.conn = None
        path = os.getcwd() + '/src/data/' + filename + '.sqlite'
        try:
            self.conn = sqlite3.connect(path)
        except Error as e:
            print(e)

    def create_table(self, create_table_sql):
        """ create a table from the create_table_sql statement
        :param create_table_sql: a CREATE TABLE statement
        :return:
        """
        try:
            self.cursor = self.conn.cursor()
            self.cursor.execute(create_table_sql)
        except Error as e:
            print(e)

    def execute_statement(self, statement, parameters):
        """
        Create a new project into the projects table
        :param statement: statement to be executed
        :param parameters: parameters for statement
        :return: touple(bool,rows,err)
            Where
            bool: True when successfull execution
            rows: return of the statement
            err: exception being caught
        """
        try:
            self.cursor.execute(statement, parameters)
            self.conn.commit()
            ret = self.cursor.fetchall()
            return True, ret, None
        except Error as err:
            if 'UNIQUE' not in str(err):
                return False, err
            return False, err
