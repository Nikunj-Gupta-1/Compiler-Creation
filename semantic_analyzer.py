class SemanticAnalyzer:
    def __init__(self):
        self.symbol_table = [{}]
        self.errors = []
        self.scope_id = 0
        self.all_scopes = [(self.scope_id, self.symbol_table[0])]

    def error(self, msg, lineno):
        self.errors.append(f"Line {lineno}: {msg}")

    def enter_scope(self):
        #self.symbol_table.append({})
        self.scope_id += 1
        new_scope = {}
        self.symbol_table.append(new_scope)
        self.all_scopes.append((self.scope_id, new_scope))

    def exit_scope(self):
        self.symbol_table.pop()

    def current_scope(self):
        return self.symbol_table[-1]

    def lookup(self, var):
        for scope in reversed(self.symbol_table):
            if var in scope:
                return scope[var]
        return None

    def declare(self, var, var_type, lineno):
        if var in self.current_scope():
            self.error(f"Multiple declaration of '{var}'", lineno)
        else:
            self.current_scope()[var] = {
                "type": var_type,
                "offset": len(self.current_scope()) * 4
            }
            print(f"Declared {var} of type {var_type} in scope {len(self.symbol_table)-1}")


    def check_variable(self, var, lineno):
        var_type = self.lookup(var)
        if var_type is None:
            self.error(f"Undeclared variable '{var}'", lineno)
        return var_type["type"] if var_type else None


    # Traverse AST

    def resolve_type(self, left, right):
        if left == "float" or right == "float":
            return "float"
        return "int"
    def analyze(self, node):
        if not node:
            return None

        if node.type == "program":
            self.analyze(node.children[0])
            self.analyze(node.children[1])

        elif node.type == "decl":
            var_type = node.children[0].leaf
            var_name = node.leaf
            self.declare(var_name, var_type, node.lineno)

        elif node.type == "assign_stmt":
            var_name = node.leaf
            expr_type = self.eval_expr(node.children[0])
            var_type = self.check_variable(var_name, node.lineno)

            if var_type and expr_type and var_type != expr_type:
                # int <- float (allowed with implicit cast)
                if var_type == "int" and expr_type == "float":
                    # optional: allow truncation silently
                    self.error(f"Type mismatch in assignment to '{var_name}'", node.lineno)
                    #pass

                # float <- int (safe widening)
                elif var_type == "float" and expr_type == "int":
                    pass

                # exact match
                elif var_type != expr_type:
                    self.error(f"Type mismatch in assignment to '{var_name}'", node.lineno)

        elif node.type == "block":
            self.enter_scope()
            self.analyze(node.children[0])
            self.exit_scope()

        elif node.type == "stmt_list":
            for child in node.children:
                if child.type != "empty":
                    self.analyze(child)

        elif node.type == "stmt":
            self.analyze(node.children[0])

        elif node.type == "if_stmt":
            cond_type = self.eval_expr(node.children[0])
            if cond_type != "bool":
                self.error("Invalid boolean condition in IF", node.lineno)
            self.analyze(node.children[1])
            self.analyze(node.children[2])

        elif node.type == "while_stmt":
            cond_type = self.eval_expr(node.children[0])
            if cond_type != "bool":
                self.error("Invalid boolean condition in WHILE", node.lineno)
            self.analyze(node.children[1])

        elif node.type == "print_stmt":
            self.eval_expr(node.children[0])
        
        elif node.type == "decl_list":
            for child in node.children:
                self.analyze(child)

    # Expression evaluation
    def eval_expr(self, node):
        if node.type == "factor":
            if node.leaf is not None:
                if isinstance(node.leaf, int):
                    return "int"
                elif isinstance(node.leaf, float):
                    return "float"
                else:
                    return self.check_variable(node.leaf, node.lineno)
            else:
                return self.eval_expr(node.children[0])

        elif node.type in ("expr", "term"):
            left = self.eval_expr(node.children[0])
            right = self.eval_expr(node.children[1])
            op = node.leaf
            
            if left is None or right is None:
                return left or right
            
            if op in ["+", "-", "*", "/", "%"]:
                result_type = self.resolve_type(left, right)
                return result_type

        elif node.type == "rel_expr":
            left = self.eval_expr(node.children[0])
            right = self.eval_expr(node.children[1])
            if left is None or right is None:
                self.error("Invalid relational expression", node.lineno)
                return "bool"
            if left != right:
                self.error("Type mismatch in relational expression", node.lineno)
            return "bool"

        elif node.type in ("bool_expr", "bool_term"):
            left = self.eval_expr(node.children[0])
            right = self.eval_expr(node.children[1])
            if left is None or right is None:
                return "bool"
            #else:
                #self.error("Invalid boolean expression", node.lineno)
                #return "bool"
            if left != "bool" or right != "bool":
                self.error("Invalid boolean expression", node.lineno)
            return "bool"

        elif node.type == "NOT":
            val = self.eval_expr(node.children[0])
            if val is None:
                return "bool"
            if val != "bool":
                self.error("Invalid NOT usage", node.lineno)
            return "bool"

        return None

    def report(self):
        if not self.errors:
            print("\nNo semantic errors")
        else:
            print("\nSemantic Errors:")
            for err in self.errors:
                print(err)
    
    """def print_symbol_table(self):
        for i, scope in enumerate(self.symbol_table):
            print(f"\nScope Level: {i}")
            print("-" * 44)
            print(f"{'Variable':<15}{'Type':<15}{'Offset':<10}")
            print("-" * 44)

            if not scope:
                print("(empty)")
            else:
                for var, info in scope.items():
                    print(f"{var:<15}{info['type']:<15}{info['offset']:<10}")

        print("\n" + "=" * 50)
    """
    def print_symbol_table(self):

        for scope_id, scope in self.all_scopes:
            print(f"\nScope Level: {scope_id}")
            print("-" * 44)
            print(f"{'Variable':<15}{'Type':<15}{'Offset':<10}")
            print("-" * 44)

            if not scope:
                print("(empty)")
            else:
                for var, info in scope.items():
                    print(f"{var:<15}{info['type']:<15}{info['offset']:<10}")

        print("\n" + "=" * 50)