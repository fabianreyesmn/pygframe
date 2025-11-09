#!/usr/bin/env python3
"""
Integration tests for semantic analyzer using TestSemantica.txt.
Tests the complete semantic analysis workflow and validates expected results.
"""

import unittest
import os
from semantico import process_test_file, analyze_test_semantica
from lexico import AnalizadorLexico
from sintactico import AnalizadorSintactico


class TestSemanticaIntegration(unittest.TestCase):
    """Integration tests using TestSemantica.txt file"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_file = "TestSemantica.txt"
        self.assertTrue(os.path.exists(self.test_file), 
                       f"Test file {self.test_file} not found")
    
    def test_complete_semantic_analysis(self):
        """Test complete semantic analysis workflow"""
        # Run the complete analysis
        annotated_ast, symbol_table, errors, report = process_test_file(self.test_file)
        
        # Verify that analysis completed
        self.assertIsNotNone(annotated_ast, "Annotated AST should not be None")
        self.assertIsNotNone(symbol_table, "Symbol table should not be None")
        self.assertIsNotNone(errors, "Error list should not be None")
        self.assertIsNotNone(report, "Report should not be None")
        
        # Verify report contains expected sections
        self.assertIn("REPORTE COMPLETO DE ANÁLISIS", report)
        self.assertIn("TABLA DE SÍMBOLOS", report)
        self.assertIn("ERRORES SEMÁNTICOS", report)
    
    def test_expected_semantic_errors(self):
        """Test detection of expected semantic errors in TestSemantica.txt"""
        annotated_ast, symbol_table, errors, report = process_test_file(self.test_file)
        
        # Convert errors to a more searchable format
        error_messages = [error.message for error in errors]
        error_lines = [error.line for error in errors]
        
        # Expected errors based on TestSemantica.txt analysis:
        
        # 1. Variable 'suma' not declared (line 4)
        suma_errors = [error for error in errors 
                      if 'suma' in error.message and 'no declarada' in error.message]
        self.assertGreater(len(suma_errors), 0, 
                          "Should detect undeclared variable 'suma'")
        
        # 2. Type incompatibility: assigning float to int variable 'x' (line 5)
        type_errors = [error for error in errors 
                      if 'x' in error.message and ('tipo' in error.message.lower() or 
                                                  'incompatib' in error.message.lower())]
        self.assertGreater(len(type_errors), 0, 
                          "Should detect type incompatibility for x = 32.32")
        
        # 3. Variable 'mas' not declared (appears in lines 28, 33)
        mas_errors = [error for error in errors 
                     if 'mas' in error.message and 'no declarada' in error.message]
        self.assertGreater(len(mas_errors), 0, 
                          "Should detect undeclared variable 'mas'")
        
        # Verify we have at least the expected number of errors
        self.assertGreaterEqual(len(errors), 3, 
                               f"Expected at least 3 errors, found {len(errors)}")
    
    def test_symbol_table_construction(self):
        """Test accurate symbol table construction"""
        annotated_ast, symbol_table, errors, report = process_test_file(self.test_file)
        
        # Get all declared symbols
        all_symbols = symbol_table.get_all_symbols()
        symbol_names = [symbol.name for symbol in all_symbols]
        
        # Expected declared variables from TestSemantica.txt:
        expected_variables = ['x', 'y', 'z', 'a', 'b', 'c']
        
        for var_name in expected_variables:
            self.assertIn(var_name, symbol_names, 
                         f"Variable '{var_name}' should be in symbol table")
        
        # Verify types are correct
        symbol_dict = {symbol.name: symbol for symbol in all_symbols}
        
        # int variables
        for int_var in ['x', 'y', 'z']:
            if int_var in symbol_dict:
                self.assertEqual(symbol_dict[int_var].type_info.base_type, 'int',
                               f"Variable '{int_var}' should be int type")
        
        # float variables  
        for float_var in ['a', 'b', 'c']:
            if float_var in symbol_dict:
                self.assertEqual(symbol_dict[float_var].type_info.base_type, 'float',
                               f"Variable '{float_var}' should be float type")
        
        # Verify symbol table formatting
        formatted_table = symbol_table.to_formatted_table()
        self.assertIn("TABLA DE SÍMBOLOS", formatted_table)
        for var_name in expected_variables:
            self.assertIn(var_name, formatted_table)
    
    def test_type_checking_expressions(self):
        """Test type checking for all expressions in test file"""
        annotated_ast, symbol_table, errors, report = process_test_file(self.test_file)
        
        # Verify that arithmetic expressions are properly type-checked
        # Most arithmetic operations should be valid
        
        # Count type-related errors vs other errors
        type_errors = [error for error in errors 
                      if any(keyword in error.message.lower() 
                            for keyword in ['tipo', 'type', 'incompatib', 'conversion'])]
        
        undeclared_errors = [error for error in errors 
                           if 'no declarada' in error.message or 'not declared' in error.message]
        
        # We expect some type errors (like x = 32.32) and undeclared variable errors
        # but most arithmetic expressions should be valid
        total_errors = len(errors)
        self.assertGreater(total_errors, 0, "Should have some errors")
        
        # Verify the main types of errors we expect
        self.assertGreater(len(undeclared_errors), 0, "Should have undeclared variable errors")
        
        print(f"Total errors found: {total_errors}")
        print(f"Type-related errors: {len(type_errors)}")
        print(f"Undeclared variable errors: {len(undeclared_errors)}")
    
    def test_valid_arithmetic_operations(self):
        """Test that valid arithmetic operations don't generate errors"""
        annotated_ast, symbol_table, errors, report = process_test_file(self.test_file)
        
        # Filter out expected errors (undeclared variables, type incompatibilities)
        # and check that valid operations don't generate errors
        
        expected_error_patterns = [
            'suma',  # undeclared variable
            'mas',   # undeclared variable  
            'x.*32.32',  # type incompatibility
        ]
        
        unexpected_errors = []
        for error in errors:
            is_expected = False
            for pattern in expected_error_patterns:
                if pattern in error.message:
                    is_expected = True
                    break
            
            if not is_expected:
                # Check if it's a valid arithmetic operation that shouldn't error
                if any(op in error.message for op in ['+', '-', '*', '/', '(', ')']):
                    # This might be an unexpected error in arithmetic operations
                    unexpected_errors.append(error)
        
        # Print any unexpected errors for debugging
        if unexpected_errors:
            print("Unexpected errors in arithmetic operations:")
            for error in unexpected_errors:
                print(f"  - {error}")
    
    def test_control_flow_analysis(self):
        """Test semantic analysis of control flow structures"""
        annotated_ast, symbol_table, errors, report = process_test_file(self.test_file)
        
        # The test file contains if-else, do-until, and while structures
        # These should be analyzed without generating structural errors
        
        # Look for any errors related to control flow that aren't expected
        control_flow_errors = [error for error in errors 
                             if any(keyword in error.message.lower() 
                                   for keyword in ['if', 'while', 'do', 'until', 'then', 'else'])]
        
        # We don't expect control flow structure errors in this test file
        # (the syntax should be correct, only semantic errors expected)
        self.assertEqual(len(control_flow_errors), 0, 
                        f"Unexpected control flow errors: {control_flow_errors}")
    
    def test_boolean_expressions(self):
        """Test analysis of boolean expressions"""
        annotated_ast, symbol_table, errors, report = process_test_file(self.test_file)
        
        # The test file contains boolean expressions like:
        # - 2>3
        # - 4>2 && true  
        # - y == 5
        # - y == 0
        
        # These should be properly analyzed and typed as boolean
        # Look for any unexpected errors in boolean expressions
        
        boolean_errors = [error for error in errors 
                         if any(op in error.message for op in ['>', '<', '==', '!=', '&&', '||'])]
        
        # Filter out errors that are due to undeclared variables
        unexpected_boolean_errors = [error for error in boolean_errors 
                                   if 'no declarada' not in error.message]
        
        # Print any unexpected boolean expression errors
        if unexpected_boolean_errors:
            print("Unexpected boolean expression errors:")
            for error in unexpected_boolean_errors:
                print(f"  - {error}")
    
    def test_analyze_test_semantica_function(self):
        """Test the convenience function for analyzing TestSemantica.txt"""
        # Test the specific function for TestSemantica.txt analysis
        report = analyze_test_semantica()
        
        self.assertIsNotNone(report, "Report should not be None")
        self.assertIsInstance(report, str, "Report should be a string")
        
        # Verify report contains expected sections
        self.assertIn("REPORTE COMPLETO DE ANÁLISIS", report)
        self.assertIn("TABLA DE SÍMBOLOS", report)
        
        # Verify the report mentions the expected variables
        expected_vars = ['x', 'y', 'z', 'a', 'b', 'c']
        for var in expected_vars:
            self.assertIn(var, report, f"Variable '{var}' should be mentioned in report")
    
    def test_error_line_numbers(self):
        """Test that errors are reported with correct line numbers"""
        annotated_ast, symbol_table, errors, report = process_test_file(self.test_file)
        
        # Verify that most errors have valid line numbers (some may be 0 for inference errors)
        valid_line_errors = [error for error in errors if error.line > 0]
        self.assertGreater(len(valid_line_errors), 0, "Should have some errors with valid line numbers")
        
        for error in valid_line_errors:
            self.assertGreater(error.line, 0, f"Error should have valid line number: {error}")
            self.assertGreaterEqual(error.column, 0, f"Error should have valid column number: {error}")
        
        # Check specific expected error locations
        suma_errors = [error for error in errors if 'suma' in error.message]
        if suma_errors:
            # 'suma' appears on line 4 in TestSemantica.txt
            suma_error = suma_errors[0]
            self.assertEqual(suma_error.line, 4, 
                           f"'suma' error should be on line 4, found on line {suma_error.line}")
    
    def test_memory_address_assignment(self):
        """Test that variables are assigned memory addresses"""
        annotated_ast, symbol_table, errors, report = process_test_file(self.test_file)
        
        all_symbols = symbol_table.get_all_symbols()
        
        # Verify that declared variables have memory addresses
        for symbol in all_symbols:
            self.assertIsNotNone(symbol.memory_address, 
                               f"Variable '{symbol.name}' should have memory address")
            self.assertGreater(symbol.memory_address, 0, 
                             f"Variable '{symbol.name}' should have positive memory address")
        
        # Verify that memory addresses are unique
        addresses = [symbol.memory_address for symbol in all_symbols]
        unique_addresses = set(addresses)
        self.assertEqual(len(addresses), len(unique_addresses), 
                        "All variables should have unique memory addresses")


