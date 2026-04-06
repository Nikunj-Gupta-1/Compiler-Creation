import ply.yacc as yacc  # type: ignore
from lexer import tokens, lexer

import sys
from collections import defaultdict

# Grammar used for FIRST / FOLLOW analysis
grammar_first_follow = {
    "S": [["S", "S"], ["ID", "ASSIGN", "E", "SEMI"]],
    "E": [
        ["E", "PLUS",  "E"],
        ["E", "MINUS", "E"],
        ["E", "MUL",   "E"],
        ["E", "DIV",   "E"],
        ["E", "MOD",   "E"],
        ["E", "LT",    "E"],
        ["E", "GT",    "E"],
        ["E", "LE",    "E"],
        ["E", "GE",    "E"],
        ["E", "EQ",    "E"],
        ["E", "NEQ",   "E"],
        ["E", "AND",   "E"],
        ["E", "OR",    "E"],
        ["NOT", "E"],
        ["LPAREN", "E", "RPAREN"],
        ["ID"],
        ["INT"],
        ["FLOAT"],
    ],
}

FIRST  = defaultdict(set)
FOLLOW = defaultdict(set)


def compute_first():
    changed = True
    while changed:
        changed = False
        for A, productions in grammar_first_follow.items():
            for production in productions:
                for symbol in production:
                    if symbol not in grammar_first_follow:   # terminal
                        if symbol not in FIRST[A]:
                            FIRST[A].add(symbol)
                            changed = True
                        break
                    else:                                     # non-terminal
                        before = len(FIRST[A])
                        FIRST[A].update(FIRST[symbol])
                        if len(FIRST[A]) > before:
                            changed = True
                        break


def compute_follow():
    start = list(grammar_first_follow.keys())[0]
    FOLLOW[start].add("$")
    changed = True
    while changed:
        changed = False
        for A, productions in grammar_first_follow.items():
            for production in productions:
                for i, B in enumerate(production):
                    if B not in grammar_first_follow:
                        continue
                    if i + 1 < len(production):
                        beta = production[i + 1]
                        if beta not in grammar_first_follow:   # terminal
                            if beta not in FOLLOW[B]:
                                FOLLOW[B].add(beta)
                                changed = True
                        else:                                   # non-terminal
                            before = len(FOLLOW[B])
                            FOLLOW[B].update(FIRST[beta])
                            if len(FOLLOW[B]) > before:
                                changed = True
                    else:                                       # last symbol
                        before = len(FOLLOW[B])
                        FOLLOW[B].update(FOLLOW[A])
                        if len(FOLLOW[B]) > before:
                            changed = True


def print_first_follow():
    print("\n" + "=" * 60)
    print("FIRST / FOLLOW SETS")
    print("=" * 60)
    print("\n--- FIRST SETS ---")
    for nt in grammar_first_follow:
        print(f"  FIRST({nt:2}) = {sorted(FIRST[nt])}")
    print("\n--- FOLLOW SETS ---")
    for nt in grammar_first_follow:
        print(f"  FOLLOW({nt:2}) = {sorted(FOLLOW[nt])}")


# Simplified LL(1) grammar
grammar_ll1 = {
    "S":  [["id", "=", "E", ";"]],
    "E":  [["T", "E'"]],
    "E'": [["+", "T", "E'"], ["e"]],
    "T":  [["id"], ["num"]],
}


def construct_ll1_table():
    table = defaultdict(dict)
    for nt, productions in grammar_ll1.items():
        for prod in productions:
            first_sym = prod[0]
            if first_sym in grammar_first_follow:
                for f in FIRST[first_sym]:
                    table[nt][f] = prod
            else:
                table[nt][first_sym] = prod
    return table


def print_ll1_table(table):
    terminals = ["id", "num", "=", "+", ";", "$"]
    print("\n" + "=" * 60)
    print("LL(1) PARSING TABLE")
    print("=" * 60)
    print("NT   | " + " | ".join(f"{t:10}" for t in terminals))
    print("-" * 75)
    for nt in grammar_ll1:
        row = f"{nt:4} | "
        for t in terminals:
            cell = " ".join(table[nt][t]) if t in table[nt] else ""
            row += f"{cell:10} | "
        print(row)


