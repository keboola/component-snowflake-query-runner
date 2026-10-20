import json
import os
import tempfile
import unittest
from unittest import mock

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from keboola.component.exceptions import UserException
from keboola.component.sync_actions import MessageType

from component import Component, KBCEnvironment, SnowflakeCredentials


def _private_key_pem():
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    return key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")


def _component_from_parameters(**credentials):
    # runs the real __init__, unlike _component_with_credentials
    parameters = {"account": "account", "warehouse": "warehouse", "username": "user", **credentials}
    with tempfile.TemporaryDirectory() as data_dir:
        with open(os.path.join(data_dir, "config.json"), "w") as config_file:
            json.dump({"parameters": parameters}, config_file)
        with mock.patch.dict(os.environ, {"KBC_DATADIR": data_dir}):
            return Component()


def _component_with_credentials(auth_type, password=None, private_key=None):
    # bypass ComponentBase.__init__, which needs a data folder
    comp = Component.__new__(Component)
    comp.kbc = KBCEnvironment("123")
    comp.snfk = SnowflakeCredentials(
        auth_type=auth_type,
        host="account",
        warehouse="warehouse",
        username="user",
        password=password,
        private_key=private_key,
        private_key_passphrase=None,
        database=None,
        schema=None,
    )
    return comp


class TestSnowflakeConnection(unittest.TestCase):

    @mock.patch("component.snowflake.connector.connect")
    def test_key_pair_without_private_key_and_password_raises_user_exception(self, connect):
        comp = _component_with_credentials("key_pair")
        with self.assertRaisesRegex(UserException, "no private key is set"):
            comp.create_snfk_connection()
        connect.assert_not_called()

    @mock.patch("component.snowflake.connector.connect")
    def test_key_pair_without_private_key_falls_back_to_password_with_warning(self, connect):
        comp = _component_with_credentials("key_pair", password="secret")
        with self.assertLogs(level="WARNING") as logs:
            comp.create_snfk_connection()
        self.assertIn("Falling back to password authentication", logs.output[0])
        self.assertEqual(connect.call_args.kwargs["password"], "secret")

    @mock.patch("component.snowflake.connector.connect")
    def test_password_auth_does_not_warn(self, connect):
        comp = _component_with_credentials("password", password="secret")
        with self.assertNoLogs(level="WARNING"):
            comp.create_snfk_connection()
        self.assertEqual(connect.call_args.kwargs["password"], "secret")

    @mock.patch("component.snowflake.connector.connect")
    def test_test_connection_returns_missing_key_message(self, connect):
        comp = _component_with_credentials("key_pair")
        result = Component.test_connection.__wrapped__(comp)
        self.assertEqual(result.type, MessageType.WARNING)
        self.assertTrue(result.message.startswith("Key Pair authentication is selected"))
        connect.assert_not_called()

    @mock.patch("component.snowflake.connector.connect")
    def test_key_pair_with_leftover_password_signs_in_with_private_key(self, connect):
        comp = _component_from_parameters(
            auth_type="key_pair", **{"#password": "leftover", "#private_key": _private_key_pem()}
        )
        comp.create_snfk_connection()
        self.assertIn("private_key", connect.call_args.kwargs)
        self.assertNotIn("password", connect.call_args.kwargs)

    @mock.patch("component.snowflake.connector.connect")
    def test_password_auth_with_leftover_private_key_signs_in_with_password(self, connect):
        comp = _component_from_parameters(
            auth_type="password", **{"#password": "secret", "#private_key": "leftover"}
        )
        comp.create_snfk_connection()
        self.assertEqual(connect.call_args.kwargs["password"], "secret")
        self.assertNotIn("private_key", connect.call_args.kwargs)


class TestComponent(unittest.TestCase):

    def test_split_sql_queries_empty_string_returns_empty_list(self):
        sql_string = ""
        expected = []
        result = Component.split_sql_queries(sql_string)
        self.assertEqual(result, expected)

    def test_split_sql_queries_single_query(self):
        sql_string = "SELECT * FROM table1"
        expected = ["SELECT * FROM table1"]
        result = Component.split_sql_queries(sql_string)
        self.assertEqual(result, expected)

    def test_split_sql_queries_multiple_queries(self):
        sql_string = "SELECT * FROM table1; SELECT * FROM table2; SELECT * FROM table3;"
        expected = ["SELECT * FROM table1;", "SELECT * FROM table2;", "SELECT * FROM table3;"]
        result = Component.split_sql_queries(sql_string)
        self.assertEqual(result, expected)

    def test_split_sql_queries_with_semicolon_in_quotes(self):
        sql_string = "SELECT * FROM table1; SELECT ';'; SELECT * FROM table3;"
        expected = ["SELECT * FROM table1;", "SELECT ';';", "SELECT * FROM table3;"]
        result = Component.split_sql_queries(sql_string)
        self.assertEqual(result, expected)

    def test_split_sql_queries_with_empty_queries(self):
        sql_string = "SELECT * FROM table1; SELECT * FROM table2;"
        expected = ["SELECT * FROM table1;", "SELECT * FROM table2;"]
        result = Component.split_sql_queries(sql_string)
        self.assertEqual(result, expected)

    def test_split_sql_queries_with_comments(self):
        sql_string = '''/*
 Some ;comment; here
 */

// some inline comment; here
SELECT * FROM table1; SELECT * FROM table2;
'''
        expected = ['/*\n Some ;comment; here\n */\n\n// some inline comment; here\nSELECT * FROM table1;',
                    'SELECT * FROM table2;']
        result = Component.split_sql_queries(sql_string)
        self.assertEqual(result, expected)


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
