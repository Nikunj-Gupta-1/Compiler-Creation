import sys
import ply.yacc as yacc # type: ignore
from py1 import tokens, lexer


def p_program(p):
    'program : global_list'
    pass


def p_global_list(p):
    '''global_list : global
                   | global_list global'''
    pass


def p_global(p):
    '''global : declaration SEMICOLON
              | function_def
              | statement'''
    pass


def p_function_def(p):
    'function_def : type_specifier func_name LPAREN param_list RPAREN compound_stmt'
    pass


def p_func_name(p):
    '''func_name : ID
                 | FUNCTION'''
    pass


def p_param_list(p):
    '''param_list : empty
                  | param_decl
                  | param_list COMMA param_decl'''
    pass


def p_param_decl(p):
    'param_decl : type_specifier ID'
    pass


def p_type_specifier(p):
    'type_specifier : KEYWORD'
    pass


def p_compound_stmt(p):
    'compound_stmt : LBRACE stmt_list RBRACE'
    pass


def p_compound_stmt_error(p):
    'compound_stmt : LBRACE stmt_list error'
    print(f"Syntax error: missing '}}' for block before token '{p[3].value}' on line {p.lineno(3)}")


def p_stmt_list(p):
    '''stmt_list : empty
                 | stmt_list statement'''
    pass


def p_statement(p):
    '''statement : compound_stmt
                 | declaration SEMICOLON
                 | expr_stmt
                 | selection_stmt
                 | iteration_stmt
                 | jump_stmt'''
    pass


def p_declaration(p):
    'declaration : type_specifier init_declarator_list'
    pass


def p_init_declarator_list(p):
    '''init_declarator_list : init_declarator
                            | init_declarator_list COMMA init_declarator'''
    pass


def p_init_declarator(p):
    '''init_declarator : ID
                       | ID ASSIGN expression'''
    pass


def p_expr_stmt(p):
    '''expr_stmt : SEMICOLON
                 | expression SEMICOLON'''
    pass


def p_expr_stmt_missing_semicolon(p):
    'expr_stmt : expression error'
    print(f"Syntax error: expected ';' after expression near '{p[2].value}' on line {p.lineno(2)}")


def p_selection_stmt(p):
    '''selection_stmt : IF LPAREN expression RPAREN statement
                      | IF LPAREN expression RPAREN statement ELSE statement'''
    pass


def p_selection_stmt_missing_rparen(p):
    'selection_stmt : IF LPAREN expression error statement'
    print(f"Syntax error: missing ')' in if condition near '{p[4].value}' on line {p.lineno(4)}")


def p_iteration_stmt(p):
    'iteration_stmt : WHILE LPAREN expression RPAREN statement'
    pass


def p_iteration_stmt_missing_rparen(p):
    'iteration_stmt : WHILE LPAREN expression error statement'
    print(f"Syntax error: missing ')' in while condition near '{p[4].value}' on line {p.lineno(4)}")


def p_jump_stmt(p):
    '''jump_stmt : RETURN SEMICOLON
                 | RETURN expression SEMICOLON'''
    pass


def p_jump_stmt_missing_semicolon(p):
    'jump_stmt : RETURN expression error'
    print(f"Syntax error: expected ';' after return expression near '{p[3].value}' on line {p.lineno(3)}")


def p_expression(p):
    '''expression : ID ASSIGN expression
                  | ID PLUS_EQ expression
                  | ID MINUS_EQ expression
                  | logical_or_expr'''
    pass


def p_logical_or_expr(p):
    '''logical_or_expr : logical_and_expr
                       | logical_or_expr OR logical_and_expr'''
    pass


def p_logical_and_expr(p):
    '''logical_and_expr : equality_expr
                        | logical_and_expr AND equality_expr'''
    pass


def p_equality_expr(p):
    '''equality_expr : relational_expr
                     | equality_expr EQ relational_expr
                     | equality_expr NE relational_expr'''
    pass


def p_relational_expr(p):
    '''relational_expr : additive_expr
                       | relational_expr LT additive_expr
                       | relational_expr GT additive_expr
                       | relational_expr LE additive_expr
                       | relational_expr GE additive_expr'''
    pass


def p_additive_expr(p):
    '''additive_expr : multiplicative_expr
                     | additive_expr PLUS multiplicative_expr
                     | additive_expr MINUS multiplicative_expr'''
    pass


def p_multiplicative_expr(p):
    '''multiplicative_expr : unary_expr
                           | multiplicative_expr MULT unary_expr
                           | multiplicative_expr DIV unary_expr
                           | multiplicative_expr MOD unary_expr'''
    pass


def p_unary_expr(p):
    '''unary_expr : postfix_expr
                  | PLUS unary_expr
                  | MINUS unary_expr
                  | NOT unary_expr
                  | INC unary_expr
                  | DEC unary_expr'''
    pass


def p_postfix_expr(p):
    '''postfix_expr : primary_expr
                    | postfix_expr LPAREN argument_expr_list RPAREN
                    | postfix_expr LPAREN RPAREN
                    | postfix_expr LBRACKET expression RBRACKET
                    | postfix_expr INC
                    | postfix_expr DEC'''
    pass


def p_argument_expr_list(p):
    '''argument_expr_list : expression
                          | argument_expr_list COMMA expression'''
    pass


def p_primary_expr(p):
    '''primary_expr : ID
                    | FUNCTION
                    | INT_CONST
                    | FLOAT_CONST
                    | LPAREN expression RPAREN'''
    pass


def p_empty(p):
    'empty :'
    pass


def p_error(p):
    if p:
        print(f"Syntax error at line {p.lineno} near '{p.value}'")
    else:
        print("Syntax error at EOF")


parser = yacc.yacc()


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
    result = parser.parse(data, lexer=lexer)
    print("Parsing finished")


if __name__ == "__main__":
    main()
