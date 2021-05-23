import os
from dotenv import load_dotenv
import mysql.connector
load_dotenv()


class DB:

    def __init__(self, filename):
        load_dotenv()
        self.conn = None
        self.cursor = None
        self.create_connection(filename)

    def create_connection(self, filename):
        """ create a database connection to the SQLite database

                specified by the db_file
            :param filename: database filename ( without file extension )
        """
        try:
            self.conn = mysql.connector.connect(
                host=os.getenv('MSQL_HOST'),
                user=os.getenv('MSQL_USER'),
                password=os.getenv('MSQL_PW'),
                database=(os.getenv('MSQL_DB'))
            )
            self.cursor = self.conn.cursor(buffered=True)
        except Exception as e:
            print(e)

    def last_row_id(self):
        return self.cursor.lastrowid

    def create_table(self, create_table_sql):
        """ create a table from the create_table_sql statement

        :param create_table_sql: a CREATE TABLE statement
        :return:
        """
        try:
            self.cursor.execute(create_table_sql)
        except Exception as e:
            print(e)

    def execute_statement(self, statement, parameters=''):
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
            return True, ret
        except Exception as err:
            if 'UNIQUE' not in str(err):
                return False, err
            return False, err
