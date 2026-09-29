## 📄 Project Summary: Compiler/Interpreter System

This project is designed to function as a **Compiler** for a simple subset of a language like C or C++. In essence, it takes source code written in a high-level language and translates it into machine-executable instructions, following a structured, multi-stage compilation pipeline.

### 🧑‍🏫 Simple Analogy
Imagine writing an essay:
1.  **The Proofreader (Lexer):** Breaks down text into basic words/tokens ("noun," "verb").
2.  **The Grammar Checker (Parser):** Checks if the tokens are arranged correctly according to grammar rules, building a logical blueprint (AST).
3.  **The Expert Reviewer (Semantic Analyzer):** Ensures the meaning is correct—no undefined variables or type mismatches.
4.  **The Translator (Code Generator):** Converts this perfect blueprint into low-level instructions that the computer's hardware can execute efficiently.

### 🧩 Key Components and Their Roles
The system follows a classic compiler architecture:

*   **Lexical Analyzer (Tokenizing):** Reads raw source code character by character and groups them into meaningful units called **tokens**.
    *   *(Example Files/Components: `v1_lexer_standalone.py`)*
*   **Syntax Analyzer / Parser (AST Generation):** Takes the stream of tokens and verifies that they follow the language's defined grammar rules, creating an **Abstract Syntax Tree (AST)**—a nested, hierarchical representation of the program's structure.
    *   *(Example Files/Components: `parser.py`, `v2_parser_ast.py`)*
*   **Semantic Analyzer & Symbol Table (Meaning Check):** This critical phase ensures that the code is *meaningful*. It checks for things like variable existence and type compatibility (e.g., preventing adding a string to an integer).
    *   *(Example Files/Components: `parser.py`)*
*   **Intermediate Representation (IR) Generator & Optimizer:** Translates the high-level AST into a simplified, machine-independent format called **Three-Address Code (TAC)**. This stage includes optimization steps like constant folding (`3 + 5` → `8`).
    *   *(Example Files/Components: Within `parser.py`)*
*   **Target Code Generator:** The final phase that takes the optimized TAC and translates it into assembly-like instructions for a specific target architecture, modeling CPU registers and execution flow.

---
This structure demonstrates a solid implementation of compiler theory fundamentals, moving from abstract text to concrete machine logic.*"