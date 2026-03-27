import os
import ast
class AsyncCallVisitor(ast.NodeVisitor):
    def __init__(self, async_funcs):
        self.async_funcs = async_funcs
        self.missing_awaits = []

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
            if func_name in self.async_funcs:
                # Check if it is inside an Await node
                pass # This requires walking up, or easier: find all awaits and match
        self.generic_visit(node)

# A simpler approach: Just collect all async def names across the project
# Then grep for those names being called without an "await" prefix.

async_funcs = set()
for root, _, files in os.walk('app'):
    for f in files:
        if f.endswith('.py'):
            try:
                tree = ast.parse(open(os.path.join(root, f), encoding='utf-8').read())
                for node in ast.walk(tree):
                    if isinstance(node, ast.AsyncFunctionDef):
                        async_funcs.add(node.name)
            except Exception: pass

with open("async_funcs_list.txt", "w") as out:
    for a in sorted(list(async_funcs)):
        out.write(a + "\n")
