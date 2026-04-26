import ply.yacc as yacc #type: ignore
from lexer import tokens, lexer
import sys
import io
from contextlib import redirect_stdout, redirect_stderr
from collections import defaultdict


grammar = {
    "program": [["decl_list", "stmt_list"]],
    "decl_list": [["decl", "decl_list"], ["ε"]],
    "decl": [["type", "ID", "SEMI"]],
    "type": [["INT_TYPE"], ["FLOAT_TYPE"]],
    "stmt_list": [["stmt", "stmt_list"], ["ε"]],
    "stmt": [["assign_stmt"], ["if_stmt"], ["while_stmt"], ["block"], ["print_stmt"]],
    "assign_stmt": [["ID", "ASSIGN", "expr", "SEMI"]],
    "expr": [["expr", "PLUS", "term"], ["expr", "MINUS", "term"], ["term"]],
    "term": [["term", "MUL", "factor"], ["term", "DIV", "factor"], ["term", "MOD", "factor"], ["factor"]],
    "factor": [["LPAREN", "expr", "RPAREN"], ["ID"], ["INT"], ["FLOAT"]],
    "bool_expr": [["bool_expr", "OR", "bool_term"], ["bool_term"]],
    "bool_term": [["bool_term", "AND", "bool_factor"], ["bool_factor"]],
    "bool_factor": [["NOT", "bool_factor"], ["LPAREN", "bool_expr", "RPAREN"], ["rel_expr"]],
    "rel_expr": [["expr", "LT", "expr"], ["expr", "GT", "expr"], ["expr", "LE", "expr"],
                 ["expr", "GE", "expr"], ["expr", "EQ", "expr"], ["expr", "NEQ", "expr"]],
    "if_stmt": [["IF", "LPAREN", "bool_expr", "RPAREN", "stmt", "ELSE", "stmt"], ["IF", "LPAREN", "bool_expr", "RPAREN", "stmt"]],
    "while_stmt": [["WHILE", "LPAREN", "bool_expr", "RPAREN", "stmt"]],
    "block": [["LCURLY", "stmt_list", "RCURLY"]],
    "print_stmt": [["PRINT", "LPAREN", "expr", "RPAREN", "SEMI"]],
}

TERMINALS = set()
NONTERMINALS = set(grammar.keys())
for prods in grammar.values():
    for prod in prods:
        for sym in prod:
            if sym not in NONTERMINALS and sym != "ε":
                TERMINALS.add(sym)

FIRST = defaultdict(set)
FOLLOW = defaultdict(set)


def compute_first():
    for t in TERMINALS:
        FIRST[t].add(t)
    FIRST["ε"].add("ε")
    changed = True
    while changed:
        changed = False
        for A, productions in grammar.items():
            for prod in productions:
                for i, sym in enumerate(prod):
                    if sym == "ε":
                        if "ε" not in FIRST[A]:
                            FIRST[A].add("ε")
                            changed = True
                        break
                    before = len(FIRST[A])
                    FIRST[A].update(FIRST[sym] - {"ε"})
                    if len(FIRST[A]) > before:
                        changed = True
                    if "ε" not in FIRST[sym]:
                        break
                else:
                    if "ε" not in FIRST[A]:
                        FIRST[A].add("ε")
                        changed = True


def compute_follow():
    start = list(grammar.keys())[0]
    FOLLOW[start].add("$")
    changed = True
    while changed:
        changed = False
        for A, productions in grammar.items():
            for prod in productions:
                for i, B in enumerate(prod):
                    if B not in NONTERMINALS:
                        continue
                    rest = prod[i + 1:]
                    first_rest = set()
                    all_nullable = True
                    for sym in rest:
                        first_rest.update(FIRST[sym] - {"ε"})
                        if "ε" not in FIRST[sym]:
                            all_nullable = False
                            break
                    if not rest:
                        all_nullable = True
                    before = len(FOLLOW[B])
                    FOLLOW[B].update(first_rest)
                    if all_nullable:
                        FOLLOW[B].update(FOLLOW[A])
                    if len(FOLLOW[B]) > before:
                        changed = True


def print_first_follow():
    print("=" * 60)
    print(" 1: PARSER IMPLEMENTATION")
    print("=" * 60)
    print("\n--- FIRST SETS ---")
    for nt in grammar:
        print(f"  FIRST({nt}) = {{ {', '.join(sorted(FIRST[nt]))} }}")
    print("\n--- FOLLOW SETS ---")
    for nt in grammar:
        print(f"  FOLLOW({nt}) = {{ {', '.join(sorted(FOLLOW[nt]))} }}")


ll1_grammar = {
    "S":   [["id", "=", "E", ";"]],
    "E":   [["T", "E'"]],
    "E'":  [["+", "T", "E'"], ["-", "T", "E'"], ["ε"]],
    "T":   [["F", "T'"]],
    "T'":  [["*", "F", "T'"], ["/", "F", "T'"], ["ε"]],
    "F":   [["(", "E", ")"], ["id"], ["num"]],
}

FIRST_LL1 = defaultdict(set)
FOLLOW_LL1 = defaultdict(set)
LL1_NT = set(ll1_grammar.keys())


