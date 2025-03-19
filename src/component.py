import logging
import os
import re
import sys
from dataclasses import dataclass
from cryptography.hazmat.primitives import serialization

import snowflake.connector
from keboola.component.base import ComponentBase, sync_action
from keboola.component.exceptions import UserException
from keboola.component.sync_actions import ValidationResult, MessageType

# Snowflake database settings
KEY_AUTH_TYPE = 'auth_type'
KEY_ACCT = 'account'
KEY_USER = 'username'
KEY_PASS = '#password'
KEY_WRHS = 'warehouse'
KEY_PRIVATE_KEY = '#private_key'
KEY_PRIVATE_KEY_PASS = '#private_key_passphrase'

# Historize Tables
KEY_DB = 'database'
KEY_SCHEMA = 'schema'
KEY_QUERY = 'query'

MANDATORY_PARAMETERS = [KEY_ACCT, KEY_USER, KEY_WRHS, KEY_QUERY]

KEY_RUNID = 'KBC_RUNID'

# configuration variables
KEY_DEBUG = 'debug'

# list of mandatory parameters => if some is missing, component will fail with readable message on initialization.

APP_VERSION = '0.0.3'
sys.tracebacklimit = 0


@dataclass
class SnowflakeCredentials:
    auth_type: str
    host: str
    warehouse: str
    username: str
    password: str
    private_key: str
    private_key_passphrase: str
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
        super().__init__()
        logging.getLogger('snowflake.connector').setLevel(logging.WARNING)

        self.kbc = KBCEnvironment(os.environ.get(KEY_RUNID, '@@@123'))
        self.snfk = SnowflakeCredentials(self.configuration.parameters[KEY_AUTH_TYPE],
                                         self.configuration.parameters[KEY_ACCT],
                                         self.configuration.parameters[KEY_WRHS],
                                         self.configuration.parameters[KEY_USER],
                                         self.configuration.parameters.get(KEY_PASS)
                                         if self.configuration.parameters.get(KEY_PASS) != '' else None,
                                         self.configuration.parameters.get(KEY_PRIVATE_KEY)
                                         if self.configuration.parameters.get(KEY_PRIVATE_KEY) != '' else None,
                                         self.configuration.parameters.get(KEY_PRIVATE_KEY_PASS)
                                         if self.configuration.parameters.get(KEY_PRIVATE_KEY_PASS) != '' else None,
                                         self.configuration.parameters.get(KEY_DB)
                                         if self.configuration.parameters.get(KEY_DB) != '' else None,
                                         self.configuration.parameters.get(KEY_SCHEMA)
                                         if self.configuration.parameters.get(KEY_SCHEMA) != '' else None,
                                         snowflake.connector.DictCursor)

        if self.snfk.password and self.snfk.private_key:
            raise UserException("Only one of password and private key can be set.")

    def _log_query(self, query):
        logging.info(f"Running query: {query}")

    def create_snfk_connection(self):

        if self.snfk.auth_type != 'key_pair':
            self.snfk_conn = snowflake.connector.connect(user=self.snfk.username, password=self.snfk.password,
                                                         account=self.snfk.host,
                                                         database=self.snfk.database,
                                                         warehouse=self.snfk.warehouse,
                                                         session_parameters={
                                                             'QUERY_TAG': f'{{"runId":"{self.kbc.run_id}"}}'
                                                         })
        else:
            private_key_pem = self.snfk.private_key.encode('utf-8')
            passphrase = self.snfk.private_key_passphrase
            password = passphrase.encode('utf-8') if passphrase is not None else None
            private_key = serialization.load_pem_private_key(private_key_pem, password=password)
            private_key_der = private_key.private_bytes(
                encoding=serialization.Encoding.DER,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
            self.snfk_conn = snowflake.connector.connect(user=self.snfk.username,
                                                         account=self.snfk.host,
                                                         warehouse=self.snfk.warehouse,
                                                         private_key=private_key_der,
                                                         database=self.snfk.database,
                                                         session_parameters={
                                                             'QUERY_TAG': f'{{"runId":"{self.kbc.run_id}"}}'
                                                         })

    @staticmethod
    def split_sql_queries(sql_string):
        # taken from Keboola TR UI
        pattern = (r"\s*((?:'[^'\\]*(?:\\.[^'\\]*)*'|\"[^\"\\]*(?:\\.[^\"\\]*)*\"|\$\$(?:.|\n|\r)*?\$\$|\/\*[^*]*\*+"
                   r"(?:[^*/][^*]*\*+)*\/|#.*|--.*|\/\/.*|[^\"';#])+(?:;|$))")
        queries = re.split(pattern, sql_string)
        queries = [query.strip() for query in queries if query.strip()]
        return queries

    @sync_action("testConnection")
    def test_connection(self):
        try:
            self.create_snfk_connection()
            self.snfk_conn.close()
            return ValidationResult("Connection successful.", MessageType.SUCCESS)

        except snowflake.connector.errors.Error as e:
            return ValidationResult(f"Connection failed: {e}", MessageType.WARNING)

        except Exception as e:
            return ValidationResult(f"Unexpected error: {e}", MessageType.WARNING)

    def run(self):
        try:
            # validation of mandatory parameters. Produces ValueError
            self.validate_configuration_parameters(MANDATORY_PARAMETERS)
            self.parameters = Parameters(self.configuration.parameters.get(KEY_QUERY))
        except ValueError as e:
            raise UserException(e)

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
                    self._log_query(query)
                    snfk_cursor.execute(query)


if __name__ == "__main__":
    try:
        comp = Component()
        comp.execute_action()
    except (UserException, snowflake.connector.errors.DatabaseError) as exc:
        logging.exception(exc)
        exit(1)
    except Exception as exc:
        logging.exception(exc)
        exit(2)
