import os
import ast

def get_unawaited_async_calls():
    # 1. Gather all async function names
    async_funcs = set()
    for root, _, files in os.walk("app"):
        for f in files:
            if f.endswith(".py"):
                with open(os.path.join(root, f), "r", encoding="utf-8") as file:
                    try:
                        tree = ast.parse(file.read())
                        for node in ast.walk(tree):
                            if isinstance(node, ast.AsyncFunctionDef):
                                async_funcs.add(node.name)
                    except: pass
    
    # 2. Find Calls to these functions that are not inside an Await node
    class AwaitChecker(ast.NodeVisitor):
        def __init__(self, filename):
            self.filename = filename
            self.unawaited = []
            
        def visit_Call(self, node):
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
                if func_name in async_funcs:
                    if not hasattr(node, "parent") or not isinstance(node.parent, ast.Await):
                        self.unawaited.append((func_name, node.lineno))
            elif isinstance(node.func, ast.Attribute):
                func_name = node.func.attr
                if func_name in async_funcs: # naive check
                    if not hasattr(node, "parent") or not isinstance(node.parent, ast.Await):
                        self.unawaited.append((func_name, node.lineno))
            self.generic_visit(node)
            
    for root, _, files in os.walk("app"):
        for f in files:
            if f.endswith(".py"):
                file_path = os.path.join(root, f)
                with open(file_path, "r", encoding="utf-8") as file:
                    try:
                        tree = ast.parse(file.read())
                        for node in ast.walk(tree):
                            for child in ast.iter_child_nodes(node):
                                child.parent = node
                        checker = AwaitChecker(file_path)
                        checker.visit(tree)
                        if checker.unawaited:
                            for func, line in checker.unawaited:
                                print(f"{file_path}:{line} -> unawaited call to {func}()")
                    except: pass

get_unawaited_async_calls()
