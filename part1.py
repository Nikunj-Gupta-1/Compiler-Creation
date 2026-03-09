import ply.lex as lex # type: ignore
import sys

tokens = ('INT', 'FLOAT', 'INT_TYPE', 'FLOAT_TYPE', 'ID', 'SEMI', 'ASSIGN', 'PLUS', 'MINUS', 'MUL', 'DIV', 'MOD',
          'LT', 'GT', 'LE', 'GE', 'EQ', 'NEQ', 
          'AND', 'OR', 'NOT',
          'IF', 'ELSE', 'WHILE',
          'LCURLY', 'RCURLY', 'LPAREN', 'RPAREN',
          'PRINT')

t_PLUS = r'\+'
t_MINUS = r'-'
t_MUL = r'\*'
t_DIV = r'/'
t_MOD = r'%'
t_LE = r'<='
t_LT = r'<'
t_GE = r'>='
t_GT = r'>'
t_EQ = r'=='
t_ASSIGN = r'='
t_NEQ = r'!='
t_NOT = r'!'
t_AND = r'&&'
t_OR = r'\|\|'
t_SEMI = r';'
t_LCURLY = r'\{'
t_RCURLY = r'\}'
t_LPAREN = r'\('    
t_RPAREN = r'\)'

reserved = {
    'if': 'IF',
    'else': 'ELSE', 
    'while': 'WHILE',
    'print': 'PRINT',
    'int' : 'INT_TYPE',
    'float' : 'FLOAT_TYPE',
}

def t_ID(t):
    r'[a-zA-Z][a-zA-Z0-9_]*'
    if t.value in reserved:
        t.type = reserved[t.value]
    return t

def t_FLOAT(t):
    r'\d+\.\d+'
    t.value = float(t.value)
    return t

def t_INT(t):
    r'\d+'
    t.value = int(t.value)
    return t

t_ignore = ' \t'

def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

def t_error(t):
    print(f"Lexical Error: Illegal character '{t.value[0]}' at line {t.lineno}")
    t.lexer.skip(1)

lexer = lex.lex()

if len(sys.argv) <2:
    print("Usage: python lexer <filename>")
    exit(1)

with open(sys.argv[1], 'r') as f:
    data = f.read()
lexer.input(data)

print(f"{'Lexeme':<10}{'Token Type':<15}{'Line'}")
print("-" * 35)

for token in lexer:
    print(f"{token.value:<10}{token.type:<15}{token.lineno}")

print("-" * 35)