def compute_first_ll1():
    ll1_terminals = set()
    for prods in ll1_grammar.values():
        for prod in prods:
            for sym in prod:
                if sym not in LL1_NT and sym != "ε":
                    ll1_terminals.add(sym)
    for t in ll1_terminals:
        FIRST_LL1[t].add(t)
    FIRST_LL1["ε"].add("ε")
    changed = True
    while changed:
        changed = False
        for A, productions in ll1_grammar.items():
            for prod in productions:
                for sym in prod:
                    if sym == "ε":
                        if "ε" not in FIRST_LL1[A]:
                            FIRST_LL1[A].add("ε")
                            changed = True
                        break
                    before = len(FIRST_LL1[A])
                    FIRST_LL1[A].update(FIRST_LL1[sym] - {"ε"})
                    if len(FIRST_LL1[A]) > before:
                        changed = True
                    if "ε" not in FIRST_LL1[sym]:
                        break
                else:
                    if "ε" not in FIRST_LL1[A]:
                        FIRST_LL1[A].add("ε")
                        changed = True


def compute_follow_ll1():
    FOLLOW_LL1["S"].add("$")
    changed = True
    while changed:
        changed = False
        for A, productions in ll1_grammar.items():
            for prod in productions:
                for i, B in enumerate(prod):
                    if B not in LL1_NT:
                        continue
                    rest = prod[i + 1:]
                    first_rest = set()
                    all_nullable = True
                    for sym in rest:
                        first_rest.update(FIRST_LL1[sym] - {"ε"})
                        if "ε" not in FIRST_LL1[sym]:
                            all_nullable = False
                            break
                    if not rest:
                        all_nullable = True
                    before = len(FOLLOW_LL1[B])
                    FOLLOW_LL1[B].update(first_rest)
                    if all_nullable:
                        FOLLOW_LL1[B].update(FOLLOW_LL1[A])
                    if len(FOLLOW_LL1[B]) > before:
                        changed = True


def first_of_string_ll1(symbols):
    result = set()
    for sym in symbols:
        result.update(FIRST_LL1[sym] - {"ε"})
        if "ε" not in FIRST_LL1[sym]:
            return result
    result.add("ε")
    return result


def construct_ll1_table():
    compute_first_ll1()
    compute_follow_ll1()
    table = defaultdict(dict)
    for A, productions in ll1_grammar.items():
        for prod in productions:
            fp = first_of_string_ll1(prod)
            for t in fp:
                if t != "ε":
                    table[A][t] = prod
            if "ε" in fp:
                for t in FOLLOW_LL1[A]:
                    table[A][t] = prod
    return table


def print_ll1_table(table):
    terminals = sorted({t for row in table.values() for t in row})
    print("\n--- LL(1) PARSING TABLE ---")
    header = f"  {'NT':<6}|"
    for t in terminals:
        header += f" {t:<16}|"
    print(header)
    print("  " + "-" * (len(terminals) * 18 + 8))
    for nt in ll1_grammar:
        row = f"  {nt:<6}|"
        for t in terminals:
            cell = " ".join(table[nt][t]) if t in table[nt] else ""
            row += f" {cell:<16}|"
        print(row)


def ll1_parse(input_tokens, table):
    stack = ["$", "S"]
    buf = list(input_tokens) + ["$"]
    print("\n--- LL(1) STACK TRACE ---")
    print(f"  Input: {' '.join(input_tokens)}")
    print(f"\n  {'STACK':<35}{'INPUT':<35}{'ACTION'}")
    print("  " + "-" * 95)
    step = 0
    while stack:
        step += 1
        top = stack[-1]
        cur = buf[0]
        s_str = " ".join(stack)
        b_str = " ".join(buf)
        if top == "$" and cur == "$":
            print(f"  {s_str:<35}{b_str:<35}ACCEPT")
            break
        if top == cur:
            print(f"  {s_str:<35}{b_str:<35}Match '{cur}'")
            stack.pop()
            buf.pop(0)
        elif top in ll1_grammar:
            if cur in table[top]:
                prod = table[top][cur]
                prod_str = " ".join(prod)
                print(f"  {s_str:<35}{b_str:<35}{top} -> {prod_str}")
                stack.pop()
                if prod != ["ε"]:
                    stack.extend(reversed(prod))
            else:
                print(f"  {s_str:<35}{b_str:<35}ERROR")
                break
        else:
            print(f"  {s_str:<35}{b_str:<35}ERROR")
            break


