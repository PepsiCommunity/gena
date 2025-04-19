import re
from typing import Union


def parse_docstring(doc_string: Union[str, None]) -> dict[str, dict]:
    # 0 - description
    # 1 - args
    # 2 - returns
    state = 0
    description = ""
    args = {}

    for line in doc_string.splitlines():
        if 'args' in line.strip().lower():
            state = 1
            continue

        if 'Returns' in line.strip().lower():
            state = 2
            continue

        match state:
            case 0:
                description += line.strip() + ' '
            case 1:
                splitted = line.split(':')
                if len(splitted) != 2:
                    continue

                pattern = re.compile(
                    r'\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\(([^()]*)\)\s*'
                )
                match = pattern.findall(
                    splitted[0].strip())
                if not match:
                    continue

                name, data_type = match[0]
                args[name] = {
                    "type": data_type.strip(),
                    "description": splitted[1].strip()
                }

    return description.strip(), args


def build_tool(func) -> dict:
    description, args = parse_docstring(func.__doc__)
    return f'Function name: {func.__name__}\nDescription: {description}\nArgs: {args}'
