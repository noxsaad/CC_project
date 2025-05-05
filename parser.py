import ply.yacc as yacc
from lexer import tokens

# Define a simple AST node class
class ASTNode:
    def __init__(self, nodetype, children=None, leaf=None):
        self.nodetype = nodetype
        self.children = children if children is not None else []
        self.leaf = leaf

    def __str__(self):
        return f"{self.nodetype}: {self.leaf if self.leaf is not None else ''}"

    def print_tree(self, level=0):
        indent = "  " * level
        output = f"{indent}{self.nodetype}: {self.leaf if self.leaf is not None else ''}\n"
        for child in self.children:
            if isinstance(child, list):
                for subchild in child:
                    output += subchild.print_tree(level + 1)
            else:
                output += child.print_tree(level + 1)
        return output

# Starting rule: a program is a list of statements
def p_program(p):
    '''program : statement_list'''
    p[0] = ASTNode("program", p[1])

def p_statement_list(p):
    '''statement_list : statement_list statement
                      | statement'''
    if len(p) == 3:
        p[0] = p[1] + [p[2]]
    else:
        p[0] = [p[1]]

# Declaration: e.g., int a = 4; or int z;
def p_statement_declaration(p):
    '''statement : INT IDENTIFIER declaration_rest'''
    p[0] = ASTNode("declaration", [p[3]], p[2])

def p_declaration_rest_init(p):
    '''declaration_rest : EQUALS expression SEMI'''
    p[0] = ASTNode("init", [p[2]])
    
def p_declaration_rest_noinit(p):
    '''declaration_rest : SEMI'''
    p[0] = ASTNode("noinit")

# Assignment: e.g., a = 50;
def p_statement_assignment(p):
    '''statement : IDENTIFIER EQUALS expression SEMI'''
    p[0] = ASTNode("assignment", [ASTNode("identifier", leaf=p[1]), p[3]])

# Expression statement: e.g., a + 1;
def p_statement_expr(p):
    '''statement : expression SEMI'''
    p[0] = ASTNode("expression_statement", [p[1]])

# If statement: e.g., if (a > b) { ... }
def p_statement_if(p):
    '''statement : IF LPAREN expression RPAREN LBRACE statement_list RBRACE'''
    p[0] = ASTNode("if", [p[3], ASTNode("block", p[6])])

# Return statement: e.g., return x + y;
def p_statement_return(p):
    '''statement : RETURN expression SEMI'''
    p[0] = ASTNode("return", [p[2]])

# Function declaration:
# e.g., function sum(int x, int y) -> int { return x + y; }
def p_statement_function(p):
    '''statement : FUNCTION IDENTIFIER LPAREN parameter_list RPAREN ARROW INT LBRACE statement_list RBRACE'''
    p[0] = ASTNode("function_decl", [p[4], ASTNode("return_type", leaf="int"), ASTNode("block", p[9])], p[2])

def p_parameter_list(p):
    '''parameter_list : parameter_list COMMA parameter
                      | parameter
                      | empty'''
    if len(p) == 4:
        p[0] = p[1] + [p[3]]
    elif len(p) == 2:
        if p[1] is None:
            p[0] = []
        else:
            p[0] = [p[1]]

def p_parameter(p):
    '''parameter : INT IDENTIFIER'''
    p[0] = ASTNode("param", leaf=p[2])

def p_empty(p):
    'empty :'
    p[0] = None

# Function call expression: e.g., sum(a, b)
def p_expression_funccall(p):
    '''expression : IDENTIFIER LPAREN argument_list RPAREN'''
    p[0] = ASTNode("funccall", [p[3]], p[1])

def p_argument_list(p):
    '''argument_list : argument_list COMMA expression
                     | expression
                     | empty'''
    if len(p) == 4:
        p[0] = p[1] + [p[3]]
    elif len(p) == 2:
        if p[1] is None:
            p[0] = []
        else:
            p[0] = [p[1]]

# Binary operations and comparisons
def p_expression_binop(p):
    '''expression : expression PLUS expression
                  | expression MINUS expression
                  | expression TIMES expression
                  | expression DIVIDE expression
                  | expression GT expression'''
    p[0] = ASTNode("binary_op", [p[1], p[3]], p[2])

def p_expression_group(p):
    '''expression : LPAREN expression RPAREN'''
    p[0] = p[2]

def p_expression_number(p):
    '''expression : NUMBER'''
    p[0] = ASTNode("number", leaf=p[1])

def p_expression_identifier(p):
    '''expression : IDENTIFIER'''
    p[0] = ASTNode("identifier", leaf=p[1])

def p_error(p):
    if p:
        print(f"Syntax error at token '{p.value}' (line {p.lineno})")
    else:
        print("Syntax error at EOF")

# Build the parser
parser = yacc.yacc()

if __name__ == '__main__':
    # Read from test_code.txt
    try:
        with open('test_code.txt', 'r') as f:
            data = f.read()
    except FileNotFoundError:
        print("Error: 'test_code.txt' not found.")
        exit(1)
        
    result = parser.parse(data)
    if result:
        print(result.print_tree())
    else:
        print("Parsing failed.")
