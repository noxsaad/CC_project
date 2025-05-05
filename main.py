from lexer import lexer
from parser import parser
from semantic import semantic_check
from ir_generator import IRGenerator
from graphviz import Digraph

def visualize_ast(ast, graph=None, parent=None):
    if graph is None:
        graph = Digraph()
    
    # If ast is a list, iterate through each element
    if isinstance(ast, list):
        for node in ast:
            visualize_ast(node, graph, parent)
        return graph

    node_id = str(id(ast))
    label = ast.nodetype if ast.leaf is None else f"{ast.nodetype}: {ast.leaf}"
    graph.node(node_id, label)
    
    if parent:
        graph.edge(parent, node_id)
    
    for child in ast.children:
        # If a child is a list, iterate through each element
        if isinstance(child, list):
            for subchild in child:
                visualize_ast(subchild, graph, node_id)
        else:
            visualize_ast(child, graph, node_id)
    return graph

def constant_folding(ir_code):
    """
    Constant folding optimization: Evaluate constant expressions at compile-time.
    Example: '3 + 4' becomes '7'.
    """
    optimized_ir = []
    
    for line in ir_code:
        if '=' in line:
            try:
                lhs, rhs = line.split('=', 1)
                rhs = rhs.strip()
                
                # Check if right-hand side is a constant expression (e.g., '3 + 4')
                if '+' in rhs:
                    parts = rhs.split('+')
                    if parts[0].isdigit() and parts[1].isdigit():
                        # Perform constant folding
                        result = int(parts[0]) + int(parts[1])
                        optimized_ir.append(f"{lhs.strip()} = {result}")
                        continue

                # Check other operations if necessary, such as '-', '*', '/'
                optimized_ir.append(line)
            except ValueError:
                # If we can't split or unpack, just add the line as is
                optimized_ir.append(line)
        else:
            optimized_ir.append(line)
    
    return optimized_ir

def dead_code_elimination(ir_code):
    """
    Dead Code Elimination: Remove assignments that are never used.
    Example: 'a = 5;' where 'a' is never used later.
    """
    used_variables = set()
    optimized_ir = []

    # First pass: Find all used variables
    for line in ir_code:
        if '=' in line:
            lhs = line.split('=')[0].strip()
            used_variables.add(lhs)
        elif any(var in line for var in used_variables):
            optimized_ir.append(line)
    
    # Second pass: Remove dead assignments
    for line in ir_code:
        lhs = line.split('=')[0].strip()
        if lhs in used_variables:
            optimized_ir.append(line)

    return optimized_ir

def strength_reduction(ir_code):
    """
    Strength reduction optimization: Replace expensive operations with cheaper alternatives.
    Example: Replace 'i * 2' with 'i << 1'.
    """
    optimized_ir = []
    
    for line in ir_code:
        if '*' in line:
            try:
                lhs, rhs = line.split('=', 1)
                rhs = rhs.strip()
                
                if rhs.endswith('* 2'):
                    # Replace multiplication by 2 with shift left by 1
                    optimized_ir.append(f"{lhs.strip()} = {rhs.replace('* 2', '<< 1')}")  
                else:
                    optimized_ir.append(line)
            except ValueError:
                # If we can't split or unpack, just add the line as is
                optimized_ir.append(line)
        else:
            optimized_ir.append(line)
    
    return optimized_ir

def apply_optimizations(ir_code):
    """
    Apply all optimizations to the LLVM IR code.
    """
    ir_code = constant_folding(ir_code)
    ir_code = dead_code_elimination(ir_code)
    ir_code = strength_reduction(ir_code)
    
    return ir_code

def main():
    # Read the source code from test_code.txt
    try:
        with open('test_code.txt', 'r') as f:
            data = f.read()
    except FileNotFoundError:
        print("Error: 'test_code.txt' not found. Please create the file with your source code.")
        return

    # Lexical analysis: Print tokens
    lexer.input(data)
    print("Tokens:")
    for tok in lexer:
        print(f"{tok.lineno}: {tok.type}({tok.value})")

    # Syntax analysis: Build the AST
    ast = parser.parse(data)
    if ast:
        print("\nAbstract Syntax Tree:")
        print(ast.print_tree())

        # Visualize the AST (generates a PDF file named 'ast.pdf')
        graph = visualize_ast(ast)
        graph.render('ast', view=True)
    else:
        print("Parsing failed.")
        return

    # Semantic analysis
    print("\nSemantic Analysis:")
    semantic_check(ast)
    
    # Generate LLVM IR
    print("\nGenerating LLVM IR:")
    try:
        ir_gen = IRGenerator()
        ir_module = ir_gen.generate_ir(ast)
        
        # Print the generated IR
        print(str(ir_module))
        
        # Write the generated IR to a file
        with open('output.ll', 'w') as f:
            f.write(str(ir_module))
        print("LLVM IR written to output.ll")
        
        # Read the IR from the file and apply optimizations
        with open('output.ll', 'r') as f:
            ir_code = f.readlines()
        
        # Apply optimizations to the IR
        optimized_ir = apply_optimizations(ir_code)
        
        # Write the optimized IR to a new file
        with open('optimized_output.ll', 'w') as f:
            f.writelines(optimized_ir)
        print("Optimized LLVM IR written to optimized_output.ll")
        
    except Exception as e:
        print(f"Error generating LLVM IR: {e}")
        return

if __name__ == '__main__':
    main()
