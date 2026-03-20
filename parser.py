import ply.yacc as yacc # type: ignore
from lexer import tokens, lexer
import sys

class Node:
    def __init__(self, type, children=None, leaf=None):
        self.type = type
        self.children = children if children else []
        self.leaf = leaf

    def print_tree(self, indent=0):
        print('  ' * indent + self.type + (f": {self.leaf}" if self.leaf else ''))
        for child in self.children:
            if isinstance(child, Node):
                child.print_tree(indent + 1)
            else:
                print('  ' * (indent + 1) + str(child))

precedence = (
    ('left', 'OR'),
    ('left', 'AND'),
    ('left', 'EQ', 'NEQ'),
    ('left', 'LT', 'LE', 'GT', 'GE'),
    ('left', 'PLUS', 'MINUS'),
    ('left', 'MUL', 'DIV', 'MOD'),
    ('right', 'NOT'),
)

def p_program(p):
    '''program : decl_list stmt_list'''
    p[0] = Node('program', [p[1], p[2]])
    print("Valid program")
    global parse_tree
    parse_tree = p[0]

def p_decl_list(p):
    '''decl_list : decl decl_list
                 | empty'''
    if len(p) == 3:
        p[0] = Node('decl_list', [p[1], p[2]])
    else:
        p[0] = Node('decl_list', [])

def p_decl(p):
    '''decl : type ID SEMI'''
    p[0] = Node('decl', [p[1]], p[2])

def p_type(p):
    '''type : INT_TYPE
            | FLOAT_TYPE'''
    p[0] = Node('type', leaf=p[1])

def p_stmt_list(p):
    '''stmt_list : stmt stmt_list
                 | empty'''
    if len(p) == 3:
        p[0] = Node('stmt_list', [p[1], p[2]])
    else:
        p[0] = Node('stmt_list', [])

def p_stmt(p):
    '''stmt : assign_stmt
            | if_stmt
            | while_stmt
            | block
            | decl
            | print_stmt'''
    p[0] = Node('stmt', [p[1]])

def p_assign_stmt(p):
    '''assign_stmt : ID ASSIGN expr SEMI'''
    p[0] = Node('assign_stmt', [p[3]], p[1])

def p_expr(p):
    '''expr : expr PLUS term
            | expr MINUS term
            | term'''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = Node('expr', [p[1], p[3]], p[2])

def p_term(p):
    '''term : term MUL factor
            | term DIV factor
            | term MOD factor
            | factor'''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = Node('term', [p[1], p[3]], p[2])

def p_factor(p):
    '''factor : LPAREN expr RPAREN
              | ID
              | INT
              | FLOAT'''
    if len(p) == 2:
        p[0] = Node('factor', leaf=p[1])
    else:
        p[0] = Node('factor', [p[2]])

def p_bool_expr(p):
    '''bool_expr : bool_expr OR bool_term
                 | bool_term'''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = Node('bool_expr', [p[1], p[3]], p[2])

def p_bool_term(p):
    '''bool_term : bool_term AND bool_factor
                 | bool_factor'''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = Node('bool_term', [p[1], p[3]], p[2])

def p_bool_factor(p):
    '''bool_factor : NOT bool_factor
                   | LPAREN bool_expr RPAREN
                   | rel_expr'''
    if len(p) == 2:
        p[0] = p[1]
    elif len(p) == 3:
        p[0] = Node('NOT', [p[2]])
    else:
        p[0] = Node('bool_factor', [p[2]])

def p_rel_expr(p):
    '''rel_expr : expr LT expr
                | expr GT expr
                | expr LE expr
                | expr GE expr
                | expr EQ expr
                | expr NEQ expr'''
    p[0] = Node('rel_expr', [p[1], p[3]], p[2])

def p_while_stmt(p):
    '''while_stmt : WHILE LPAREN bool_expr RPAREN stmt'''
    p[0] = Node('while_stmt', [p[3], p[5]])

def p_if_stmt(p):
    '''if_stmt : IF LPAREN bool_expr RPAREN stmt ELSE stmt'''
    p[0] = Node('if_stmt', [p[3], p[5], p[7]])

def p_block(p):
    '''block : LCURLY stmt_list RCURLY'''
    p[0] = Node('block', [p[2]])

def p_print_stmt(p):
    '''print_stmt : PRINT LPAREN expr RPAREN SEMI'''
    p[0] = Node('print_stmt', [p[3]])

def p_empty(p):
    'empty : '
    p[0] = Node('empty')

_input_text = ""

def _find_column(text, token):
    last_cr = text.rfind('\n', 0, token.lexpos)
    if last_cr < 0:
        last_cr = -1
    column = (token.lexpos - last_cr)
    return column

def _suggest_fix(p, text):
    if not p:
        return "Unexpected end of file. Maybe you forgot a '}' or ';' at the end of the program?"
    tok = p
    tval = str(tok.value)
    ttype = tok.type
    if ttype == 'ID':
        return "Check for a missing ';' at the end of the previous statement or a missing operator before this identifier."
    if ttype in ('INT', 'FLOAT'):
        return "Check for a missing operator before this literal or a missing ';' after the previous statement."
    if ttype == 'RCURLY':
        return "Unexpected '}'. Make sure all '{' have matching '}' and that blocks are properly closed."
    if ttype == 'LCURLY':
        return "Unexpected '{'. Check the preceding 'if', 'while', or block syntax."
    if ttype == 'RPAREN':
        return "Unexpected ')'. Check that you have a matching '(' and that expressions are complete."
    if ttype == 'LPAREN':
        return "Unexpected '('. Check the preceding 'if', 'while', or function-like syntax."
    if ttype == 'SEMI':
        return "Unexpected ';'. You may have an extra semicolon or a missing statement before it."
    if ttype in ('PLUS', 'MINUS', 'MUL', 'DIV', 'MOD'):
        return "Unexpected operator. Check for a missing operand before or after this operator."
    if ttype in ('IF', 'ELSE', 'WHILE'):
        return f"Misplaced '{tval}'. Check the syntax: 'if (cond) stmt else stmt', 'while (cond) stmt'."
    return "Check the syntax around this token; you may have a missing ';', ')', or '}' nearby."

def p_error(p):
    global _input_text
    if p:
        line = p.lineno
        col = _find_column(_input_text, p)
        suggestion = _suggest_fix(p, _input_text)
        lines = _input_text.splitlines()
        line_text = lines[line - 1] if 0 < line <= len(lines) else ""
        print(f"Syntax Error: unexpected token '{p.value}' (type {p.type}) at line {line}, column {col}")
        if line_text:
            print(f"  {line}: {line_text}")
            print(" " * (len(str(line)) + 2 + col - 1) + "^")
        print("Hint:", suggestion)
    else:
        print("Syntax Error: unexpected end of input (EOF)")
        print("Hint: Maybe you forgot a '}', ')', or ';' before the end of the file.")
    sys.exit(1)

parser = yacc.yacc()

if len(sys.argv) < 2:
    print("Usage: python parser.py <input_file>")
    sys.exit(1)

with open(sys.argv[1], 'r') as f:
    data = f.read()

_input_text = data
parse_tree = None
parser.parse(data, lexer=lexer)

if parse_tree is not None:
    print("\nParse Tree: ")
    parse_tree.print_tree()
