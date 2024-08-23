import logging
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import snowflake.connector
from keboola.component import ComponentBase, UserException

# Snowflake database settings
KEY_ACCT = 'account'
KEY_USER = 'username'
KEY_PASS = '#password'
KEY_WRHS = 'warehouse'

# Historize Tables
KEY_DB = 'database'
KEY_SCHEMA = 'schema'
KEY_QUERY = 'query'

MANDATORY_PARAMETERS = [KEY_ACCT, KEY_USER, KEY_PASS, KEY_WRHS, KEY_QUERY]

KEY_RUNID = 'KBC_RUNID'

# configuration variables
KEY_DEBUG = 'debug'

# list of mandatory parameters => if some is missing, component will fail with readable message on initialization.

APP_VERSION = '0.0.3'
sys.tracebacklimit = 0


@dataclass
class SnowflakeCredentials:
    host: str
    warehouse: str
    username: str
    password: str
    database: str
    schema: str
    cursor: snowflake.connector.cursor = snowflake.connector.DictCursor


@dataclass
class KBCEnvironment:
    run_id: str


@dataclass
class Parameters:
    query: str


class Component(ComponentBase):

    def __init__(self):
        default_data_dir = Path(__file__).resolve().parent.parent.joinpath('data').as_posix() \
            if not os.environ.get('KBC_DATADIR') else None

        logging.info(f'Running version {APP_VERSION}...')
        super().__init__(data_folder_path=default_data_dir)
        logging.getLogger('snowflake.connector').setLevel(logging.WARNING)

        if self.configuration.parameters.get(KEY_DEBUG, False) is True:
            logging.getLogger().setLevel(logging.DEBUG)
            logging.getLogger('snowflake.connector').setLevel(logging.DEBUG)
            sys.tracebacklimit = 3

        try:
            # validation of mandatory parameters. Produces ValueError
            self.validate_configuration(MANDATORY_PARAMETERS)
            self.parameters = Parameters(self.configuration.parameters.get(KEY_QUERY))
        except ValueError as e:
            logging.exception(e)
            exit(1)

        self.kbc = KBCEnvironment(os.environ.get(KEY_RUNID, '@@@123'))
        self.snfk = SnowflakeCredentials(self.configuration.parameters[KEY_ACCT],
                                         self.configuration.parameters[KEY_WRHS],
                                         self.configuration.parameters[KEY_USER],
                                         self.configuration.parameters[KEY_PASS],
                                         self.configuration.parameters.get(KEY_DB)
                                         if self.configuration.parameters.get(KEY_DB) != '' else None,
                                         self.configuration.parameters.get(KEY_SCHEMA)
                                         if self.configuration.parameters.get(KEY_SCHEMA) != '' else None,
                                         snowflake.connector.DictCursor)

    def _log_query(self, query):
        logging.info(f"Running query: {query}")

    def create_snfk_connection(self):

        self.snfk_conn = snowflake.connector.connect(user=self.snfk.username, password=self.snfk.password,
                                                     account=self.snfk.host,
                                                     database=self.snfk.database,
                                                     warehouse=self.snfk.warehouse,
                                                     session_parameters={
                                                         'QUERY_TAG': f'{{"runId":"{self.kbc.run_id}"}}'
                                                     })

    @staticmethod
    def split_sql_queries(sql_string):
        # Regular expression to split by semicolons not inside quotes
        queries = re.split(r';(?=(?:[^\'"]|\'[^\']*\'|"[^"]*")*$)', sql_string)
        queries = [query.strip() for query in queries if query.strip()]
        return queries

    def run(self):

        self.create_snfk_connection()

        with self.snfk_conn:
            with self.snfk_conn.cursor(self.snfk.cursor) as snfk_cursor:
                if self.snfk.schema is not None:
                    use_schema_sql = f'USE SCHEMA "{self.snfk.schema}";'
                    self._log_query(use_schema_sql)
                    snfk_cursor.execute(use_schema_sql)

                for query in self.split_sql_queries(self.parameters.query):
                    query = query.strip()
                    if query == '':
                        continue
                    query = query + ';'
                    self._log_query(query)
                    snfk_cursor.execute(query)


if __name__ == "__main__":
    try:
        comp = Component()
        comp.execute_action()
    except UserException as exc:
        logging.exception(exc)
        exit(1)
    except Exception as exc:
        logging.exception(exc)
        exit(2)
