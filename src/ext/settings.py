import os
import psycopg2
from dotenv import load_dotenv
load_dotenv()


class Settings:

    def __init__(self, filename):
        load_dotenv()
        self.filename = filename
        self.conn = None
        self.cursor = None

    def __create_connection(self, filename):
        """ create a database connection to the SQLite database

                specified by the db_file
            :param filename: database filename ( without file extension )
        """
        try:
            self.conn = psycopg2.connect(os.getenv('POSTGRES_URL'), sslmode='require')
            self.cursor = self.conn.cursor(buffered=True)
            self.cursor.execute('''CREATE TABLE IF NOT EXISTS settings( 
                                        category VARCHAR(255) NOT NULL PRIMARY KEY,
                                        key VARCHAR(255) NOT NULL,
                                        value VARCHAR(255) NOT NULL);
                                        ''')
        except Exception as e:
            print(e)

    def last_row_id(self):
        return self.cursor.lastrowid

    def insert(self):
        self.__create_connection(self.filename)
        print('insert')
        self.conn.colose()

    def get(self, category, key=None):
        self.__create_connection(self.filename)
        if category is None:
            statement = '''SELECT * FROM settings WHERE category = ?'''
            args = (str(category),)
        else:
            statement = '''SELECT * FROM SETTINGS WHERE category = ? and key = ?'''
            args = (str(category), str(key),)

        _, ret = self.__execute_statement(statement, args)
        self.conn.colose()
        if ret is None:
            return dict()
        return ret

    def update(self):
        self.__create_connection(self.filename)
        print('update')
        self.conn.colose()

    def __execute_statement(self, statement, parameters=None):
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
            if parameters is None:
                parameters = ''
            self.cursor.execute(statement, parameters)
            self.conn.commit()
            ret = self.cursor.fetchall()
            return True, ret
        except Exception as err:
            if 'UNIQUE' not in str(err):
                return False, err
            return False, err