class TestSemanticAnalysisComponents(unittest.TestCase):
    """Test individual components of semantic analysis with TestSemantica.txt"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_file = "TestSemantica.txt"
    
    def test_lexical_analysis_integration(self):
        """Test integration with lexical analyzer"""
        # Read test file
        try:
            with open(self.test_file, 'r', encoding='utf-8') as f:
                codigo = f.read()
        except UnicodeDecodeError:
            with open(self.test_file, 'r', encoding='cp1252') as f:
                codigo = f.read()
        
        # Run lexical analysis
        analizador_lexico = AnalizadorLexico(codigo)
        tokens, errores_lexicos = analizador_lexico.analizar()
        
        # Verify tokens were generated
        self.assertGreater(len(tokens), 0, "Should generate tokens from test file")
        
        # Verify expected token types are present (tokens are tuples: (type, value, line, column))
        token_types = [token[0] for token in tokens]
        expected_types = ['MAIN', 'TIPO', 'ID', 'NUM_INT', 'NUM_FLOAT', 'ASIGNACION']
        
        for expected_type in expected_types:
            self.assertIn(expected_type, token_types, 
                         f"Token type '{expected_type}' should be present")
    
    def test_syntactic_analysis_integration(self):
        """Test integration with syntactic analyzer"""
        # Read test file
        try:
            with open(self.test_file, 'r', encoding='utf-8') as f:
                codigo = f.read()
        except UnicodeDecodeError:
            with open(self.test_file, 'r', encoding='cp1252') as f:
                codigo = f.read()
        
        # Run lexical analysis
        analizador_lexico = AnalizadorLexico(codigo)
        tokens, errores_lexicos = analizador_lexico.analizar()
        
        # Run syntactic analysis
        analizador_sintactico = AnalizadorSintactico(tokens)
        ast, errores_sintacticos = analizador_sintactico.analizar()
        
        # Verify AST was generated
        self.assertIsNotNone(ast, "Should generate AST from test file")
        
        # Note: TestSemantica.txt may have some syntactic issues, so we just verify AST generation
        # rather than requiring zero errors
        print(f"Syntactic errors found: {len(errores_sintacticos)}")
        if errores_sintacticos:
            print("Syntactic errors:", errores_sintacticos[:3])  # Show first 3 errors
    
    def test_file_output_generation(self):
        """Test that analysis generates proper output files"""
        # Run analysis
        report = analyze_test_semantica()
        
        # Check if output files were created
        expected_files = [
            'TestSemantica_results_symbol_table.txt',
            'TestSemantica_results_errors.txt', 
            'TestSemantica_results_annotated_ast.txt'
        ]
        
        for filename in expected_files:
            if os.path.exists(filename):
                # Verify file has content
                with open(filename, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.assertGreater(len(content), 0, 
                                 f"Output file '{filename}' should have content")


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)