def shift_reduce_parse(tok_stream):
    stack = []
    buf = list(tok_stream) + ["$"]
    print("\n--- SHIFT-REDUCE STACK TRACE ---")
    print(f"  Input: {' '.join(tok_stream)}")
    print(f"\n  {'STACK':<40}{'INPUT':<30}{'ACTION'}")
    print("  " + "-" * 90)

    def pr(action):
        s_str = " ".join(stack) if stack else "(empty)"
        b_str = " ".join(buf)
        print(f"  {s_str:<40}{b_str:<30}{action}")

    while True:
        tok = buf.pop(0)
        stack.append(tok)
        pr(f"Shift '{tok}'")
        if tok == "$":
            clean = [s for s in stack if s != "$"]
            if len(clean) == 1 and clean[0] in ("E", "S"):
                pr("ACCEPT")
            else:
                pr("REJECT")
            break
        reduced = True
        while reduced:
            reduced = False
            if stack[-1] in ("ID", "INT", "FLOAT"):
                old = stack[-1]
                stack[-1] = "F"
                pr(f"Reduce F -> {old}")
                reduced = True
                continue
            if len(stack) >= 3 and stack[-3:] == ["LPAREN", "E", "RPAREN"]:
                stack[-3:] = ["F"]
                pr("Reduce F -> ( E )")
                reduced = True
                continue
            if stack[-1] == "F":
                stack[-1] = "T"
                pr("Reduce T -> F")
                reduced = True
                continue
            if len(stack) >= 3 and stack[-3] == "T" and stack[-2] in ("MUL", "DIV", "MOD") and stack[-1] == "T":
                op = stack[-2]
                stack[-3:] = ["T"]
                pr(f"Reduce T -> T {op} T")
                reduced = True
                continue
            if stack[-1] == "T" and (len(stack) < 2 or stack[-2] not in ("MUL", "DIV", "MOD")):
                peek = buf[0] if buf else "$"
                if peek not in ("MUL", "DIV", "MOD"):
                    stack[-1] = "E"
                    pr("Reduce E -> T")
                    reduced = True
                    continue
            if len(stack) >= 3 and stack[-3] == "E" and stack[-2] in ("PLUS", "MINUS") and stack[-1] == "E":
                peek = buf[0] if buf else "$"
                if peek not in ("PLUS", "MINUS", "MUL", "DIV", "MOD"):
                    op = stack[-2]
                    stack[-3:] = ["E"]
                    pr(f"Reduce E -> E {op} E")
                    reduced = True
                    continue
            if len(stack) >= 3 and stack[-3] == "E" and stack[-1] == "E" and stack[-2] in ("LT", "GT", "LE", "GE", "EQ", "NEQ"):
                op = stack[-2]
                stack[-3:] = ["E"]
                pr(f"Reduce E -> E {op} E")
                reduced = True
                continue
            if len(stack) >= 3 and stack[-3] == "E" and stack[-1] == "E" and stack[-2] in ("AND", "OR"):
                op = stack[-2]
                stack[-3:] = ["E"]
                pr(f"Reduce E -> E {op} E")
                reduced = True
                continue
            if len(stack) >= 2 and stack[-2] == "NOT" and stack[-1] == "E":
                stack[-2:] = ["E"]
                pr("Reduce E -> ! E")
                reduced = True
                continue
            if len(stack) >= 4 and stack[-4] == "E" and stack[-3] == "ASSIGN" and stack[-1] == "SEMI":
                stack[-4:] = ["S"]
                pr("Reduce S -> id = E ;")
                reduced = True
                continue


class Node:
    def __init__(self, ntype, children=None, leaf=None, lineno=None):
        self.type = ntype
        self.children = children or []
        self.leaf = leaf
        self.lineno = lineno

    def print_tree(self, indent=0):
        label = self.type + (f": {self.leaf}" if self.leaf is not None else "")
        print("  " * indent + label)
        for child in self.children:
            if isinstance(child, Node):
                child.print_tree(indent + 1)


class SymbolTable:
    def __init__(self):
        self.scopes = [{}]
        self.scope_id = 0
        self.all_scopes = []
        self.offset_counter = [0]
        self.all_scopes.append((0, self.scopes[0]))

    def enter_scope(self):
        self.scope_id += 1
        new_scope = {}
        self.scopes.append(new_scope)
        self.offset_counter.append(0)
        self.all_scopes.append((self.scope_id, new_scope))

    def exit_scope(self):
        self.scopes.pop()
        self.offset_counter.pop()

    def current_scope(self):
        return self.scopes[-1]

    def current_scope_id(self):
        return len(self.scopes) - 1

    def insert(self, name, var_type, lineno):
        if name in self.current_scope():
            return False
        offset = self.offset_counter[-1]
        self.current_scope()[name] = {
            "type": var_type,
            "scope": self.current_scope_id(),
            "offset": offset,
            "line": lineno
        }
        self.offset_counter[-1] += 4
        return True

    def lookup(self, name):
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        return None

    def display(self):
        print("\n" + "=" * 60)
        print(" 2: SYMBOL TABLE")
        print("=" * 60)
        print(f"\n  {'Name':<12}{'Type':<10}{'Scope':<10}{'Offset':<10}{'Line':<8}")
        print("  " + "-" * 50)
        for scope_id, scope in self.all_scopes:
            if not scope:
                continue
            for var, info in scope.items():
                print(f"  {var:<12}{info['type']:<10}{scope_id:<10}{info['offset']:<10}{info['line']:<8}")

    def display_updates(self, updates):
        print("\n--- Symbol Table Updates ---")
        for u in updates:
            print(f"  {u}")


