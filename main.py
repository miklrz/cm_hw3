import toml
import sys
import argparse
import re
from collections import deque
from typing import Any, Dict, List, Tuple

OPERATORS = {
    '+': lambda x, y: x + y,
    '-': lambda x, y: x - y,
    '*': lambda x, y: x * y,
    '/': lambda x, y: x / y,
    'min': lambda x, y: x if x < y else y
}

NAME_REGEX = r'^[_A-Z][_a-zA-Z0-9]*$'


def parse_arguments():
    parser = argparse.ArgumentParser(description="Конвертер TOML в учебный конфигурационный язык.")
    parser.add_argument("input", help="Путь к входному файлу.")
    parser.add_argument("output", help="Путь к выходному файлу.")
    return parser.parse_args()


def load_toml(file_path: str) -> Tuple[Dict[str, Any], List[Tuple[int, str]]]:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = f.read()
        data, comments = remove_comments(data)
        data_dict = toml.loads(data)
        return data_dict, comments
    except toml.TomlDecodeError as e:
        sys.stderr.write("Ошибка синтаксиса TOML: " + str(e) + "\n")
        sys.exit(1)
    except IOError as e:
        sys.stderr.write("Ошибка чтения файла: " + str(e) + "\n")
        sys.exit(1)

def remove_comments(data: str) -> Tuple[str, List[Tuple[int, str]]]:
    """
    Удаляет многострочные комментарии из данных и возвращает их вместе с их строками.
    Многострочные комментарии имеют формат {{! ... }}.
    """
    lines = data.splitlines()
    cleaned_lines = []
    comments = []
    inside_comment = False
    comment_buffer = []
    comment_start_line = None

    for line_number, line in enumerate(lines):
        if "{{!" in line:
            inside_comment = True
            comment_start_line = line_number
            comment_buffer.append(line)
            continue
        elif "}}" in line and inside_comment:
            inside_comment = False
            comment_buffer.append(line)
            # Сохраняем весь комментарий как одну запись
            comments.append((comment_start_line, " ".join(comment_buffer).strip()))
            comment_buffer = []
            continue

        if inside_comment:
            comment_buffer.append(line)
        else:
            cleaned_lines.append(line)

    return '\n'.join(cleaned_lines), comments

def validate_name(name: str):
    if not re.match(NAME_REGEX, name):
        raise ValueError(f"Некорректное имя '{name}'")


def format_list(array: List[Any]) -> str:
    return "(list " + " ".join(map(str, array)) + ")"

def format_table(value: Dict[str, Any]) -> str:
    formatted_items = [f"{k} = {v}" for k, v in value.items()]
    return "table([" + ", ".join(formatted_items) + "])"

def evaluate_infix(expression: str, constants: Dict[str, Any]) -> Any:
    """Оценка инфиксного выражения (простая версия)"""
    stack = deque()
    tokens = expression.split()
    for token in tokens:
        if token.isdigit():  # Если токен число
            stack.append(int(token))
        elif token in constants:  # Если токен это имя
            stack.append(constants[token])
        elif token in OPERATORS:  # Если это операция
            b = stack.pop()
            a = stack.pop()
            result = OPERATORS[token](a, b)
            stack.append(result)
        else:
            raise ValueError(f"Неизвестный токен '{token}'")
    return stack.pop()

def process_data(data: Dict[str, Any], constants: Dict[str, Any], comments: List[Tuple[int, str]]) -> List[str]:
    output_lines = []

    # Словарь для сопоставления строковых номеров с комментариями
    comment_dict = {line_number: comment for line_number, comment in comments}

    for key, value in data.items():
        validate_name(key)
        output_line = ""

        if isinstance(value, (int, float)):  # Простое значение
            output_line = f"{value} -> {key}"
            constants[key] = value
        elif isinstance(value, list):  # Массив
            output_line = f"{format_list(value)} -> {key}"
        elif isinstance(value, dict):  # Словарь
            output_line = f"{format_table(value)} -> {key}"
        elif isinstance(value, str) and value.startswith("|") and value.endswith("|"):  # Постфиксное выражение
            expression = value[1:-1].strip()  # Убираем '|' с концов
            try:
                result = evaluate_infix(expression, constants)
                output_line = f"{result} -> {expression}"
                constants[key] = result
            except ValueError as e:
                raise ValueError(f"Ошибка в выражении для '{key}': {e}")
        else:
            raise ValueError(f"Некорректный формат для '{key}'")

        output_lines.append(output_line)

        # Добавляем комментарий, если есть соответствующий
        current_index = len(output_lines) - 1  # Индекс текущей строки вывода
        if current_index in comment_dict:
            output_lines[-1] += f"   {{! {comment_dict[current_index]} !}}"

    return output_lines


def main():
    args = parse_arguments()
    data, comments = load_toml(args.input)
    constants = {}

    try:
        output_lines = process_data(data, constants, comments)
    except ValueError as e:
        sys.stderr.write("Ошибка обработки данных: " + str(e) + "\n")
        sys.exit(1)

    try:
        with open(args.output, 'w', encoding='utf-8') as f:
            for line in output_lines:
                f.write(f"{line}\n")
    except IOError as e:
        sys.stderr.write("Ошибка записи в файл: " + str(e) + "\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
