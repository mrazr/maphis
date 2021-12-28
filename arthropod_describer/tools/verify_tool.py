import inspect
from typing import Tuple, List

from arthropod_describer.tools.tool import Tool

required_methods = [(name, method) for name, method in inspect.getmembers(Tool, inspect.isfunction) if not name.endswith('_')]
required_methods = [(name, inspect.signature(memb)) for name, memb in required_methods]

required_properties = [(name, inspect.signature(prop.fget)) for name, prop in inspect.getmembers(Tool, lambda o: isinstance(o, property))]


class VerificationResult:
    def __init__(self):
        self.missing_methods: List[Tuple[str, inspect.Signature]] = []
        self.missing_props: List[Tuple[str, inspect.Signature]] = []

        self.incorrect_methods: List[Tuple[str, inspect.Signature, inspect.Signature]] = []
        self.incorrect_props: List[Tuple[str, inspect.Signature, inspect.Signature]] = []

        self.success: bool = True


def verify_tool(tool) -> VerificationResult:
    tool_methods = {name: inspect.signature(memb) for name, memb in inspect.getmembers(tool, inspect.isfunction) if not name.startswith('_')}
    tool_props = {name: inspect.signature(prop.fget) for name, prop in inspect.getmembers(tool, lambda o: isinstance(o, property))}

    result = VerificationResult()

    for name, req_prop in required_properties:
        if name not in tool_props:
            result.missing_props.append((name, req_prop))
            result.success = False
            continue
        #if tool_props[name] != req_prop:
        #    result.incorrect_props.append((name, req_prop, tool_props[name]))
        #    result.success = False

    for name, req_sig in required_methods:
        if name not in tool_methods:
            result.missing_methods.append((name, req_sig))
            result.success = False
            continue
        #if tool_methods[name] != req_sig:
        #    result.incorrect_methods.append((name, req_sig, tool_methods[name]))
        #    result.success = False

    return result


def print_result(result: VerificationResult, name: str=''):
    if not result.success:
        if name == '':
            print('Not a valid tool:')
        else:
            print(f'{name} is not a valid tool')

        for prop_name, prop in result.missing_props:
            print(f'Missing property "{prop_name}" {prop}')

        for method_name, method in result.missing_methods:
            print(f'Missing property "{method_name}" {method}')

        for prop_name, correct_prop, incorrect_prop in result.incorrect_props:
            print(f'Incorrect property "{prop_name}" required = {correct_prop}, given = {incorrect_prop}')

        for method_name, correct_method, incorrect_method in result.incorrect_methods:
            print(f'Incorrect method "{method_name}" required = {correct_method}, given = {incorrect_method}')