class SemanticAnalyzer:
    def __init__(self, symtab):
        self.symtab = symtab
        self.errors = []
        self.updates = []

    def error(self, msg, lineno):
        self.errors.append(f"  Line {lineno}: {msg}")

    def analyze(self, node):
        if not node:
            return None
        if node.type == "program":
            self.analyze(node.children[0])
            self.analyze(node.children[1])
        elif node.type == "decl_list":
            for child in node.children:
                self.analyze(child)
        elif node.type == "decl":
            var_type = node.children[0].leaf
            var_name = node.leaf
            ok = self.symtab.insert(var_name, var_type, node.lineno)
            if ok:
                self.updates.append(f"Declared '{var_name}' as {var_type} in scope {self.symtab.current_scope_id()}, offset {self.symtab.current_scope()[var_name]['offset']}")
            else:
                self.error(f"Multiple declaration of '{var_name}' in the same scope", node.lineno)
        elif node.type == "assign_stmt":
            var_name = node.leaf
            expr_type = self.eval_expr(node.children[0])
            info = self.symtab.lookup(var_name)
            if info is None:
                self.error(f"Use of undeclared variable '{var_name}'", node.lineno)
            elif expr_type and info["type"] != expr_type:
                if info["type"] == "int" and expr_type == "float":
                    self.error(f"Type mismatch: cannot assign float to int variable '{var_name}'", node.lineno)
                elif info["type"] == "float" and expr_type == "int":
                    pass
                else:
                    self.error(f"Type mismatch in assignment to '{var_name}'", node.lineno)
        elif node.type == "block":
            self.symtab.enter_scope()
            self.updates.append(f"Entering new scope {self.symtab.current_scope_id()}")
            self.analyze(node.children[0])
            self.updates.append(f"Exiting scope {self.symtab.current_scope_id()}")
            self.symtab.exit_scope()
        elif node.type == "stmt_list":
            for child in node.children:
                if child.type != "empty":
                    self.analyze(child)
        elif node.type == "stmt":
            self.analyze(node.children[0])
        elif node.type == "if_stmt":
            cond_type = self.eval_expr(node.children[0])
            if cond_type != "bool":
                self.error("Invalid boolean condition in if statement", node.lineno)
            self.analyze(node.children[1])
            if len(node.children) > 2:
                self.analyze(node.children[2])
        elif node.type == "while_stmt":
            cond_type = self.eval_expr(node.children[0])
            if cond_type != "bool":
                self.error("Invalid boolean condition in while statement", node.lineno)
            self.analyze(node.children[1])
        elif node.type == "print_stmt":
            self.eval_expr(node.children[0])
        elif node.type == "error_stmt":
            pass

    def eval_expr(self, node):
        if not node:
            return None
        if node.type == "factor":
            if node.leaf is not None:
                if isinstance(node.leaf, int):
                    return "int"
                elif isinstance(node.leaf, float):
                    return "float"
                else:
                    info = self.symtab.lookup(node.leaf)
                    if info is None:
                        self.error(f"Use of undeclared variable '{node.leaf}'", node.lineno)
                        return None
                    return info["type"]
            else:
                return self.eval_expr(node.children[0])
        elif node.type in ("expr", "term"):
            if len(node.children) == 2:
                left = self.eval_expr(node.children[0])
                right = self.eval_expr(node.children[1])
                if left is None or right is None:
                    return left or right
                if left == "float" or right == "float":
                    return "float"
                return "int"
            else:
                return self.eval_expr(node.children[0])
        elif node.type == "rel_expr":
            left = self.eval_expr(node.children[0])
            right = self.eval_expr(node.children[1])
            if left and right and left != right:
                if not ((left == "int" and right == "float") or (left == "float" and right == "int")):
                    self.error("Type mismatch in relational expression", node.lineno)
            return "bool"
        elif node.type in ("bool_expr", "bool_term"):
            left = self.eval_expr(node.children[0])
            right = self.eval_expr(node.children[1])
            if left and left != "bool":
                self.error("Invalid boolean expression operand", node.lineno)
            if right and right != "bool":
                self.error("Invalid boolean expression operand", node.lineno)
            return "bool"
        elif node.type == "NOT":
            val = self.eval_expr(node.children[0])
            if val and val != "bool":
                self.error("Invalid operand for NOT", node.lineno)
            return "bool"
        elif node.type == "bool_factor":
            return self.eval_expr(node.children[0])
        return None

    def report(self):
        print("\n" + "=" * 60)
        print(" 3: SEMANTIC ANALYSIS")
        print("=" * 60)
        self.symtab.display_updates(self.updates)
        if not self.errors:
            print("\n  No semantic errors detected.")
        else:
            print(f"\n--- Semantic Errors ({len(self.errors)} found) ---")
            for err in self.errors:
                print(err)


class TACGenerator:
    def __init__(self):
        self.code = []
        self.temp_count = 0
        self.label_count = 0

    def new_temp(self):
        self.temp_count += 1
        return f"t{self.temp_count}"

    def new_label(self):
        self.label_count += 1
        return f"L{self.label_count}"

    def emit(self, op, arg1="-", arg2="-", result="-"):
        self.code.append((op, str(arg1), str(arg2), str(result)))

    def emit_assign(self, target, source):
        self.emit("=", source, "-", target)

    def emit_binary(self, op, left, right, result):
        self.emit(op, left, right, result)

    def emit_if_goto(self, cond, label):
        self.emit("if_goto", cond, "-", label)

    def emit_goto(self, label):
        self.emit("goto", "-", "-", label)

    def emit_label(self, label):
        self.emit("label", "-", "-", label)

    def emit_print(self, value):
        self.emit("print", value, "-", "-")

    def generate(self, node):
        if not node:
            return None
        if node.type == "program":
            self.generate(node.children[0])
            self.generate(node.children[1])
        elif node.type == "decl_list":
            for child in node.children:
                self.generate(child)
        elif node.type == "decl":
            pass
        elif node.type == "stmt_list":
            for child in node.children:
                if child.type != "empty":
                    self.generate(child)
        elif node.type == "stmt":
            self.generate(node.children[0])
        elif node.type == "assign_stmt":
            t = self.gen_expr(node.children[0])
            self.emit_assign(node.leaf, t)
        elif node.type == "if_stmt":
            cond = self.gen_bool(node.children[0])
            l_true = self.new_label()
            l_false = self.new_label()
            self.emit_if_goto(cond, l_true)
            self.emit_goto(l_false)
            self.emit_label(l_true)
            self.generate(node.children[1])
            if len(node.children) > 2:
                l_end = self.new_label()
                self.emit_goto(l_end)
                self.emit_label(l_false)
                self.generate(node.children[2])
                self.emit_label(l_end)
            else:
                self.emit_label(l_false)
        elif node.type == "while_stmt":
            l_start = self.new_label()
            l_body = self.new_label()
            l_end = self.new_label()
            self.emit_label(l_start)
            cond = self.gen_bool(node.children[0])
            self.emit_if_goto(cond, l_body)
            self.emit_goto(l_end)
            self.emit_label(l_body)
            self.generate(node.children[1])
            self.emit_goto(l_start)
            self.emit_label(l_end)
        elif node.type == "block":
            self.generate(node.children[0])
        elif node.type == "print_stmt":
            t = self.gen_expr(node.children[0])
            self.emit_print(t)
        elif node.type == "error_stmt":
            pass
        return None

    def gen_expr(self, node):
        if not node:
            return ""
        if node.type == "factor":
            if node.leaf is not None:
                return str(node.leaf)
            return self.gen_expr(node.children[0])
        elif node.type in ("expr", "term"):
            if len(node.children) == 2:
                left = self.gen_expr(node.children[0])
                right = self.gen_expr(node.children[1])
                t = self.new_temp()
                self.emit_binary(node.leaf, left, right, t)
                return t
            return self.gen_expr(node.children[0])
        return str(node.leaf) if node.leaf is not None else ""

    def gen_bool(self, node):
        if not node:
            return ""
        if node.type == "rel_expr":
            left = self.gen_expr(node.children[0])
            right = self.gen_expr(node.children[1])
            t = self.new_temp()
            self.emit_binary(node.leaf, left, right, t)
            return t
        elif node.type in ("bool_expr", "bool_term"):
            left = self.gen_bool(node.children[0])
            right = self.gen_bool(node.children[1])
            t = self.new_temp()
            self.emit_binary(node.leaf, left, right, t)
            return t
        elif node.type == "NOT":
            val = self.gen_bool(node.children[0])
            t = self.new_temp()
            self.emit("not", val, "-", t)
            return t
        elif node.type == "bool_factor":
            return self.gen_bool(node.children[0])
        return self.gen_expr(node)

    def format_instruction(self, quad):
        op, arg1, arg2, result = quad
        if op == "label":
            return f"{result}:"
        if op == "goto":
            return f"goto {result}"
        if op == "if_goto":
            return f"if {arg1} goto {result}"
        if op == "print":
            return f"print {arg1}"
        if op == "=":
            return f"{result} = {arg1}"
        if op == "not":
            return f"{result} = ! {arg1}"
        return f"{result} = {arg1} {op} {arg2}"

    def display(self):
        print("\n" + "=" * 60)
        print(" 4: THREE-ADDRESS CODE (TAC) - QUADRUPLES")
        print("=" * 60)
        print(f"\n {'#':<4}{'OP':<12}{'ARG1':<12}{'ARG2':<12}{'RESULT':<12}")
        print(" " + "-" * 52)
        for i, quad in enumerate(self.code, 1):
            op, arg1, arg2, result = quad
            print(f" {i:<4}{op:<12}{arg1:<12}{arg2:<12}{result:<12}")
        print("\n--- Readable TAC ---")
        for quad in self.code:
            print(f" {self.format_instruction(quad)}")


