from llvmlite import ir
from llvmlite import binding as llvm

# Initialize LLVM
llvm.initialize()
llvm.initialize_native_target()
llvm.initialize_native_asmprinter()

class IRGenerator:
    def __init__(self):
        # Initialize module and builder
        self.module = ir.Module(name="cc_module")
        self.builder = None
        
        # Setup target info for the current machine
        target = llvm.Target.from_default_triple()
        target_machine = target.create_target_machine()
        self.module.triple = target_machine.triple
        
        # Symbol table for storing variable addresses
        self.symbol_table = {}
        
        # Function table
        self.functions = {}
        
        # Define main function type (int main())
        self.func_type = ir.FunctionType(ir.IntType(32), [], False)
        
        # Create int type (default to 32-bit)
        self.int_type = ir.IntType(32)
        
    def generate_ir(self, ast):
        """Generate LLVM IR from AST"""
        if ast.nodetype == "program":
            # Create main function
            main_func = ir.Function(self.module, self.func_type, name="main")
            block = main_func.append_basic_block(name="entry")
            self.builder = ir.IRBuilder(block)
            
            # Generate IR for all statements
            for stmt in ast.children:
                self._generate_statement(stmt)
            
            # Add a return statement at the end if not present
            if not self.builder.block.is_terminated:
                self.builder.ret(ir.Constant(self.int_type, 0))
            
            return self.module
        else:
            raise ValueError(f"Expected program node, got {ast.nodetype}")
    
    def _generate_statement(self, node):
        """Generate IR for a statement node"""
        if node.nodetype == "declaration":
            self._generate_declaration(node)
        elif node.nodetype == "assignment":
            self._generate_assignment(node)
        elif node.nodetype == "expression_statement":
            self._generate_expression(node.children[0])  # Just evaluate the expression
        elif node.nodetype == "if":
            self._generate_if(node)
        elif node.nodetype == "return":
            self._generate_return(node)
        elif node.nodetype == "function_decl":
            self._generate_function_decl(node)
        else:
            raise ValueError(f"Unknown statement type: {node.nodetype}")
    
    def _generate_declaration(self, node):
        """Generate IR for variable declaration"""
        var_name = node.leaf
        init_node = node.children[0]
        
        # Allocate memory for the variable
        var_addr = self.builder.alloca(self.int_type, name=var_name)
        self.symbol_table[var_name] = var_addr
        
        # If initialized, store the initial value
        if init_node.nodetype == "init":
            init_value = self._generate_expression(init_node.children[0])
            self.builder.store(init_value, var_addr)
    
    def _generate_assignment(self, node):
        """Generate IR for assignment"""
        identifier_node = node.children[0]
        var_name = identifier_node.leaf
        
        if var_name not in self.symbol_table:
            raise ValueError(f"Variable {var_name} not in symbol table")
        
        # Generate the expression value
        expr_value = self._generate_expression(node.children[1])
        
        # Store the value to the variable
        self.builder.store(expr_value, self.symbol_table[var_name])
    
    def _generate_expression(self, node):
        """Generate IR for expression nodes"""
        if node.nodetype == "number":
            return ir.Constant(self.int_type, node.leaf)
        
        elif node.nodetype == "identifier":
            var_name = node.leaf
            if var_name in self.symbol_table:
                return self.builder.load(self.symbol_table[var_name], name=f"{var_name}_val")
            else:
                raise ValueError(f"Variable {var_name} not in symbol table")
        
        elif node.nodetype == "binary_op":
            left = self._generate_expression(node.children[0])
            right = self._generate_expression(node.children[1])
            
            if node.leaf == '+':
                return self.builder.add(left, right, name="addtmp")
            elif node.leaf == '-':
                return self.builder.sub(left, right, name="subtmp")
            elif node.leaf == '*':
                return self.builder.mul(left, right, name="multmp")
            elif node.leaf == '/':
                return self.builder.sdiv(left, right, name="divtmp")
            elif node.leaf == '>':
                # Compare and convert boolean to int
                cmp = self.builder.icmp_signed('>', left, right, name="cmptmp")
                return self.builder.zext(cmp, self.int_type, name="booltmp")
            else:
                raise ValueError(f"Unknown binary operator: {node.leaf}")
        
        elif node.nodetype == "funccall":
            return self._generate_funccall(node)
        
        else:
            raise ValueError(f"Unknown expression node: {node.nodetype}")
    
    def _generate_if(self, node):
        """Generate IR for if statement"""
        # Generate condition expression
        cond_value = self._generate_expression(node.children[0])
        
        # Convert condition to a boolean value
        zero = ir.Constant(self.int_type, 0)
        cond_bool = self.builder.icmp_signed('!=', cond_value, zero, name="ifcond")
        
        # Create basic blocks for then and else
        func = self.builder.function
        then_block = func.append_basic_block(name="then")
        else_block = func.append_basic_block(name="else")
        merge_block = func.append_basic_block(name="ifcont")
        
        # Create conditional branch
        self.builder.cbranch(cond_bool, then_block, else_block)
        
        # Generate code for then block
        self.builder.position_at_end(then_block)
        for stmt in node.children[1].children:  # node.children[1] is the block
            self._generate_statement(stmt)
        
        # Branch to merge block if not already terminated
        if not self.builder.block.is_terminated:
            self.builder.branch(merge_block)
        
        # Generate code for else block (if there is one)
        self.builder.position_at_end(else_block)
        if len(node.children) > 2:  # If there's an else block
            for stmt in node.children[2].children:
                self._generate_statement(stmt)
        
        # Branch to merge block if not already terminated
        if not self.builder.block.is_terminated:
            self.builder.branch(merge_block)
        
        # Continue at merge block
        self.builder.position_at_end(merge_block)
    
    def _generate_return(self, node):
        """Generate IR for return statement"""
        if node.children:
            ret_val = self._generate_expression(node.children[0])
            self.builder.ret(ret_val)
        else:
            self.builder.ret(ir.Constant(self.int_type, 0))
    
    def _generate_function_decl(self, node):
        """Generate IR for function declaration"""
        func_name = node.leaf
        
        # Get return type (always int for now)
        ret_type = self.int_type
        
        # Create parameter types (all ints for now)
        param_types = [self.int_type] * len(node.children[0])
        
        # Create function type
        func_type = ir.FunctionType(ret_type, param_types, False)
        
        # Create function
        func = ir.Function(self.module, func_type, name=func_name)
        
        # Name the parameters
        for i, param_node in enumerate(node.children[0]):
            func.args[i].name = param_node.leaf
        
        # Store function in function table
        self.functions[func_name] = func
        
        # Create entry block
        block = func.append_basic_block(name="entry")
        old_builder = self.builder
        self.builder = ir.IRBuilder(block)
        
        # Create a new symbol table scope
        old_symbol_table = self.symbol_table
        self.symbol_table = {}
        
        # Allocate parameters in the function
        for i, param_node in enumerate(node.children[0]):
            param_name = param_node.leaf
            param_addr = self.builder.alloca(self.int_type, name=param_name)
            self.builder.store(func.args[i], param_addr)
            self.symbol_table[param_name] = param_addr
        
        # Generate IR for function body
        block_node = node.children[2]  # The block node
        for stmt in block_node.children:
            self._generate_statement(stmt)
        
        # Add implicit return 0 if not already terminated
        if not self.builder.block.is_terminated:
            self.builder.ret(ir.Constant(self.int_type, 0))
        
        # Restore old symbol table and builder
        self.symbol_table = old_symbol_table
        self.builder = old_builder
    
    def _generate_funccall(self, node):
        """Generate IR for function call"""
        func_name = node.leaf
        
        if func_name not in self.functions:
            raise ValueError(f"Function {func_name} not declared")
        
        func = self.functions[func_name]
        
        # Generate arguments
        args = []
        for arg_node in node.children[0]:
            args.append(self._generate_expression(arg_node))
        
        # Call function
        return self.builder.call(func, args, name=f"{func_name}_call")
    
    def print_ir(self):
        """Print the generated IR"""
        print(str(self.module))
    
    def write_ir_to_file(self, filename):
        """Write the generated IR to a file"""
        with open(filename, 'w') as f:
            f.write(str(self.module))
