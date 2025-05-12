from typing_extensions import TypedDict, List
from modules.db_config import db
from dotenv import load_dotenv
from typing import Annotated
from modules.llm_config import llm
from bson import ObjectId
import importlib
import textwrap
import inspect
import astor
import json
import ast
import os
import re

load_dotenv()

def parse_code(file_content):
    class FunctionCollector(ast.NodeTransformer):
        def __init__(self):
            self.func_defs = []
            self.top_level_calls = []

        def visit_FunctionDef(self, node):
            self.func_defs.append(node)
            return None

        def visit_If(self, node):
            if (isinstance(node.test, ast.Compare)
                and isinstance(node.test.left, ast.Name) and node.test.left.id == '__name__'):
                self.top_level_calls.extend(node.body)
            return None

    tree = ast.parse(file_content)
    collector = FunctionCollector()
    collector.visit(tree)
    
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(f"import {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                imports.append(f"from {node.module} import {alias.name}")

    input_args = set()
    for stmt in collector.top_level_calls:
        for node in ast.walk(stmt):
            if isinstance(node, ast.Call):
                for arg in node.args:
                    if isinstance(arg, ast.Name): 
                        input_args.add(arg.id)
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        input_args.add(target.id)

    input_args = list(input_args)
    if collector.top_level_calls:
        last_stmt = collector.top_level_calls[-1]
        if isinstance(last_stmt, ast.Expr):
            collector.top_level_calls[-1] = ast.Return(value=last_stmt.value)
        elif isinstance(last_stmt, ast.Assign):
            target = last_stmt.targets[0]
            if isinstance(target, ast.Name):
                collector.top_level_calls.append(ast.Return(value=ast.Name(id=target.id, ctx=ast.Load())))
    
    main_func = ast.FunctionDef(
        name="some_function",
        args=ast.arguments(
            args=[ast.arg(arg=name) for name in input_args],
            vararg=None, kwarg=None, defaults=[],
            posonlyargs=[], kwonlyargs=[], kw_defaults=[]
        ),
        body=collector.func_defs + collector.top_level_calls,
        decorator_list=[]
    )

    new_module = ast.Module(body=[main_func], type_ignores=[])

    unified_function = astor.to_source(new_module)

    tree = ast.parse(unified_function)
    params = []

    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            func_name = node.name
            args = [arg.arg for arg in node.args.args]
            if node.args.vararg:
                args.append(node.args.vararg.arg)
            if node.args.kwarg:
                args.append(node.args.kwarg.arg)
            params.append(args)

    function_parameters = params[0]

    return imports, function_parameters, unified_function

def tool_creation():
    tools_collection = db['tools']
    print("""\n
Sample Code Structure to Successfully Build a Tool
-------------------------------------------------------------------------------
    # Valid Imports
    import os
    import re

    def fn1(param1):
        '''Performs an operation using param1 and calls fn2.'''
        fn2('value1', 'value2')
        return 'result_from_fn1'

    def fn2(param1, param2):
        '''Processes two parameters and returns a result.'''
        return 'result_from_fn2'

    def fn3(number):
        '''Initiates the process by calling fn1.'''
        fn1('value_for_fn1')
        return 'result_from_fn3'

    
    if __name__ == "__main__":
        number = input("Enter a number: ")
        fn3(number)  # This is the main function that initiates the workflow.
    # No further code should be placed below this line.
-------------------------------------------------------------------------------\n\n
""")

    tool_name = input("\nEnter Tool Name: ")
    tool_description = input("Enter Tool Description: ")
    file_path = input("Enter Absolute File Path for the code you want to use as a tool: ")

    normalized_path = os.path.normpath(file_path)
    with open(normalized_path, 'r', encoding='utf-8') as file:
        file_content = file.read()

    imports, function_parameters, unified_function = parse_code(file_content)

    details = {
        "imports": imports,
        "tool_name": tool_name,
        "tool_description": tool_description,
        "code": unified_function,
        "function_parameters": function_parameters,
    }

    class FuncParams(TypedDict):
        name: Annotated[str, ..., "Function Parameter Name"]
        type: Annotated[str, ..., "Function Parameter Type"]
        description: Annotated[str, ..., "Function Parameter Description"]
    
    class Router(TypedDict):
        func_params: Annotated[List[FuncParams], ..., "List of Function Parameters"]
    
    system_prompt = """
        Given tool code and other relevant details, your task is to simply assign a valid PYTHON data type and description to the GIVEN function parameters only.
        The code and other given detaiils are for your context only.
        
        Tool Details:
    """ + json.dumps(details)

    llm_respone = llm.with_structured_output(Router).invoke(system_prompt)
    func_params = llm_respone["func_params"]

    tool_name = re.sub(r'[^\w\s]', '', tool_name)
    tool_name = re.sub(r'\s+', ' ', tool_name)

    function_name = tool_name.replace(" ", "_")
    class_name = tool_name.title().replace(" ", "")

    function_params = {item["name"]: item["description"] for item in func_params}
    
    additional_desc = "\nArgs:\n"
    for key, val in function_params.items():
        additional_desc += f"\t{key}: {val}\n"
    tool_description += additional_desc

    import_lines = "\n".join(imports)
    func_params_code = "self"
    if len(func_params) > 0:
        func_params_code += ", " + ", ".join([f"{item['name']}: {item['type']}" for item in func_params])
    
    function_code = re.sub(r'some_function\s*\([^()]*\)', f"_run({func_params_code})", unified_function)
    function_code = re.sub(r'^\s*.*input\(.*\).*$', '', function_code, flags=re.MULTILINE)
    function_code = textwrap.indent(function_code, '\t')

    template = '''
from langchain_core.tools import BaseTool
from typing import Type, Optional
{import_lines}
class {class_name}(BaseTool):
\tname: str = "{function_name}"
\tdescription: str = \"\"\"{tool_description}\"\"\"

{function_code}
'''

    final_code = template.format(
        import_lines=import_lines,
        class_name=class_name,
        function_name=function_name,
        tool_description=tool_description,
        function_code=function_code
    )
    

    tool_dir = os.getenv("TOOLS_DIRECTORY")
    tool_path = os.path.join(tool_dir, f"{tool_name.title().replace(" ", "_")}.py")

    os.makedirs(tool_dir, exist_ok=True)
    
    with open(f"{tool_path}", "w", encoding='utf-8') as file:
        file.write(final_code)
    
    tool_data = {
        "name": tool_name,
        "description": tool_description,
        "tool_path": tool_path
    }
    tools_collection.insert_one(tool_data)
    print("\nTool created successfully!\n")

def fetch_tools():
    tools_collection = db['tools']
    tools = tools_collection.find()

    available_tools = []
    for i, tool in enumerate(tools, start=1):
        available_tools.append({
            "reference_id": i,
            "tool_id": str(tool.get("_id")),
            "tool_name": tool.get("name"),
            "tool_description": tool.get("description"),
            "tool_path": tool.get("tool_path")
        })
    
    return available_tools

def display_tools(tools):
    if tools is None or len(tools) == 0:
        tools = fetch_tools()
    
    print("\nAvailable Tools:\n")
    for tool in tools:
        print(f"  - Reference ID: {tool['reference_id']}, Tool ID: {tool['tool_id']}, Name: {tool['tool_name']}, Description: {tool['tool_description']}")

def fetch_tool_objects(tool_ids):
    tools_collection = db['tools']
    
    object_ids = [ObjectId(id) for id in tool_ids]
    cursor = tools_collection.find(
        {"_id": {"$in": object_ids}},
        {"_id": 0, "tool_path": 1}
    )
    
    file_path_list = [doc["tool_path"] for doc in cursor]
    tool_list = []
    for path in file_path_list:
        module_name = os.path.splitext(os.path.basename(path))[0]
        spec = importlib.util.spec_from_file_location(module_name, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    
        for name, obj in inspect.getmembers(module):
            if name != 'BaseTool' and inspect.isclass(obj):
                tool_list.append(obj())
                break
    return tool_list
