import sys
import ply.lex as lex # type: ignore

tokens = [
    'ID', 'INT_CONST', 'FLOAT_CONST',
    'COMMENT',
    'AND', 'OR',
    'LE', 'GE', 'EQ', 'NE',
    'LT', 'GT',
    'PLUS_EQ', 'MINUS_EQ', 'ASSIGN',
    'INC', 'DEC',
    'PLUS', 'MINUS', 'MULT', 'DIV', 'MOD',
    'NOT',
    'LPAREN', 'RPAREN',
    'LBRACE', 'RBRACE',
    'LBRACKET', 'RBRACKET',
    'COMMA', 'SEMICOLON',
    'DOUBLE_QUOTE', 'SINGLE_QUOTE', 'ESCAPED_QUOTE',
    'KEYWORD', 'FUNCTION',
    'IF', 'ELSE', 'WHILE', 'FOR', 'RETURN', 'CONTINUE', 'SWITCH', 'CASE'
]


keywords = {
    "int", "float", "if", "else", "while", "for", "return", "continue",
    "switch", "case", "def", "char", "const", "default", "do", "double",
    "enum", "extern", "goto", "long", "register", "short", "signed",
    "sizeof", "static", "struct", "typedef", "union", "unsigned", "void",
    "volatile",
}

functions = {
    "main", "print", "printf", "scanf", "fprintf", "sprintf", "snprintf",
    "fopen", "fclose", "fread", "fwrite", "fgets", "fputs",
    "getchar", "putchar", "puts",
    "malloc", "calloc", "realloc", "free", "exit", "abort",
    "system", "qsort", "bsearch", "rand", "srand",
    "strlen", "strcpy", "strncpy", "strcat", "strncat",
    "strcmp", "strncmp", "strchr", "strrchr", "strstr", "strtok",
    "memcpy", "memmove", "memset", "memcmp",
    "isalpha", "isdigit", "isalnum", "isspace",
    "islower", "isupper", "tolower", "toupper",
    "sin", "cos", "tan", "sqrt", "pow", "exp", "log", "fabs",
    "time", "difftime", "clock", "mktime", "strftime",
}

t_AND      = r'&&'
t_OR       = r'\|\|'
t_LE       = r'<='
t_GE       = r'>='
t_EQ       = r'=='
t_NE       = r'!='
t_PLUS_EQ  = r'\+='
t_MINUS_EQ = r'-='
t_INC      = r'\+\+'
t_DEC      = r'--'

t_ASSIGN   = r'='
t_LT       = r'<'
t_GT       = r'>'
t_PLUS     = r'\+'
t_MINUS    = r'-'
t_MULT     = r'\*'
t_DIV      = r'/'
t_MOD      = r'%'
t_NOT      = r'!'

t_LPAREN    = r'\('
t_RPAREN    = r'\)'
t_LBRACE    = r'\{'
t_RBRACE    = r'\}'
t_LBRACKET  = r'\['
t_RBRACKET  = r'\]'
t_COMMA     = r','
t_SEMICOLON = r';'

def t_COMMENT(t):
    r'//.*|/\*([^*]|\*+[^*/])*\*+/'
    return t

def t_ESCAPED_QUOTE(t):
    r'\\"'
    return t

def t_DOUBLE_QUOTE(t):
    r'"'
    return t

def t_SINGLE_QUOTE(t):
    r"'"
    return t

def t_ID(t):
    r'[A-Za-z_][A-Za-z0-9_]*'
    if t.value in {"if"}:
        t.type = 'IF'
    elif t.value in {"else"}:
        t.type = 'ELSE'
    elif t.value in {"while"}:
        t.type = 'WHILE'
    elif t.value in {"for"}:
        t.type = 'FOR'
    elif t.value in {"return"}:
        t.type = 'RETURN'
    elif t.value in {"continue"}:
        t.type = 'CONTINUE'
    elif t.value in {"switch"}:
        t.type = 'SWITCH'
    elif t.value in {"case"}:
        t.type = 'CASE'
    elif t.value in keywords:
        t.type = 'KEYWORD'
    elif t.value in functions:
        t.type = 'FUNCTION'
    else:
        t.type = 'ID'
    return t


def t_FLOAT_CONST(t):
    r'[0-9]*\.[0-9]+|[0-9]+\.[0-9]*'
    return t

def t_INT_CONST(t):
    r'[0-9]+'
    return t

t_ignore_WS = r'[ \t\r]+'
t_ignore = ''

def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

def t_error(t):
    print(f"Error: unexpected character '{t.value[0]}' at line {t.lexer.lineno}")
    t.lexer.skip(1)

lexer = lex.lex()

def main():
    if len(sys.argv) < 2:
        print("Usage: python py1.py <filename>")
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

if __name__ == "__main__":
    main()
