# Simple SymbolTable implementation for semantic analysis

class SymbolTable:
    def __init__(self, parent=None):
        self.symbols = {}
        self.parent = parent

    def add(self, name, info):
        if name in self.symbols:
            print(f"Semantic error: Symbol '{name}' already declared.")
        else:
            self.symbols[name] = info

    def lookup(self, name):
        if name in self.symbols:
            return self.symbols[name]
        elif self.parent:
            return self.parent.lookup(name)
        return None

def semantic_check(ast, sym_table=None):
    if sym_table is None:
        sym_table = SymbolTable()

    if ast is None:
        return

    if ast.nodetype == "program":
        for stmt in ast.children:
            semantic_check(stmt, sym_table)

    elif ast.nodetype == "block":
        new_table = SymbolTable(sym_table)
        for stmt in ast.children:
            semantic_check(stmt, new_table)

    elif ast.nodetype == "declaration":
        var_name = ast.leaf
        init_node = ast.children[0]
        if init_node.nodetype == "init":
            sym_table.add(var_name, {"initialized": True})
            semantic_check(init_node.children[0], sym_table)
        elif init_node.nodetype == "noinit":
            print(f"Semantic error: Variable '{var_name}' is not initialized before use.")
            # Optionally, do not add it to the symbol table

    elif ast.nodetype == "assignment":
        identifier_node = ast.children[0]
        var_name = identifier_node.leaf
        symbol = sym_table.lookup(var_name)
        if symbol is None:
            print(f"Semantic error: Variable '{var_name}' is not declared before assignment.")
        else:
            symbol["initialized"] = True
        semantic_check(ast.children[1], sym_table)

    elif ast.nodetype == "identifier":
        var_name = ast.leaf
        symbol = sym_table.lookup(var_name)
        if symbol is None or not symbol.get("initialized", False):
            print(f"Semantic error: Variable '{var_name}' is not initialized before use.")

    elif ast.nodetype == "binary_op":
        semantic_check(ast.children[0], sym_table)
        semantic_check(ast.children[1], sym_table)

    elif ast.nodetype == "expression_statement":
        semantic_check(ast.children[0], sym_table)

    elif ast.nodetype == "if":
        semantic_check(ast.children[0], sym_table)
        new_table = SymbolTable(sym_table)
        semantic_check(ast.children[1], new_table)

    elif ast.nodetype == "return":
        semantic_check(ast.children[0], sym_table)

    elif ast.nodetype == "function_decl":
        func_name = ast.leaf
        sym_table.add(func_name, {"initialized": True})
        new_table = SymbolTable(sym_table)
        param_list = ast.children[0]
        if param_list is not None:
            for param in param_list:
                new_table.add(param.leaf, {"initialized": True})
        semantic_check(ast.children[2], new_table)

    elif ast.nodetype == "init":
        semantic_check(ast.children[0], sym_table)

    elif ast.nodetype == "funccall":
        # Process function call arguments
        for arg in ast.children[0]:
            semantic_check(arg, sym_table)

    else:
        for child in ast.children:
            semantic_check(child, sym_table)

if __name__ == '__main__':
    # Standalone test of semantic analysis
    from parser import ASTNode
    decl_z = ASTNode("declaration", [ASTNode("noinit")], "z")
    assign_z = ASTNode("assignment", [ASTNode("identifier", leaf="z"), ASTNode("number", leaf=50)])
    program_ast = ASTNode("program", [decl_z, assign_z])
    semantic_check(program_ast)
