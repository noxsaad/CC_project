import ply.lex as lex

# List of token names including keywords and symbols
tokens = (
    'IDENTIFIER',
    'NUMBER',
    'PLUS',
    'MINUS',
    'TIMES',
    'DIVIDE',
    'LPAREN',
    'RPAREN',
    'SEMI',
    'EQUALS',
    'COMMA',
    'LBRACE',
    'RBRACE',
    'GT',
    'ARROW',  
    # Keywords
    'IF',
    'ELSE',
    'WHILE',
    'FOR',
    'DEF',
    'RETURN',
    'INT',
    'FUNCTION',
)

# Regular expression rules for simple tokens
t_PLUS    = r'\+'
t_MINUS   = r'-'
t_TIMES   = r'\*'
t_DIVIDE  = r'/'
t_LPAREN  = r'\('
t_RPAREN  = r'\)'
t_SEMI    = r';'
t_EQUALS  = r'='
t_COMMA   = r','
t_LBRACE  = r'\{'
t_RBRACE  = r'\}'
t_GT      = r'>'
t_ARROW   = r'->'  

# Reserved keywords dictionary
reserved = {
    'if': 'IF',
    'else': 'ELSE',
    'while': 'WHILE',
    'for': 'FOR',
    'def': 'DEF',
    'return': 'RETURN',
    'int': 'INT',
    'function': 'FUNCTION'
}

# Token for identifiers and keywords
def t_IDENTIFIER(t):
    r'[A-Za-z_][A-Za-z0-9_]*'
    t.type = reserved.get(t.value, 'IDENTIFIER')
    return t

# Token for numbers
def t_NUMBER(t):
    r'\d+(\.\d+)?'
    t.value = float(t.value) if '.' in t.value else int(t.value)
    return t

# Single-line comments (e.g., // comment)
def t_COMMENT_SINGLELINE(t):
    r'//.*'
    pass

# Multi-line comments (e.g., /* comment */)
def t_COMMENT_MULTILINE(t):
    r'/\*(.|\n)*?\*/'
    t.lexer.lineno += t.value.count('\n')
    pass

# Characters to ignore (spaces and tabs)
t_ignore = ' \t'

# Track line numbers
def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

def t_error(t):
    print(f"Illegal character '{t.value[0]}' at line {t.lineno}")
    t.lexer.skip(1)

# Build the lexer
lexer = lex.lex()

if __name__ == '__main__':
    data = "int a = 4; int b = 3;"
    lexer.input(data)
    for tok in lexer:
        print(f"{tok.lineno}: {tok.type}({tok.value})")
