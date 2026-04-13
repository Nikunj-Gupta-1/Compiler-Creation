import io
import sys
from contextlib import redirect_stdout

import ply.yacc as yacc # type: ignore
from lexer import tokens, lexer
from semantic_analyzer import SemanticAnalyzer


class Node:
    def __init__(self, ntype, children=None, leaf=None, lineno=None):
        self.type = ntype
        self.children = children or []
        self.leaf = leaf
        self.lineno = lineno

    def print_tree(self, indent=0):
        label = self.type if self.leaf is None else f"{self.type}: {self.leaf}"
        print('  ' * indent + label)
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
    ('right', 'NOT')
)

parse_tree_holder = {'tree': None}
source_text = ''


def p_program(p):
    'program : decllist stmtlist'
    p[0] = Node('program', [p[1], p[2]], lineno=1)
    parse_tree_holder['tree'] = p[0]


def p_decllist_rec(p):
    'decllist : decl decllist'
    p[0] = Node('decllist', [p[1]] + p[2].children, lineno=p[1].lineno)


def p_decllist_empty(p):
    'decllist : empty'
    p[0] = Node('decllist', [], lineno=0)


def p_decl(p):
    'decl : type ID SEMI'
    p[0] = Node('decl', [p[1]], leaf=p[2], lineno=p.lineno(2))


def p_type_int(p):
    'type : INTTYPE'
    p[0] = Node('type', leaf='int', lineno=p.lineno(1))


def p_type_float(p):
    'type : FLOATTYPE'
    p[0] = Node('type', leaf='float', lineno=p.lineno(1))


def p_type_bool(p):
    'type : BOOLTYPE'
    p[0] = Node('type', leaf='bool', lineno=p.lineno(1))


def p_stmtlist_rec(p):
    'stmtlist : stmt stmtlist'
    p[0] = Node('stmtlist', [p[1]] + p[2].children, lineno=p[1].lineno)


def p_stmtlist_empty(p):
    'stmtlist : empty'
    p[0] = Node('stmtlist', [], lineno=0)


def p_stmt_assign(p):
    'stmt : assignstmt'
    p[0] = Node('stmt', [p[1]], lineno=p[1].lineno)


def p_stmt_if(p):
    'stmt : ifstmt'
    p[0] = Node('stmt', [p[1]], lineno=p[1].lineno)


def p_stmt_while(p):
    'stmt : whilestmt'
    p[0] = Node('stmt', [p[1]], lineno=p[1].lineno)


def p_stmt_block(p):
    'stmt : block'
    p[0] = Node('stmt', [p[1]], lineno=p[1].lineno)


def p_stmt_decl(p):
    'stmt : decl'
    p[0] = Node('stmt', [p[1]], lineno=p[1].lineno)


def p_stmt_print(p):
    'stmt : printstmt'
    p[0] = Node('stmt', [p[1]], lineno=p[1].lineno)


def p_assignstmt(p):
    'assignstmt : ID ASSIGN expr SEMI'
    p[0] = Node('assignstmt', [p[3]], leaf=p[1], lineno=p.lineno(1))


def p_ifstmt(p):
    'ifstmt : IF LPAREN expr RPAREN stmt ELSE stmt'
    p[0] = Node('ifstmt', [p[3], p[5], p[7]], lineno=p.lineno(1))


def p_whilestmt(p):
    'whilestmt : WHILE LPAREN expr RPAREN stmt'
    p[0] = Node('whilestmt', [p[3], p[5]], lineno=p.lineno(1))


def p_block(p):
    'block : LCURLY stmtlist RCURLY'
    p[0] = Node('block', [p[2]], lineno=p.lineno(1))


def p_printstmt(p):
    'printstmt : PRINT LPAREN expr RPAREN SEMI'
    p[0] = Node('printstmt', [p[3]], lineno=p.lineno(1))


