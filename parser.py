import sys
import ply.yacc as yacc  # type: ignore
from py1 import tokens, lexer


class Node:
    def __init__(self, name, children=None, value=None):
        self.name = name
        self.children = children or []
        self.value = value


def print_tree(node, indent=0):
    space = "    " * indent
    if node.value is not None:
        print(f"{space}{node.name}: {node.value}")
    else:
        print(f"{space}{node.name}")
    for child in node.children:
        print_tree(child, indent + 1)


def p_program(p):
    'program : global_list'
    p[0] = Node("program", [p[1]])


def p_global_list(p):
    '''global_list : global
                   | global_list global'''
    if len(p) == 2:
        p[0] = Node("global_list", [p[1]])
    else:
        p[1].children.append(p[2])
        p[0] = p[1]


def p_global(p):
    '''global : declaration SEMICOLON
              | function_def
              | statement'''
    if len(p) == 3:
        p[0] = Node("global_decl", [p[1]])
    else:
        p[0] = Node("global", [p[1]])


def p_function_def(p):
    'function_def : type_specifier func_name LPAREN param_list RPAREN compound_stmt'
    p[0] = Node("function_def", [p[1], p[2], p[4], p[6]])


def p_func_name(p):
    '''func_name : ID
                 | FUNCTION'''
    p[0] = Node("func_name", value=p[1])


def p_param_list(p):
    '''param_list : empty
                  | param_decl
                  | param_list COMMA param_decl'''
    if len(p) == 2:
        p[0] = Node("param_list")
    elif len(p) == 2:
        p[0] = Node("param_list", [p[1]])
    else:
        p[1].children.append(p[3])
        p[0] = p[1]


def p_param_decl(p):
    'param_decl : type_specifier ID'
    p[0] = Node("param_decl", [p[1], Node("ID", value=p[2])])


def p_type_specifier(p):
    'type_specifier : KEYWORD'
    p[0] = Node("type", value=p[1])


def p_compound_stmt(p):
    'compound_stmt : LBRACE stmt_list RBRACE'
    p[0] = Node("block", [p[2]])


def p_compound_stmt_error(p):
    'compound_stmt : LBRACE stmt_list error'
    print(f"Syntax error: missing '}}' for block before token '{p[3].value}' on line {p.lineno(3)}")
    p[0] = Node("block_error", [p[2]])


def p_stmt_list(p):
    '''stmt_list : empty
                 | stmt_list statement'''
    if len(p) == 2:
        p[0] = Node("stmt_list")
    else:
        p[1].children.append(p[2])
        p[0] = p[1]


def p_statement(p):
    '''statement : compound_stmt
                 | declaration SEMICOLON
                 | expr_stmt
                 | selection_stmt
                 | iteration_stmt
                 | jump_stmt'''
    if len(p) == 3:
        p[0] = Node("stmt_decl", [p[1]])
    else:
        p[0] = Node("stmt", [p[1]])


def p_declaration(p):
    'declaration : type_specifier init_declarator_list'
    p[0] = Node("declaration", [p[1], p[2]])


def p_init_declarator_list(p):
    '''init_declarator_list : init_declarator
                            | init_declarator_list COMMA init_declarator'''
    if len(p) == 2:
        p[0] = Node("decl_list", [p[1]])
    else:
        p[1].children.append(p[3])
        p[0] = p[1]


def p_init_declarator(p):
    '''init_declarator : ID
                       | ID ASSIGN expression'''
    if len(p) == 2:
        p[0] = Node("init_decl", [Node("ID", value=p[1])])
    else:
        p[0] = Node("init_decl_assign", [Node("ID", value=p[1]), p[3]])


def p_expr_stmt(p):
    '''expr_stmt : SEMICOLON
                 | expression SEMICOLON'''
    if len(p) == 2:
        p[0] = Node("empty_stmt")
    else:
        p[0] = Node("expr_stmt", [p[1]])


def p_expr_stmt_missing_semicolon(p):
    'expr_stmt : expression error'
    print(f"Syntax error: expected ';' after expression near '{p[2].value}' on line {p.lineno(2)}")
    p[0] = Node("expr_stmt_error", [p[1]])


def p_selection_stmt(p):
    '''selection_stmt : IF LPAREN expression RPAREN statement
                      | IF LPAREN expression RPAREN statement ELSE statement'''
    if len(p) == 6:
        p[0] = Node("if_stmt", [p[3], p[5]])
    else:
        p[0] = Node("if_else_stmt", [p[3], p[5], p[7]])


def p_selection_stmt_missing_rparen(p):
    'selection_stmt : IF LPAREN expression error statement'
    print(f"Syntax error: missing ')' in if condition near '{p[4].value}' on line {p.lineno(4)}")
    p[0] = Node("if_stmt_error", [p[3], p[5]])


def p_iteration_stmt(p):
    'iteration_stmt : WHILE LPAREN expression RPAREN statement'
    p[0] = Node("while_stmt", [p[3], p[5]])


