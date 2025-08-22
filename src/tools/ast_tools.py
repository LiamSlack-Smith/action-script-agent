"""
This module provides tools for parsing and querying Python source code using the Abstract Syntax Tree (AST).
"""
import ast

def _read_file_content(file_path: str) -> str:
    """Safely reads the content of a file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {e}"

class FunctionVisitor(ast.NodeVisitor):
    """AST visitor to find function definitions."""
    def __init__(self):
        self.functions = []

    def visit_FunctionDef(self, node):
        self.functions.append({
            'name': node.name,
            'args': [arg.arg for arg in node.args.args],
            'lineno': node.lineno
        })
        self.generic_visit(node)

class ClassVisitor(ast.NodeVisitor):
    """AST visitor to find class definitions."""
    def __init__(self):
        self.classes = []

    def visit_ClassDef(self, node):
        self.classes.append({
            'name': node.name,
            'lineno': node.lineno
        })
        self.generic_visit(node)

class ImportVisitor(ast.NodeVisitor):
    """AST visitor to find import statements."""
    def __init__(self):
        self.imports = []

    def visit_Import(self, node):
        for alias in node.names:
            self.imports.append(f"import {alias.name}")
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        for alias in node.names:
            self.imports.append(f"from {node.module} import {alias.name}")
        self.generic_visit(node)


def find_function_definitions(file_path: str) -> dict:
    """Find all function definitions in a Python file and return their names, arguments, and line numbers."""
    content = _read_file_content(file_path)
    if content.startswith("Error reading file:"):
        return {'error': content}
    try:
        tree = ast.parse(content)
        visitor = FunctionVisitor()
        visitor.visit(tree)
        return {'functions': visitor.functions}
    except SyntaxError as e:
        return {'error': f"Failed to parse AST: {e}"

def find_class_definitions(file_path: str) -> dict:
    """Find all class definitions in a Python file and return their names and line numbers."""
    content = _read_file_content(file_path)
    if content.startswith("Error reading file:"):
        return {'error': content}
    try:
        tree = ast.parse(content)
        visitor = ClassVisitor()
        visitor.visit(tree)
        return {'classes': visitor.classes}
    except SyntaxError as e:
        return {'error': f"Failed to parse AST: {e}"}


def find_imports(file_path: str) -> dict:
    """Find all import statements in a Python file."""
    content = _read_file_content(file_path)
    if content.startswith("Error reading file:"):
        return {'error': content}
    try:
        tree = ast.parse(content)
        visitor = ImportVisitor()
        visitor.visit(tree)
        return {'imports': visitor.imports}
    except SyntaxError as e:
        return {'error': f"Failed to parse AST: {e}"}