def ll1_parse(input_tokens, table):
    stack = ["$", "S"]
    input_tokens = list(input_tokens) + ["$"]

    print("\n" + "=" * 60)
    print("LL(1) STACK TRACE  (demo: id = id + num ;)")
    print("=" * 60)
    print(f"  {'STACK':30} | {'INPUT BUFFER':30} | ACTION")
    print("  " + "-" * 80)

    while stack:
        top     = stack[-1]
        current = input_tokens[0]
        print(f"  {str(stack):30} | {str(input_tokens):30}", end=" | ")

        if top == "$" and current == "$":
            print("ACCEPT")
            break

        if top == current:
            print(f"Match '{current}'")
            stack.pop()
            input_tokens.pop(0)
        elif top in grammar_ll1:
            if current in table[top]:
                production = table[top][current]
                print(f"Expand: {top} -> {' '.join(production)}")
                stack.pop()
                if production != ["e"]:
                    stack.extend(reversed(production))
            else:
                print("ERROR – no rule in table")
                break
        else:
            print("ERROR – unexpected token")
            break

# SHIFT-REDUCE PARSER


def shift_reduce_parser(tokens):
    stack  = []
    tokens = list(tokens) + ["$"]

    print("\n--- Shift-Reduce Parsing ---")

    while True:
        # SHIFT
        stack.append(tokens.pop(0))
        print(f"  Stack: {stack}, Input: {tokens}")

        # REDUCE loop
        while True:
            # Identifiers / constants → F
            if stack and stack[-1] in ("ID", "INT", "FLOAT"):
                stack[-1] = "F"
                print("  Reduce: F → value")

            # Parenthesised expression
            elif len(stack) >= 3 and stack[-3:] == ["LPAREN", "E", "RPAREN"]:
                stack[-3:] = ["F"]
                print("  Reduce: F → ( E )")

            # Unary NOT
            elif len(stack) >= 2 and stack[-2:] == ["NOT", "F"]:
                stack[-2:] = ["E"]
                print("  Reduce: E → NOT E")

            # Multiplicative
            elif len(stack) >= 3 and stack[-3] in ("F", "E") and stack[-1] in ("F", "E") and stack[-2] == "MUL":
                stack[-3:] = ["E"]; print("  Reduce: E → E * E")
            elif len(stack) >= 3 and stack[-3] in ("F", "E") and stack[-1] in ("F", "E") and stack[-2] == "DIV":
                stack[-3:] = ["E"]; print("  Reduce: E → E / E")
            elif len(stack) >= 3 and stack[-3] in ("F", "E") and stack[-1] in ("F", "E") and stack[-2] == "MOD":
                stack[-3:] = ["E"]; print("  Reduce: E → E % E")

            # Additive
            elif len(stack) >= 3 and stack[-3] in ("F", "E") and stack[-1] in ("F", "E") and stack[-2] == "PLUS":
                stack[-3:] = ["E"]; print("  Reduce: E → E + E")
            elif len(stack) >= 3 and stack[-3] in ("F", "E") and stack[-1] in ("F", "E") and stack[-2] == "MINUS":
                stack[-3:] = ["E"]; print("  Reduce: E → E - E")

            # Relational
            elif len(stack) >= 3 and stack[-3] == "E" and stack[-1] == "E" and stack[-2] in ("LT","GT","LE","GE","EQ","NEQ"):
                op = stack[-2]; stack[-3:] = ["E"]; print(f"  Reduce: E → E {op} E")

            # Boolean
            elif len(stack) >= 3 and stack[-3] == "E" and stack[-1] == "E" and stack[-2] == "AND":
                stack[-3:] = ["E"]; print("  Reduce: E → E && E")
            elif len(stack) >= 3 and stack[-3] == "E" and stack[-1] == "E" and stack[-2] == "OR":
                stack[-3:] = ["E"]; print("  Reduce: E → E || E")

            # F → E (base promotion)
            elif stack and stack[-1] == "F":
                stack[-1] = "E"; print("  Reduce: E → F")

            # Assignment statement
            elif len(stack) >= 4 and stack[-4:] == ["E", "ASSIGN", "E", "SEMI"]:
                stack[-4:] = ["E"]; print("  Reduce: E → ID = E ;")

            # Multiple statements on stack
            elif len(stack) >= 2 and stack[-2:] == ["E", "E"]:
                stack[-2:] = ["E"]; print("  Reduce: E → E E")

            else:
                break

        if stack in (["E", "$"], ["E"]) and tokens in (["$"], []):
            print("  ✅ Accepted")
            break
        if tokens and tokens[0] == "$":
            print("  ❌ Rejected")
            break



# MAIN PARSER