# ─────────────────────────────────────────────────────────────
# QUESTION 5: OPTIMIZATION & TARGET CODE GENERATION
# ─────────────────────────────────────────────────────────────
#
# Optimization: Constant Folding
#   Replaces arithmetic operations on two compile-time constants
#   with a single constant in the TAC quadruple stream.
#
# Example cases where optimised pseudo-assembly differs:
#
#   Source:  x = 3 + 5 * 2 ;
#   Without: t1 = 5 * 2        ADD/MUL instructions for both ops
#            t2 = 3 + t1
#            x  = t2
#   With:    x  = 13           single MOV, no arithmetic needed
#
#   Source:  y = 10 / 2 ;
#   Without: t1 = 10 / 2       DIV instruction emitted
#            y  = t1
#   With:    y  = 5            single MOV, no DIV instruction
#
#   Source:  if (a < 4 + 1)    condition RHS folded to 5
#   Without: t1 = 4 + 1        ADD emitted before comparison
#            t2 = a < t1
#   With:    t1 = a < 5        comparison directly against 5
# ─────────────────────────────────────────────────────────────


def _is_number(s):
    try:
        float(s)
        return True
    except (ValueError, TypeError):
        return False


def _as_number(s):
    v = float(s)
    return int(v) if v == int(v) else v


def _fold(op, a, b):
    if op == "+":
        return a + b
    if op == "-":
        return a - b
    if op == "*":
        return a * b
    if op == "/" and b != 0:
        result = a / b
        return int(result) if result == int(result) else result
    if op == "%" and b != 0:
        return int(a) % int(b)
    return None


def constant_folding(tac_code):
    const_map = {}
    optimized = []

    for quad in tac_code:
        op, arg1, arg2, result = quad

        resolved_arg1 = const_map.get(arg1, arg1)
        resolved_arg2 = const_map.get(arg2, arg2)

        if op in ("+", "-", "*", "/", "%"):
            if _is_number(resolved_arg1) and _is_number(resolved_arg2):
                folded = _fold(op, _as_number(resolved_arg1), _as_number(resolved_arg2))
                if folded is not None:
                    folded_str = str(folded)
                    const_map[result] = folded_str
                    optimized.append(("=", folded_str, "-", result))
                    continue

        if op == "=":
            if _is_number(resolved_arg1):
                const_map[result] = resolved_arg1
            elif resolved_arg1 in const_map:
                const_map[result] = const_map[resolved_arg1]
            optimized.append((op, resolved_arg1, arg2, result))
            continue

        optimized.append((op, resolved_arg1, resolved_arg2, result))

    return optimized


def display_optimized_tac(original, optimized, formatter):
    print("\n" + "=" * 60)
    print(" 5A: CONSTANT FOLDING OPTIMIZATION")
    print("=" * 60)

    print("\n--- TAC Before Optimization ---")
    for i, quad in enumerate(original, 1):
        print(f" {i:<4}{formatter(quad)}")

    print("\n--- TAC After Optimization ---")
    for i, quad in enumerate(optimized, 1):
        print(f" {i:<4}{formatter(quad)}")

    removed = len(original) - len(optimized)
    folded_count = sum(
        1 for o, n in zip(original, optimized)
        if o != n
    ) + max(0, removed)
    print(f"\n  Instructions before : {len(original)}")
    print(f"  Instructions after  : {len(optimized)}")
    print(f"  Instructions removed/folded : {removed + folded_count}")