def p_iteration_stmt_missing_rparen(p):
    'iteration_stmt : WHILE LPAREN expression error statement'
    print(f"Syntax error: missing ')' in while condition near '{p[4].value}' on line {p.lineno(4)}")
    p[0] = Node("while_stmt_error", [p[3], p[5]])


def p_jump_stmt(p):
    '''jump_stmt : RETURN SEMICOLON
                 | RETURN expression SEMICOLON'''
    if len(p) == 3:
        p[0] = Node("return_stmt")
    else:
        p[0] = Node("return_stmt", [p[2]])


def p_jump_stmt_missing_semicolon(p):
    'jump_stmt : RETURN expression error'
    print(f"Syntax error: expected ';' after return expression near '{p[3].value}' on line {p.lineno(3)}")
    p[0] = Node("return_stmt_error", [p[2]])


def p_expression(p):
    '''expression : ID ASSIGN expression
                  | ID PLUS_EQ expression
                  | ID MINUS_EQ expression
                  | logical_or_expr'''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = Node("assign_expr", [Node("ID", value=p[1]), p[3]], value=p[2])


def p_logical_or_expr(p):
    '''logical_or_expr : logical_and_expr
                       | logical_or_expr OR logical_and_expr'''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = Node("or_expr", [p[1], p[3]])


def p_logical_and_expr(p):
    '''logical_and_expr : equality_expr
                        | logical_and_expr AND equality_expr'''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = Node("and_expr", [p[1], p[3]])


def p_equality_expr(p):
    '''equality_expr : relational_expr
                     | equality_expr EQ relational_expr
                     | equality_expr NE relational_expr'''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = Node("eq_expr", [p[1], p[3]], value=p[2])


def p_relational_expr(p):
    '''relational_expr : additive_expr
                       | relational_expr LT additive_expr
                       | relational_expr GT additive_expr
                       | relational_expr LE additive_expr
                       | relational_expr GE additive_expr'''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = Node("rel_expr", [p[1], p[3]], value=p[2])


def p_additive_expr(p):
    '''additive_expr : multiplicative_expr
                     | additive_expr PLUS multiplicative_expr
                     | additive_expr MINUS multiplicative_expr'''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = Node("add_expr", [p[1], p[3]], value=p[2])


def p_multiplicative_expr(p):
    '''multiplicative_expr : unary_expr
                           | multiplicative_expr MULT unary_expr
                           | multiplicative_expr DIV unary_expr
                           | multiplicative_expr MOD unary_expr'''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = Node("mul_expr", [p[1], p[3]], value=p[2])


def p_unary_expr(p):
    '''unary_expr : postfix_expr
                  | PLUS unary_expr
                  | MINUS unary_expr
                  | NOT unary_expr
                  | INC unary_expr
                  | DEC unary_expr'''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = Node("unary_expr", [p[2]], value=p[1])


def p_postfix_expr(p):
    '''postfix_expr : primary_expr
                    | postfix_expr LPAREN argument_expr_list RPAREN
                    | postfix_expr LPAREN RPAREN
                    | postfix_expr LBRACKET expression RBRACKET
                    | postfix_expr INC
                    | postfix_expr DEC'''
    if len(p) == 2:
        p[0] = p[1]
    elif len(p) == 3:
        p[0] = Node("postfix_incdec", [p[1]], value=p[2])
    elif p[2] == '(' and len(p) == 5:
        p[0] = Node("call", [p[1], p[3]])
    elif p[2] == '(' and len(p) == 4:
        p[0] = Node("call", [p[1]])
    else:
        p[0] = Node("subscript", [p[1], p[3]])


def p_argument_expr_list(p):
    '''argument_expr_list : expression
                          | argument_expr_list COMMA expression'''
    if len(p) == 2:
        p[0] = Node("args", [p[1]])
    else:
        p[1].children.append(p[3])
        p[0] = p[1]


def p_primary_expr(p):
    '''primary_expr : ID
                    | FUNCTION
                    | INT_CONST
                    | FLOAT_CONST
                    | LPAREN expression RPAREN'''
    if len(p) == 2:
        p[0] = Node("primary", value=p[1])
    else:
        p[0] = p[2]


def p_empty(p):
    'empty :'
    p[0] = Node("empty")


def p_error(p):
    if p:
        print(f"Syntax error at line {p.lineno} near '{p.value}'")
    else:
        print("Syntax error at EOF")


parser = yacc.yacc(debug=False, write_tables=True, debugfile="parser_debug.out")


def main():
    if len(sys.argv) < 2:
        print("Usage: python parser.py <filename>")
        sys.exit(1)

    filename = sys.argv[1]
    with open(filename, "r") as f:
        data = f.read()

    lexer.lineno = 1
    lexer.input(data)

    print(f"{'Lexeme':<15}{'Token Type':<15}{'Line'}")
    print("-" * 45)
    for tok in lexer:
        print(f"{str(tok.value):<15}{tok.type:<15}{tok.lineno}")
    print("-" * 45)

    lexer.lineno = 1
    lexer.input(data)
    tree = parser.parse(data, lexer=lexer)
    print("Parsing finished\n")
    if tree:
        print("Parse Tree:")
        print_tree(tree)


if __name__ == "__main__":
    main()