def run_lalr_parser(data):
    """Run the PLY LALR(1) parser. Requires 'ply' and a 'lexer' module."""
    try:
        import ply.yacc as yacc          # type: ignore
        from lexer import tokens as lex_tokens, lexer  # type: ignore
    except ImportError as e:
        print(f"\n[LALR Parser] Skipped – missing dependency: {e}")
        return None

    class Node:
        def __init__(self, ntype, children=None, leaf=None):
            self.type     = ntype
            self.children = children or []
            self.leaf     = leaf

        def print_tree(self, indent=0):
            label = self.type + (f": {self.leaf}" if self.leaf else "")
            print("  " * indent + label)
            for child in self.children:
                if isinstance(child, Node):
                    child.print_tree(indent + 1)
                else:
                    print("  " * (indent + 1) + str(child))

    precedence = (
        ("left",  "OR"),
        ("left",  "AND"),
        ("left",  "EQ", "NEQ"),
        ("left",  "LT", "LE", "GT", "GE"),
        ("left",  "PLUS", "MINUS"),
        ("left",  "MUL", "DIV", "MOD"),
        ("right", "NOT"),
    )

    parse_tree_holder = [None]

    # --- grammar rules ---
    def p_program(p):
        '''program : decl_list stmt_list'''
        p[0] = Node("program", [p[1], p[2]])
        print("  Valid program")
        parse_tree_holder[0] = p[0]

    def p_decl_list(p):
        '''decl_list : decl decl_list
                     | empty'''
        p[0] = Node("decl_list", [p[1], p[2]]) if len(p) == 3 else Node("decl_list")

    def p_decl(p):
        '''decl : type ID SEMI'''
        p[0] = Node("decl", [p[1]], p[2])

    def p_type(p):
        '''type : INT_TYPE
               | FLOAT_TYPE'''
        p[0] = Node("type", leaf=p[1])

    def p_stmt_list(p):
        '''stmt_list : stmt stmt_list
                     | empty'''
        p[0] = Node("stmt_list", [p[1], p[2]]) if len(p) == 3 else Node("stmt_list")

    def p_stmt(p):
        '''stmt : assign_stmt
               | if_stmt
               | while_stmt
               | block
               | decl
               | print_stmt'''
        p[0] = Node("stmt", [p[1]])

    def p_assign_stmt(p):
        '''assign_stmt : ID ASSIGN expr SEMI'''
        p[0] = Node("assign_stmt", [p[3]], p[1])

    def p_expr(p):
        '''expr : expr PLUS  term
               | expr MINUS term
               | term'''
        p[0] = p[1] if len(p) == 2 else Node("expr", [p[1], p[3]], p[2])

    def p_term(p):
        '''term : term MUL factor
               | term DIV factor
               | term MOD factor
               | factor'''
        p[0] = p[1] if len(p) == 2 else Node("term", [p[1], p[3]], p[2])

    def p_factor(p):
        '''factor : LPAREN expr RPAREN
               | ID
               | INT
               | FLOAT'''
        p[0] = Node("factor", [p[2]]) if len(p) == 4 else Node("factor", leaf=p[1])

    def p_bool_expr(p):
        '''bool_expr : bool_expr OR bool_term
                    | bool_term'''
        p[0] = p[1] if len(p) == 2 else Node("bool_expr", [p[1], p[3]], p[2])

    def p_bool_term(p):
        '''bool_term : bool_term AND bool_factor
                    | bool_factor'''
        p[0] = p[1] if len(p) == 2 else Node("bool_term", [p[1], p[3]], p[2])

    def p_bool_factor(p):
        '''bool_factor : NOT bool_factor
                      | LPAREN bool_expr RPAREN
                      | rel_expr'''
        if len(p) == 2:
            p[0] = p[1]
        elif len(p) == 3:
            p[0] = Node("NOT", [p[2]])
        else:
            p[0] = Node("bool_factor", [p[2]])

    def p_rel_expr(p):
        '''rel_expr : expr LT  expr
                    | expr GT  expr
                    | expr LE  expr
                    | expr GE  expr
                    | expr EQ  expr
                    | expr NEQ expr'''
        p[0] = Node("rel_expr", [p[1], p[3]], p[2])

    def p_while_stmt(p):
        '''while_stmt : WHILE LPAREN bool_expr RPAREN stmt'''
        p[0] = Node("while_stmt", [p[3], p[5]])

    def p_if_stmt(p):
        '''if_stmt : IF LPAREN bool_expr RPAREN stmt ELSE stmt'''
        p[0] = Node("if_stmt", [p[3], p[5], p[7]])

    def p_block(p):
        '''block : LCURLY stmt_list RCURLY'''
        p[0] = Node("block", [p[2]])

    def p_print_stmt(p):
        '''print_stmt : PRINT LPAREN expr RPAREN SEMI'''
        p[0] = Node("print_stmt", [p[3]])

    def p_empty(p):
        'empty :'
        p[0] = Node("empty")

    # --- error handling ---
    _src = [data]

    def _find_column(text, tok):
        last_cr = text.rfind("\n", 0, tok.lexpos)
        return tok.lexpos - last_cr

    def _suggest(tok, text):
        if not tok:
            return "Unexpected EOF – missing '}', ')', or ';' ?"
        t = tok.type
        if t == "ID":     return "Missing ';' or operator before this identifier."
        if t in ("INT", "FLOAT"): return "Missing operator before literal, or extra ';' after previous statement."
        if t == "RCURLY": return "Unexpected '}' – unmatched or missing corresponding block."
        if t == "LCURLY": return "Unexpected '{' – check preceding if/while syntax."
        if t == "RPAREN": return "Unexpected ')' – check matching '('."
        if t == "LPAREN": return "Unexpected '(' – check preceding if/while/function syntax."
        if t == "SEMI":   return "Extra ';' or missing statement before it."
        if t in ("PLUS","MINUS","MUL","DIV","MOD"): return "Missing operand around this operator."
        if t in ("IF","ELSE","WHILE"): return f"Misplaced '{tok.value}' – check control-flow syntax."
        return "Check for missing ';', ')', or '}'."

    def p_error(p):
        if p:
            line   = p.lineno
            col    = _find_column(_src[0], p)
            hint   = _suggest(p, _src[0])
            lines  = _src[0].splitlines()
            ltext  = lines[line - 1] if 0 < line <= len(lines) else ""
            print(f"\nSyntax Error: unexpected '{p.value}' ({p.type}) at line {line}, col {col}")
            if ltext:
                print(f"  {line}: {ltext}")
                print("  " + " " * (len(str(line)) + 2 + col - 1) + "^")
            print(f"  Hint: {hint}")
        else:
            print("\nSyntax Error: unexpected EOF")
            print("  Hint: Missing '}', ')', or ';' before end of file.")
        sys.exit(1)

    lalr_parser = yacc.yacc(debug=False, write_tables=False)

    print("\n" + "=" * 60)
    print("PLY LALR(1) PARSER")
    print("=" * 60)
    _src[0] = data
    lalr_parser.parse(data, lexer=lexer)

    tree = parse_tree_holder[0]
    if tree:
        print("\nParse Tree:")
        tree.print_tree()
    return tree


