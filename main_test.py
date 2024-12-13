import unittest
from main import (
    remove_comments,
    validate_name,
    format_list,
    format_table,
    evaluate_infix,
    process_data
)
from collections import deque

class TestTomlConverter(unittest.TestCase):
    def test_remove_comments(self):
        data = """Key1 = 10
{{! 
This is a comment 
}}
Key2 = 20"""
        expected_cleaned = "Key1 = 10\nKey2 = 20"
        expected_comments = [(1, """{{!  This is a comment  }}""")]
        cleaned_data, comments = remove_comments(data)
        self.assertEqual(cleaned_data, expected_cleaned)
        self.assertEqual(comments, expected_comments)

    def test_validate_name(self):
        validate_name("_VALID_NAME")  # Should not raise
        with self.assertRaises(ValueError):
            validate_name("1Invalid")
        with self.assertRaises(ValueError):
            validate_name("Invalid-Name")

    def test_format_list(self):
        array = [1, 2, 3]
        expected = "(list 1 2 3)"
        self.assertEqual(format_list(array), expected)

    def test_format_table(self):
        value = {"Key1": 10, "Key2": 20}
        expected = "table([\nKey1 = 10, \nKey2 = 20\n])"
        self.assertEqual(format_table(value), expected)

    def test_evaluate_infix(self):
        constants = {"a": 10, "b": 5}
        expression = "a b +"
        result = evaluate_infix(expression, constants)
        self.assertEqual(result, 15)

        expression = "a b *"
        result = evaluate_infix(expression, constants)
        self.assertEqual(result, 50)

        expression = "a b -"
        result = evaluate_infix(expression, constants)
        self.assertEqual(result, 5)

        with self.assertRaises(ValueError):
            evaluate_infix("a b %", constants)  # Unsupported operator

    def test_process_data(self):
        data = {
            "Key1": 10,
            "Key2": 20,
            "Key3": [1, 2, 3],
            "Key4": "|Key1 Key2 +|"
        }
        constants = {}
        comments = []
        result = process_data(data, constants, comments)
        expected_result = [
            "10 -> Key1",
            "20 -> Key2",
            "(list 1 2 3) -> Key3",
            "30 -> Key1 Key2 +"
        ]
        self.assertEqual(result, expected_result)

if __name__ == "__main__":
    unittest.main()
