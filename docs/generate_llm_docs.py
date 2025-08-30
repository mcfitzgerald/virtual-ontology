#!/usr/bin/env python3
"""Generate LLM-friendly documentation for the twin_model package."""

import ast
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
import inspect
import importlib

# Add project root to path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))


class DocExtractor:
    """Extract documentation from Python modules."""
    
    def __init__(self, module_path: Path):
        self.module_path = module_path
        self.docs = []
    
    def extract_module(self, file_path: Path) -> Dict[str, Any]:
        """Extract documentation from a Python module."""
        with open(file_path, 'r') as f:
            source = f.read()
        
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return None
        
        module_name = file_path.stem
        relative_path = file_path.relative_to(self.module_path)
        
        module_doc = {
            'name': module_name,
            'path': str(relative_path),
            'docstring': ast.get_docstring(tree),
            'classes': [],
            'functions': [],
            'imports': []
        }
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_doc = self.extract_class(node)
                if class_doc:
                    module_doc['classes'].append(class_doc)
            elif isinstance(node, ast.FunctionDef) and node.col_offset == 0:
                func_doc = self.extract_function(node)
                if func_doc:
                    module_doc['functions'].append(func_doc)
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                module_doc['imports'].append(self.extract_import(node))
        
        return module_doc
    
    def extract_class(self, node: ast.ClassDef) -> Dict[str, Any]:
        """Extract documentation from a class."""
        class_doc = {
            'name': node.name,
            'docstring': ast.get_docstring(node),
            'bases': [self.get_name(base) for base in node.bases],
            'methods': [],
            'attributes': []
        }
        
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                method_doc = self.extract_function(item)
                if method_doc:
                    class_doc['methods'].append(method_doc)
            elif isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                attr_doc = {
                    'name': item.target.id,
                    'type': self.get_annotation(item.annotation)
                }
                class_doc['attributes'].append(attr_doc)
        
        return class_doc
    
    def extract_function(self, node: ast.FunctionDef) -> Dict[str, Any]:
        """Extract documentation from a function."""
        func_doc = {
            'name': node.name,
            'docstring': ast.get_docstring(node),
            'args': self.extract_arguments(node.args),
            'returns': self.get_annotation(node.returns) if node.returns else None,
            'decorators': [self.get_name(d) for d in node.decorator_list]
        }
        
        return func_doc
    
    def extract_arguments(self, args: ast.arguments) -> List[Dict[str, Any]]:
        """Extract function arguments."""
        arg_list = []
        
        for arg in args.args:
            if arg.arg != 'self':
                arg_doc = {
                    'name': arg.arg,
                    'type': self.get_annotation(arg.annotation) if arg.annotation else None
                }
                arg_list.append(arg_doc)
        
        return arg_list
    
    def extract_import(self, node) -> str:
        """Extract import statement."""
        if isinstance(node, ast.Import):
            return ', '.join([alias.name for alias in node.names])
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ''
            names = ', '.join([alias.name for alias in node.names])
            return f"from {module} import {names}"
        return ""
    
    def get_annotation(self, node) -> str:
        """Get type annotation as string."""
        if node is None:
            return None
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Constant):
            return repr(node.value)
        elif isinstance(node, ast.Subscript):
            return f"{self.get_name(node.value)}[{self.get_annotation(node.slice)}]"
        elif isinstance(node, ast.Tuple):
            return f"({', '.join([self.get_annotation(elt) for elt in node.elts])})"
        else:
            return ast.unparse(node) if hasattr(ast, 'unparse') else str(node)
    
    def get_name(self, node) -> str:
        """Get name from AST node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self.get_name(node.value)}.{node.attr}"
        elif isinstance(node, ast.Constant):
            return repr(node.value)
        else:
            return ast.unparse(node) if hasattr(ast, 'unparse') else str(node)
    
    def process_directory(self) -> List[Dict[str, Any]]:
        """Process all Python files in the directory."""
        docs = []
        
        for py_file in self.module_path.rglob("*.py"):
            # Skip tests and __pycache__
            if 'test' in py_file.name or '__pycache__' in str(py_file):
                continue
            
            module_doc = self.extract_module(py_file)
            if module_doc:
                docs.append(module_doc)
        
        return docs


def format_markdown(docs: List[Dict[str, Any]]) -> str:
    """Format documentation as markdown."""
    output = ["# Twin Model API Documentation\n"]
    output.append("*Auto-generated documentation for LLM consumption*\n")
    output.append("---\n\n")
    
    # Group by package
    packages = {}
    for module in docs:
        package = Path(module['path']).parent
        if package not in packages:
            packages[package] = []
        packages[package].append(module)
    
    for package, modules in sorted(packages.items()):
        if str(package) == '.':
            output.append("## Core Modules\n\n")
        else:
            output.append(f"## Package: {package}\n\n")
        
        for module in sorted(modules, key=lambda x: x['name']):
            output.append(f"### Module: {module['name']}\n")
            output.append(f"*File: {module['path']}*\n\n")
            
            if module['docstring']:
                output.append(f"{module['docstring']}\n\n")
            
            # Classes
            if module['classes']:
                output.append("#### Classes\n\n")
                for cls in module['classes']:
                    output.append(f"##### {cls['name']}")
                    if cls['bases']:
                        output.append(f"({', '.join(cls['bases'])})")
                    output.append("\n\n")
                    
                    if cls['docstring']:
                        output.append(f"{cls['docstring']}\n\n")
                    
                    if cls['attributes']:
                        output.append("**Attributes:**\n")
                        for attr in cls['attributes']:
                            type_str = f": {attr['type']}" if attr['type'] else ""
                            output.append(f"- `{attr['name']}{type_str}`\n")
                        output.append("\n")
                    
                    if cls['methods']:
                        output.append("**Methods:**\n")
                        for method in cls['methods']:
                            # Format arguments
                            args_str = ", ".join([
                                f"{arg['name']}: {arg['type']}" if arg['type'] else arg['name']
                                for arg in method['args']
                            ])
                            
                            return_str = f" -> {method['returns']}" if method['returns'] else ""
                            output.append(f"- `{method['name']}({args_str}){return_str}`\n")
                            
                            if method['docstring']:
                                # Indent docstring
                                docstring_lines = method['docstring'].split('\n')
                                for line in docstring_lines:
                                    output.append(f"  {line}\n")
                        output.append("\n")
            
            # Functions
            if module['functions']:
                output.append("#### Functions\n\n")
                for func in module['functions']:
                    args_str = ", ".join([
                        f"{arg['name']}: {arg['type']}" if arg['type'] else arg['name']
                        for arg in func['args']
                    ])
                    
                    return_str = f" -> {func['returns']}" if func['returns'] else ""
                    output.append(f"##### `{func['name']}({args_str}){return_str}`\n\n")
                    
                    if func['docstring']:
                        output.append(f"{func['docstring']}\n\n")
            
            output.append("---\n\n")
    
    return ''.join(output)


def main():
    """Generate LLM-friendly documentation."""
    # Set up paths
    twin_model_path = root_dir / 'twin_model'
    output_dir = root_dir / 'docs' / 'llm_output'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Extract documentation
    print("Extracting documentation from twin_model...")
    extractor = DocExtractor(twin_model_path)
    docs = extractor.process_directory()
    
    # Format as markdown
    print(f"Found {len(docs)} modules")
    markdown = format_markdown(docs)
    
    # Write output
    output_file = output_dir / 'twin_model_api.md'
    with open(output_file, 'w') as f:
        f.write(markdown)
    
    print(f"Documentation written to {output_file}")
    
    # Also create a consolidated llms.txt
    llms_file = output_dir / 'llms.txt'
    with open(llms_file, 'w') as f:
        f.write("VIRTUAL TWIN MODEL - COMPLETE DOCUMENTATION\n")
        f.write("=" * 50 + "\n\n")
        f.write(markdown)
    
    print(f"LLM-friendly documentation written to {llms_file}")


if __name__ == "__main__":
    main()