def p_expr_binop(p):
    '''expr : expr PLUS expr
            | expr MINUS expr
            | expr MUL expr
            | expr DIV expr
            | expr MOD expr
            | expr LT expr
            | expr GT expr
            | expr LE expr
            | expr GE expr
            | expr EQ expr
            | expr NEQ expr
            | expr AND expr
            | expr OR expr'''
    lexeme = {
        'PLUS': '+', 'MINUS': '-', 'MUL': '*', 'DIV': '/', 'MOD': '%',
        'LT': '<', 'GT': '>', 'LE': '<=', 'GE': '>=', 'EQ': '==', 'NEQ': '!=', 'AND': '&&', 'OR': '||'
    }[p.slice[2].type]
    p[0] = Node('expr', [p[1], p[3]], leaf=lexeme, lineno=p.lineno(2))


def p_expr_not(p):
    'expr : NOT expr'
    p[0] = Node('notexpr', [p[2]], lineno=p.lineno(1))


def p_expr_group(p):
    'expr : LPAREN expr RPAREN'
    p[0] = Node('factor', [p[2]], lineno=p.lineno(1))


def p_expr_id(p):
    'expr : ID'
    p[0] = Node('factor', leaf=p[1], lineno=p.lineno(1))


def p_expr_int(p):
    'expr : INT'
    p[0] = Node('factor', leaf=p[1], lineno=p.lineno(1))


def p_expr_float(p):
    'expr : FLOAT'
    p[0] = Node('factor', leaf=p[1], lineno=p.lineno(1))


def p_expr_true(p):
    'expr : TRUE'
    p[0] = Node('factor', leaf=True, lineno=p.lineno(1))


def p_expr_false(p):
    'expr : FALSE'
    p[0] = Node('factor', leaf=False, lineno=p.lineno(1))


def p_empty(p):
    'empty :'
    p[0] = Node('empty', [], lineno=0)


def find_column(text, tok):
    last_cr = text.rfind('\n', 0, tok.lexpos)
    if last_cr < 0:
        last_cr = -1
    return tok.lexpos - last_cr


def p_error(p):
    if p:
        print(f"Syntax Error: unexpected '{p.value}' ({p.type}) at line {p.lineno}, col {find_column(source_text, p)}")
    else:
        print('Syntax Error: unexpected EOF')
    sys.exit(1)


parser = yacc.yacc(debug=False, write_tables=False)


def format_lalr_debug_trace(debug_text):
    rows = []
    state = stack = action = None
    for raw in debug_text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith('State'):
            if state or stack or action:
                rows.append((state or '', stack or '', action or ''))
            state = line.replace('State', '').strip()
            stack = ''
            action = ''
        elif line.startswith('Stack'):
            stack = line.split(':', 1)[1].strip()
        elif line.startswith('Action') or line.startswith('Result') or line.startswith('Done'):
            text = line.split(':', 1)[1].strip() if ':' in line else line
            action = f"{action} {text}".strip()
    if state or stack or action:
        rows.append((state or '', stack or '', action or ''))
    print('=' * 110)
    print('LALR STACK TRACE')
    print('=' * 110)
    print(f"{'STEP':<8}{'STATE':<10}{'STACK':<45}{'ACTION'}")
    print('-' * 110)
    for i, (state, stack, action) in enumerate(rows, start=1):
        print(f"{i:<8}{state:<10}{stack:<45}{action}")


def run_parser(data, show_trace=True):
    global source_text
    source_text = data
    parse_tree_holder['tree'] = None
    buf = io.StringIO()
    if show_trace:
        with redirect_stdout(buf):
            parser.parse(data, lexer=lexer, debug=1)
        format_lalr_debug_trace(buf.getvalue())
    else:
        parser.parse(data, lexer=lexer)
    tree = parse_tree_holder['tree']
    if tree:
        print('=' * 70)
        print('PARSE TREE')
        print('=' * 70)
        tree.print_tree()
        analyzer = SemanticAnalyzer()
        analyzer.analyze(tree)
        print('=' * 70)
        print('SYMBOL TABLES')
        print('=' * 70)
        analyzer.print_symbol_tables()
        print('=' * 70)
        print('SEMANTIC ANALYSIS')
        print('=' * 70)
        analyzer.report()
    return tree


def main():
    if len(sys.argv) < 2:
        print('Usage: python parser.py <sourcefile>')
        sys.exit(1)
    path = sys.argv[1]
    with open(path, 'r') as f:
        data = f.read()
    run_parser(data, show_trace=True)


if __name__ == '__main__':
    main()
