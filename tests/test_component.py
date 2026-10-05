import unittest
from unittest import mock

from keboola.component.exceptions import UserException
from keboola.component.sync_actions import MessageType

from component import Component, KBCEnvironment, SnowflakeCredentials


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
