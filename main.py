# main.py

import os
from lexer import lexer
from parser import parser
from semantic import semantic_check
from ir_generator import IRGenerator
from graphviz import Digraph
from llvmlite import binding as llvm
import re

# Initialize LLVM for assembly emission
llvm.initialize()
llvm.initialize_native_target()
llvm.initialize_native_asmprinter()

def visualize_ast(ast, graph=None, parent=None):
    if graph is None:
        graph = Digraph()

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
        if isinstance(child, list):
            for subchild in child:
                visualize_ast(subchild, graph, node_id)
        else:
            visualize_ast(child, graph, node_id)
    return graph

def constant_folding(ir_code):
    optimized_ir = []
    for line in ir_code:
        if '=' in line:
            try:
                lhs, rhs = line.split('=', 1)
                rhs = rhs.strip()
                if '+' in rhs:
                    parts = [p.strip() for p in rhs.split('+', 1)]
                    if parts[0].isdigit() and parts[1].isdigit():
                        result = int(parts[0]) + int(parts[1])
                        optimized_ir.append(f"{lhs.strip()} = {result}\n")
                        continue
                optimized_ir.append(line)
            except ValueError:
                optimized_ir.append(line)
        else:
            optimized_ir.append(line)
    return optimized_ir

def dead_code_elimination(ir_code):
    assignments = {}
    used = set()
    optimized_ir = []

    # First pass: collect assignments and track used vars
    for line in ir_code:
        if '=' in line and 'alloca' not in line:
            lhs, rhs = line.split('=', 1)
            var = lhs.strip().lstrip('%"')
            assignments[var] = line
            tokens = re.findall(r'%[\w\.]+', rhs)
            for tok in tokens:
                used.add(tok.lstrip('%"'))
        else:
            optimized_ir.append(line)

    # Keep only assignments whose LHS was used
    for var, instr in assignments.items():
        if var in used:
            optimized_ir.append(instr)

    return optimized_ir

def strength_reduction(ir_code):
    optimized_ir = []
    for line in ir_code:
        if '*' in line and '=' in line:
            try:
                lhs, rhs = line.split('=', 1)
                rhs = rhs.strip()
                if rhs.endswith('* 2'):
                    optimized_ir.append(f"{lhs.strip()} = {rhs.replace('* 2', '<< 1')}\n")
                    continue
                optimized_ir.append(line)
            except ValueError:
                optimized_ir.append(line)
        else:
            optimized_ir.append(line)
    return optimized_ir

def apply_optimizations(ir_code):
    ir_code = constant_folding(ir_code)
    ir_code = dead_code_elimination(ir_code)
    ir_code = strength_reduction(ir_code)
    return ir_code

def main():
    # Read source code
    try:
        with open('test_code.txt', 'r') as f:
            data = f.read()
    except FileNotFoundError:
        print("Error: 'test_code.txt' not found.")
        return

    # Lexical analysis
    lexer.input(data)
    print("Tokens:")
    for tok in lexer:
        print(f"{tok.lineno}: {tok.type}({tok.value})")

    # Parsing
    ast = parser.parse(data)
    if not ast:
        print("Parsing failed.")
        return

    print("\nAbstract Syntax Tree:")
    print(ast.print_tree())

    # Visualize AST
    try:
        out_dir = "build"
        os.makedirs(out_dir, exist_ok=True)
        graph = visualize_ast(ast)
        graph.render(filename="ast", directory=out_dir, view=False)
        print(f"AST PDF written to {out_dir}/ast.pdf")
    except Exception as e:
        print(f"Warning: could not render AST PDF: {e}")

    # Semantic analysis
    print("\nSemantic Analysis:")
    semantic_check(ast)

    # Generate LLVM IR
    print("\nGenerating LLVM IR:")
    try:
        ir_gen = IRGenerator()
        ir_module = ir_gen.generate_ir(ast)
        ir_text = str(ir_module)

        # Write unoptimized IR
        with open('output.ll', 'w') as f:
            f.write(ir_text)
        print("LLVM IR written to output.ll")

        # Emit assembly from IR
        mod = llvm.parse_assembly(ir_text)
        mod.verify()
        target = llvm.Target.from_default_triple()
        tm = target.create_target_machine()
        asm = tm.emit_assembly(mod)
        with open('output.s', 'w') as f:
            f.write(asm)
        print("Assembly written to output.s")

        # Apply optimizations to IR text
        ir_lines = ir_text.splitlines(keepends=True)
        optimized_lines = apply_optimizations(ir_lines)
        with open('optimized_output.ll', 'w') as f:
            f.writelines(optimized_lines)
        print("Optimized IR written to optimized_output.ll")

        # Emit optimized assembly
        opt_mod = llvm.parse_assembly("".join(optimized_lines))
        opt_mod.verify()
        opt_asm = tm.emit_assembly(opt_mod)
        with open('optimized_output.s', 'w') as f:
            f.write(opt_asm)
        print("Optimized assembly written to optimized_output.s")

    except Exception as e:
        print(f"Error generating code: {e}")

if __name__ == '__main__':
    main()