# ─────────────────────────────────────────────────────────────
# PSEUDO-ASSEMBLY TARGET CODE GENERATOR
#
# Register model: unlimited virtual registers R0, R1, R2, ...
# Memory model  : each program variable lives at label [varname]
#
# Instruction set:
#   MOV  Rdst, imm/Rsrc      -- load immediate or copy register
#   LOAD Rdst, [var]         -- load variable from memory
#   STORE [var], Rsrc        -- store register to memory variable
#   ADD  Rdst, Ra, Rb        -- Rdst = Ra + Rb
#   SUB  Rdst, Ra, Rb        -- Rdst = Ra - Rb
#   MUL  Rdst, Ra, Rb        -- Rdst = Ra * Rb
#   DIV  Rdst, Ra, Rb        -- Rdst = Ra / Rb
#   MOD  Rdst, Ra, Rb        -- Rdst = Ra % Rb
#   CMP  Rdst, Ra, Rb, <op>  -- Rdst = 1 if Ra <op> Rb else 0
#   NOT  Rdst, Ra            -- Rdst = logical NOT Ra
#   AND  Rdst, Ra, Rb        -- Rdst = Ra AND Rb
#   OR   Rdst, Ra, Rb        -- Rdst = Ra OR Rb
#   BNZ  Rsrc, label         -- branch to label if Rsrc != 0
#   JMP  label               -- unconditional jump
#   LABEL label:             -- label definition
#   PRINT Rsrc               -- output register value
#
# Control flow translation:
#   if_goto cond L  ->  load/compute cond into Rc, BNZ Rc, L
#   goto L          ->  JMP L
#   label L         ->  LABEL L:
#   while loop: LABEL start -> compute cond -> BNZ body -> JMP end
#                -> LABEL body -> body code -> JMP start -> LABEL end
# ─────────────────────────────────────────────────────────────

class TargetCodeGenerator:
    def __init__(self):
        self.instructions = []
        self.reg_count = 0
        self.reg_map = {}

    def _new_reg(self):
        r = f"R{self.reg_count}"
        self.reg_count += 1
        return r

    def _get_reg(self, name):
        if name not in self.reg_map:
            self.reg_map[name] = self._new_reg()
        return self.reg_map[name]

    def _emit(self, instr):
        self.instructions.append(instr)

    def _operand_to_reg(self, operand):
        if _is_number(operand):
            r = self._new_reg()
            self._emit(f"  MOV  {r}, {operand}")
            return r
        return self._get_reg(operand)

    def generate(self, tac_code):
        arith_map = {
            "+": "ADD", "-": "SUB", "*": "MUL", "/": "DIV", "%": "MOD"
        }
        cmp_ops = {"<", ">", "<=", ">=", "==", "!="}

        for quad in tac_code:
            op, arg1, arg2, result = quad

            if op == "label":
                self._emit(f"LABEL {result}:")

            elif op == "goto":
                self._emit(f"  JMP  {result}")

            elif op == "if_goto":
                rc = self._operand_to_reg(arg1)
                self._emit(f"  BNZ  {rc}, {result}")

            elif op == "=":
                if _is_number(arg1):
                    rd = self._get_reg(result)
                    self._emit(f"  MOV  {rd}, {arg1}")
                else:
                    rs = self._get_reg(arg1)
                    rd = self._get_reg(result)
                    self._emit(f"  MOV  {rd}, {rs}")
                if not result.startswith("t"):
                    rd = self._get_reg(result)
                    self._emit(f"  STORE [{result}], {rd}")

            elif op in arith_map:
                ra = self._operand_to_reg(arg1)
                rb = self._operand_to_reg(arg2)
                rd = self._get_reg(result)
                self._emit(f"  {arith_map[op]:<4} {rd}, {ra}, {rb}")

            elif op in cmp_ops:
                ra = self._operand_to_reg(arg1)
                rb = self._operand_to_reg(arg2)
                rd = self._get_reg(result)
                self._emit(f"  CMP  {rd}, {ra}, {rb}, {op}")

            elif op == "not":
                ra = self._operand_to_reg(arg1)
                rd = self._get_reg(result)
                self._emit(f"  NOT  {rd}, {ra}")

            elif op in ("&&", "||"):
                instr = "AND" if op == "&&" else "OR"
                ra = self._operand_to_reg(arg1)
                rb = self._operand_to_reg(arg2)
                rd = self._get_reg(result)
                self._emit(f"  {instr:<4} {rd}, {ra}, {rb}")

            elif op == "print":
                rc = self._operand_to_reg(arg1)
                self._emit(f"  PRINT {rc}")

    def display(self):
        print("\n" + "=" * 60)
        print(" 5B: TARGET CODE (PSEUDO ASSEMBLY)")
        print("=" * 60)
        print(f"\n  {'#':<5}{'Instruction'}")
        print("  " + "-" * 45)
        for i, instr in enumerate(self.instructions, 1):
            print(f"  {i:<5}{instr}")
        print("\n--- Register Allocation ---")
        print(f"  {'Name':<12}{'Register'}")
        print("  " + "-" * 24)
        for name, reg in sorted(self.reg_map.items()):
            print(f"  {name:<12}{reg}")


