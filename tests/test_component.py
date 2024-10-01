import unittest

from component import Component


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