def get_token_stream(line):
    """Tokenise a single source line using the PLY lexer."""
    try:
        from lexer import lexer  # type: ignore
    except ImportError:
        return []
    lexer.input(line)
    toks = []
    while True:
        tok = lexer.token()
        if not tok:
            break
        toks.append(tok.type)
    return toks


def is_assignment(tokens):
    """Return True for lines of the form: ID ASSIGN ... SEMI"""
    return (
        len(tokens) >= 4
        and tokens[0] == "ID"
        and tokens[1] == "ASSIGN"
        and tokens[-1] == "SEMI"
    )


def run_shift_reduce_on_file(data):
    """Run the shift-reduce demo on each statement in the source file."""
    print("\n" + "=" * 60)
    print("SHIFT-REDUCE DEMO (per statement)")
    print("=" * 60)
    for raw_line in data.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        tokens = get_token_stream(line)
        if not tokens:
            continue
        print("\n" + "-" * 50)
        print(f"  Statement   : {line}")
        print(f"  Token stream: {tokens}")
        if is_assignment(tokens):
            shift_reduce_parser(tokens.copy())
        else:
            print("  (Skipping – not a simple assignment expression)")


def main():
    # ── 1. FIRST / FOLLOW ──────────────────────────────────────────────────
    compute_first()
    compute_follow()
    print_first_follow()

    # ── 2. LL(1) TABLE + DEMO TRACE ────────────────────────────────────────
    table = construct_ll1_table()
    print_ll1_table(table)
    ll1_parse(["id", "=", "id", "+", "num", ";"], table)

    # ── 3 & 4. PLY LALR(1) + SHIFT-REDUCE on source file ──────────────────
    if len(sys.argv) < 2:
        print("\nUsage: python combined_parser.py <source_file>")
        print("(Skipping file-based passes – no source file provided)")
        return

    src_path = sys.argv[1]
    try:
        with open(src_path, "r") as fh:
            data = fh.read()
    except FileNotFoundError:
        print(f"Error: file '{src_path}' not found.")
        sys.exit(1)

    # PLY LALR(1) pass (needs ply + lexer.py)
    run_lalr_parser(data)

    # Shift-Reduce demo pass (needs lexer.py)
    run_shift_reduce_on_file(data)


if __name__ == "__main__":
    main()