def run_lalr_parser(data):
    precedence = (
        ("left", "OR"),
        ("left", "AND"),
        ("left", "EQ", "NEQ"),
        ("left", "LT", "LE", "GT", "GE"),
        ("left", "PLUS", "MINUS"),
        ("left", "MUL", "DIV", "MOD"),
        ("right", "NOT"),
    )

    parse_tree_holder = [None]
    syntax_errors = []

    def p_program(p):
        '''program : decl_list stmt_list'''
        p[0] = Node("program", [p[1], p[2]], lineno=1)
        parse_tree_holder[0] = p[0]

    def p_decl_list(p):
        '''decl_list : decl decl_list
                     | empty'''
        if len(p) == 3:
            p[0] = Node("decl_list", [p[1], p[2]], lineno=p.lineno(1))
        else:
            p[0] = Node("decl_list", lineno=p.lineno(1))

    def p_decl(p):
        '''decl : type ID SEMI'''
        p[0] = Node("decl", [p[1]], p[2], lineno=p.lineno(2))

    def p_type(p):
        '''type : INT_TYPE
               | FLOAT_TYPE'''
        p[0] = Node("type", leaf=p[1], lineno=p.lineno(1))

    def p_stmt_list(p):
        '''stmt_list : stmt stmt_list
                     | empty'''
        if len(p) == 3:
            p[0] = Node("stmt_list", [p[1], p[2]], lineno=p.lineno(1))
        else:
            p[0] = Node("stmt_list", lineno=p.lineno(1))

    def p_stmt(p):
        '''stmt : assign_stmt
               | if_stmt
               | while_stmt
               | block
               | decl
               | print_stmt'''
        p[0] = Node("stmt", [p[1]], lineno=p.lineno(1))

    def p_stmt_error(p):
        '''stmt : error SEMI'''
        p[0] = Node("error_stmt", lineno=p.lineno(1))

    def p_stmt_error_block(p):
        '''stmt : error RCURLY'''
        p[0] = Node("error_stmt", lineno=p.lineno(1))

    def p_assign_stmt(p):
        '''assign_stmt : ID ASSIGN expr SEMI'''
        p[0] = Node("assign_stmt", [p[3]], p[1], lineno=p.lineno(1))

    def p_expr(p):
        '''expr : expr PLUS term
               | expr MINUS term
               | term'''
        if len(p) == 2:
            p[0] = p[1]
        else:
            p[0] = Node("expr", [p[1], p[3]], p[2], lineno=p.lineno(1))

    def p_term(p):
        '''term : term MUL factor
               | term DIV factor
               | term MOD factor
               | factor'''
        if len(p) == 2:
            p[0] = p[1]
        else:
            p[0] = Node("term", [p[1], p[3]], p[2], lineno=p.lineno(1))

    def p_factor(p):
        '''factor : LPAREN expr RPAREN
               | ID
               | INT
               | FLOAT'''
        if len(p) == 4:
            p[0] = Node("factor", [p[2]], lineno=p.lineno(1))
        else:
            p[0] = Node("factor", leaf=p[1], lineno=p.lineno(1))

    def p_bool_expr(p):
        '''bool_expr : bool_expr OR bool_term
                    | bool_term'''
        if len(p) == 2:
            p[0] = p[1]
        else:
            p[0] = Node("bool_expr", [p[1], p[3]], p[2], lineno=p.lineno(1))

    def p_bool_term(p):
        '''bool_term : bool_term AND bool_factor
                    | bool_factor'''
        if len(p) == 2:
            p[0] = p[1]
        else:
            p[0] = Node("bool_term", [p[1], p[3]], p[2], lineno=p.lineno(1))

    def p_bool_factor(p):
        '''bool_factor : NOT bool_factor
                      | LPAREN bool_expr RPAREN
                      | rel_expr'''
        if len(p) == 2:
            p[0] = p[1]
        elif len(p) == 3:
            p[0] = Node("NOT", [p[2]], lineno=p.lineno(1))
        else:
            p[0] = Node("bool_factor", [p[2]], lineno=p.lineno(1))

    def p_rel_expr(p):
        '''rel_expr : expr LT expr
                    | expr GT expr
                    | expr LE expr
                    | expr GE expr
                    | expr EQ expr
                    | expr NEQ expr'''
        p[0] = Node("rel_expr", [p[1], p[3]], p[2], lineno=p.lineno(1))

    def p_while_stmt(p):
        '''while_stmt : WHILE LPAREN bool_expr RPAREN stmt'''
        p[0] = Node("while_stmt", [p[3], p[5]], lineno=p.lineno(1))

    def p_if_stmt(p):
        '''if_stmt : IF LPAREN bool_expr RPAREN stmt ELSE stmt
                   | IF LPAREN bool_expr RPAREN stmt'''
        if len(p) == 8:
            p[0] = Node("if_stmt", [p[3], p[5], p[7]], lineno=p.lineno(1))
        else:
            p[0] = Node("if_stmt", [p[3], p[5]], lineno=p.lineno(1))

    def p_block(p):
        '''block : LCURLY stmt_list RCURLY'''
        p[0] = Node("block", [p[2]], lineno=p.lineno(1))

    def p_print_stmt(p):
        '''print_stmt : PRINT LPAREN expr RPAREN SEMI'''
        p[0] = Node("print_stmt", [p[3]], lineno=p.lineno(1))

    def p_empty(p):
        'empty :'
        p[0] = Node("empty")

    _src = [data]

    def _find_column(text, tok):
        last_cr = text.rfind("\n", 0, tok.lexpos)
        return tok.lexpos - last_cr

    def _suggest(tok):
        if not tok:
            return "Missing '}', ')', or ';' before end of file."
        t = tok.type
        if t == "ID":
            return "Missing ';' or operator before this identifier."
        if t in ("INT", "FLOAT"):
            return "Missing operator before literal, or extra ';'."
        if t == "RCURLY":
            return "Unexpected '}' -- unmatched or missing block."
        if t == "LCURLY":
            return "Unexpected '{' -- check preceding if/while syntax."
        if t == "RPAREN":
            return "Unexpected ')' -- check matching '('."
        if t == "LPAREN":
            return "Unexpected '(' -- check preceding syntax."
        if t == "SEMI":
            return "Extra ';' or missing expression."
        if t in ("PLUS", "MINUS", "MUL", "DIV", "MOD"):
            return "Missing operand around this operator."
        if t in ("IF", "ELSE", "WHILE"):
            return f"Misplaced '{tok.value}' -- check control-flow syntax."
        return "Check for missing ';', ')', or '}'."

    def p_error(p):
        if p:
            line = p.lineno
            col = _find_column(_src[0], p)
            src_lines = _src[0].splitlines()
            ltext = src_lines[line - 1] if 0 < line <= len(src_lines) else ""
            hint = _suggest(p)
            msg = f"Syntax Error: unexpected '{p.value}' ({p.type}) at line {line}, col {col}"
            detail = ""
            if ltext:
                detail += f"\n    {line}: {ltext}"
                detail += "\n    " + " " * (len(str(line)) + 2 + col - 1) + "^"
            detail += f"\n    Hint: {hint}"
            syntax_errors.append(msg + detail)
        else:
            syntax_errors.append("Syntax Error: unexpected end of file\n    Hint: Missing '}', ')', or ';' before end of file.")

    lalr_parser = yacc.yacc(debug=False, write_tables=False)
    _src[0] = data

    debug_buffer = io.StringIO()
    stderr_buffer = io.StringIO()
    with redirect_stdout(debug_buffer), redirect_stderr(stderr_buffer):
        lalr_parser.parse(data, lexer=lexer, debug=1)

    if syntax_errors:
        print("\n--- LALR(1) PARSE RESULT ---")
        print(f"  Parsing completed with {len(syntax_errors)} syntax error(s):\n")
        for i, err in enumerate(syntax_errors, 1):
            print(f"  [{i}] {err}")

    tree = parse_tree_holder[0]
    if not tree:
        if not syntax_errors:
            print("\n--- LALR(1) PARSE RESULT ---")
        print("\n  Parsing failed -- could not build AST.")
        print("  Subsequent phases (symbol table, semantic analysis, TAC) skipped.")
        return None

    if not syntax_errors:
        print("\n--- LALR(1) PARSE RESULT ---")
        print("  Valid program parsed successfully.")

    print("\n--- Abstract Syntax Tree ---")
    tree.print_tree()

    raw = debug_buffer.getvalue()
    lines = raw.splitlines()
    rows = []
    state = stack_str = action_str = None
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith("State"):
            if state is not None:
                rows.append((state, stack_str or "", action_str or ""))
            state = line.replace("State", "").strip()
            stack_str = action_str = None
        elif line.startswith("Stack  :"):
            stack_str = line.split(":", 1)[1].strip()
        elif line.startswith("Action :"):
            action_str = line.split(":", 1)[1].strip()
        elif line.startswith("Result :") or line.startswith("Done   :"):
            extra = line.split(":", 1)[1].strip()
            action_str = (action_str + " | " + extra) if action_str else extra
    if state is not None:
        rows.append((state, stack_str or "", action_str or ""))

    if rows:
        print("\n--- LALR(1) STACK TRACE (partial) ---")
        print(f"  {'Step':<6}{'State':<8}{'Stack':<45}{'Action'}")
        print("  " + "-" * 100)
        for i, (st, sk, act) in enumerate(rows[:30], 1):
            print(f"  {i:<6}{st:<8}{sk[:44]:<45}{act[:55]}")
        if len(rows) > 30:
            print(f"  ... ({len(rows) - 30} more steps)")

    return tree


