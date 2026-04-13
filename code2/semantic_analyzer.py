class SemanticAnalyzer:
    def __init__(self):
        self.scopes = []
        self.scope_counter = 0
        self.errors = []
        self.trace = []
        self.enter_scope('global')

    def error(self, msg, lineno):
        self.errors.append(f"Line {lineno}: {msg}")

    def current_scope(self):
        return self.scopes[-1]

    def enter_scope(self, label='block'):
        scope = {
            'id': self.scope_counter,
            'label': label,
            'symbols': {},
            'next_offset': 0
        }
        self.scope_counter += 1
        self.scopes.append(scope)
        self.trace.append(f"ENTER SCOPE id={scope['id']} label={scope['label']}")

    def exit_scope(self):
        scope = self.scopes.pop()
        self.trace.append(f"EXIT SCOPE id={scope['id']} label={scope['label']}")

    def type_width(self, vartype):
        if vartype == 'int':
            return 4
        if vartype == 'float':
            return 8
        if vartype == 'bool':
            return 1
        return 4

    def declare(self, var, vartype, lineno):
        scope = self.current_scope()
        if var in scope['symbols']:
            self.error(f"Multiple declaration of {var}", lineno)
            return None
        entry = {
            'name': var,
            'type': vartype,
            'scope': scope['id'],
            'offset': scope['next_offset']
        }
        scope['symbols'][var] = entry
        scope['next_offset'] += self.type_width(vartype)
        self.trace.append(
            f"INSERT name={entry['name']} type={entry['type']} scope={entry['scope']} offset={entry['offset']}"
        )
        return entry

    def lookup(self, var, lineno=None):
        for scope in reversed(self.scopes):
            if var in scope['symbols']:
                entry = scope['symbols'][var]
                self.trace.append(
                    f"LOOKUP name={entry['name']} type={entry['type']} scope={entry['scope']} offset={entry['offset']}"
                )
                return entry
        if lineno is not None:
            self.error(f"Undeclared variable {var}", lineno)
        return None

    def analyze(self, node):
        if node is None:
            return None
        handler = getattr(self, f"visit_{node.type}", None)
        if handler:
            return handler(node)
        for child in getattr(node, 'children', []):
            self.analyze(child)
        return None

    def visit_program(self, node):
        for child in node.children:
            self.analyze(child)

    def visit_decllist(self, node):
        for child in node.children:
            self.analyze(child)

    def visit_stmtlist(self, node):
        for child in node.children:
            self.analyze(child)

    def visit_stmt(self, node):
        for child in node.children:
            self.analyze(child)

    def visit_decl(self, node):
        vartype = node.children[0].leaf
        varname = node.leaf
        self.declare(varname, vartype, node.lineno)

    def visit_block(self, node):
        self.enter_scope('block')
        for child in node.children:
            self.analyze(child)
        self.exit_scope()

    def visit_assignstmt(self, node):
        entry = self.lookup(node.leaf, node.lineno)
        expr_type = self.eval_expr(node.children[0])
        if entry and expr_type and entry['type'] != expr_type:
            if not (entry['type'] == 'float' and expr_type == 'int'):
                self.error(f"Type mismatch in assignment to {node.leaf}: {entry['type']} = {expr_type}", node.lineno)

    def visit_ifstmt(self, node):
        cond_type = self.eval_expr(node.children[0])
        if cond_type != 'bool':
            self.error('Invalid boolean condition in IF', node.lineno)
        self.analyze(node.children[1])
        self.analyze(node.children[2])

    def visit_whilestmt(self, node):
        cond_type = self.eval_expr(node.children[0])
        if cond_type != 'bool':
            self.error('Invalid boolean condition in WHILE', node.lineno)
        self.analyze(node.children[1])

    def visit_printstmt(self, node):
        self.eval_expr(node.children[0])

    def eval_expr(self, node):
        if node is None:
            return None
        method = getattr(self, f"eval_{node.type}", None)
        if method:
            return method(node)
        if len(getattr(node, 'children', [])) == 1:
            return self.eval_expr(node.children[0])
        return None

    def eval_exprnode(self, node):
        return self.eval_expr(node)

    def eval_term(self, node):
        if len(node.children) == 1:
            return self.eval_expr(node.children[0])
        left = self.eval_expr(node.children[0])
        right = self.eval_expr(node.children[1])
        op = node.leaf
        if left not in ('int', 'float') or right not in ('int', 'float'):
            self.error(f"Type mismatch in expression using {op}", node.lineno)
            return 'float' if 'float' in (left, right) else 'int'
        return 'float' if 'float' in (left, right) else 'int'

    def eval_expr(self, node):
        if node.type == 'expr':
            if len(node.children) == 1:
                return self.eval_expr(node.children[0])
            left = self.eval_expr(node.children[0])
            right = self.eval_expr(node.children[1])
            op = node.leaf
            if op in ('+', '-', '*', '/', '%'):
                if left not in ('int', 'float') or right not in ('int', 'float'):
                    self.error(f"Type mismatch in expression using {op}", node.lineno)
                    return 'float' if 'float' in (left, right) else 'int'
                if op == '%' and (left != 'int' or right != 'int'):
                    self.error('Type mismatch in expression using %', node.lineno)
                    return 'int'
                return 'float' if 'float' in (left, right) else 'int'
            if op in ('<', '>', '<=', '>=', '==', '!='):
                if left != right:
                    self.error('Type mismatch in relational expression', node.lineno)
                return 'bool'
            if op in ('&&', '||'):
                if left != 'bool' or right != 'bool':
                    self.error('Invalid boolean expression', node.lineno)
                return 'bool'
            return None
        if node.type == 'term':
            return self.eval_term(node)
        if node.type == 'factor':
            if node.leaf is True or node.leaf is False:
                return 'bool'
            if isinstance(node.leaf, int):
                return 'int'
            if isinstance(node.leaf, float):
                return 'float'
            if isinstance(node.leaf, str):
                entry = self.lookup(node.leaf, node.lineno)
                return entry['type'] if entry else None
            if node.children:
                return self.eval_expr(node.children[0])
        if node.type == 'notexpr':
            t = self.eval_expr(node.children[0])
            if t != 'bool':
                self.error('Invalid NOT usage', node.lineno)
            return 'bool'
        return None

    def report(self):
        if not self.errors:
            print('No semantic errors')
        else:
            print('Semantic Errors:')
            for err in self.errors:
                print(err)

    def print_symbol_tables(self):
        print('SYMBOL TABLE TRACE')
        for item in self.trace:
            print(item)
        print('ACTIVE SYMBOL TABLES')
        for scope in self.scopes:
            print(f"Scope {scope['id']} ({scope['label']})")
            if not scope['symbols']:
                print('  <empty>')
            else:
                for entry in scope['symbols'].values():
                    print(
                        f"  name={entry['name']} type={entry['type']} scope={entry['scope']} offset={entry['offset']}"
                    )