def get_token_types(line):
    lexer.input(line)
    toks = []
    while True:
        tok = lexer.token()
        if not tok:
            break
        toks.append(tok.type)
    return toks


def run_shift_reduce_demo(data):
    print("\n--- SHIFT-REDUCE DEMO (per statement) ---")
    for raw_line in data.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        toks = get_token_types(line)
        if not toks:
            continue
        if len(toks) >= 4 and toks[0] == "ID" and toks[1] == "ASSIGN" and toks[-1] == "SEMI":
            print(f"\n  Statement: {line}")
            shift_reduce_parse(toks)


def main():
    compute_first()
    compute_follow()
    print_first_follow()

    table = construct_ll1_table()
    print_ll1_table(table)
    ll1_parse(["id", "=", "id", "+", "num", "*", "num", ";"], table)

    if len(sys.argv) < 2:
        print("\nUsage: python parser.py <source_file>")
        return

    src_path = sys.argv[1]
    try:
        with open(src_path, "r") as fh:
            data = fh.read()
    except FileNotFoundError:
        print(f"Error: file '{src_path}' not found.")
        sys.exit(1)

    run_shift_reduce_demo(data)

    tree = run_lalr_parser(data)
    if not tree:
        return

    symtab = SymbolTable()
    analyzer = SemanticAnalyzer(symtab)
    analyzer.analyze(tree)
    symtab.display()
    analyzer.report()

    tac = TACGenerator()
    tac.generate(tree)
    tac.display()

    optimized_code = constant_folding(tac.code)
    display_optimized_tac(tac.code, optimized_code, tac.format_instruction)

    tcg = TargetCodeGenerator()
    tcg.generate(optimized_code)
    tcg.display()


if __name__ == "__main__":
    main()
