#!/usr/bin/env python3
"""
Unit tests for the semantic analyzer core components.
Tests SymbolTable, TypeSystem, and ErrorReporter functionality.
"""

import unittest
from semantico import (
    TypeInfo, SymbolEntry, SemanticError, SymbolTable, 
    TypeSystem, ErrorReporter, SemanticErrorDetector,
    TIPO_INT, TIPO_FLOAT, TIPO_BOOLEAN, TIPO_VOID
)
from sintactico import Nodo


class TestTypeInfo(unittest.TestCase):
    """Test cases for TypeInfo class"""
    
    def test_type_info_creation(self):
        """Test TypeInfo object creation"""
        # Test basic types
        int_type = TypeInfo('int')
        self.assertEqual(int_type.base_type, 'int')
        self.assertFalse(int_type.is_array)
        self.assertIsNone(int_type.array_size)
        
        # Test array type
        array_type = TypeInfo('int', is_array=True, array_size=10)
        self.assertEqual(array_type.base_type, 'int')
        self.assertTrue(array_type.is_array)
        self.assertEqual(array_type.array_size, 10)
    
    def test_is_numeric(self):
        """Test numeric type checking"""
        self.assertTrue(TIPO_INT.is_numeric())
        self.assertTrue(TIPO_FLOAT.is_numeric())
        self.assertFalse(TIPO_BOOLEAN.is_numeric())
        self.assertFalse(TIPO_VOID.is_numeric())
    
    def test_type_compatibility(self):
        """Test type compatibility checking"""
        # Same types should be compatible
        self.assertTrue(TIPO_INT.is_compatible_with(TIPO_INT))
        self.assertTrue(TIPO_FLOAT.is_compatible_with(TIPO_FLOAT))
        
        # int should be compatible with float (promotion)
        self.assertTrue(TIPO_INT.is_compatible_with(TIPO_FLOAT))
        
        # float should not be compatible with int (no demotion)
        self.assertFalse(TIPO_FLOAT.is_compatible_with(TIPO_INT))
        
        # Different types should not be compatible
        self.assertFalse(TIPO_INT.is_compatible_with(TIPO_BOOLEAN))
        self.assertFalse(TIPO_BOOLEAN.is_compatible_with(TIPO_FLOAT))
    
    def test_type_promotion(self):
        """Test type promotion rules"""
        # int can be promoted to float
        self.assertTrue(TIPO_INT.can_promote_to(TIPO_FLOAT))
        
        # float cannot be promoted to int
        self.assertFalse(TIPO_FLOAT.can_promote_to(TIPO_INT))
        
        # Same types don't need promotion
        self.assertFalse(TIPO_INT.can_promote_to(TIPO_INT))
    
    def test_string_representation(self):
        """Test string representation of types"""
        self.assertEqual(str(TIPO_INT), 'int')
        self.assertEqual(str(TIPO_FLOAT), 'float')
        
        array_type = TypeInfo('int', is_array=True, array_size=5)
        self.assertEqual(str(array_type), 'int[5]')
        
        dynamic_array = TypeInfo('float', is_array=True)
        self.assertEqual(str(dynamic_array), 'float[]')


class TestSymbolTable(unittest.TestCase):
    """Test cases for SymbolTable class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.symbol_table = SymbolTable()
    
    def test_symbol_table_initialization(self):
        """Test symbol table initialization"""
        self.assertEqual(len(self.symbol_table.scopes), 1)
        self.assertEqual(self.symbol_table.get_current_scope(), 'global_0')
        self.assertEqual(self.symbol_table.get_scope_depth(), 1)
    
    def test_scope_management(self):
        """Test entering and exiting scopes"""
        # Enter new scope
        scope_id = self.symbol_table.enter_scope('if_block')
        self.assertIn('if_block', scope_id)
        self.assertEqual(self.symbol_table.get_scope_depth(), 2)
        
        # Exit scope
        exited_scope = self.symbol_table.exit_scope()
        self.assertEqual(exited_scope, scope_id)
        self.assertEqual(self.symbol_table.get_scope_depth(), 1)
        
        # Cannot exit global scope
        global_scope = self.symbol_table.exit_scope()
        self.assertIsNone(global_scope)
        self.assertEqual(self.symbol_table.get_scope_depth(), 1)
    
    def test_variable_declaration(self):
        """Test variable declaration"""
        # Declare variable successfully
        success = self.symbol_table.declare_variable('x', TIPO_INT, 1, 5)
        self.assertTrue(success)
        self.assertTrue(self.symbol_table.is_declared('x'))
        
        # Duplicate declaration in same scope should fail
        duplicate = self.symbol_table.declare_variable('x', TIPO_FLOAT, 2, 10)
        self.assertFalse(duplicate)
    
    def test_variable_lookup(self):
        """Test variable lookup across scopes"""
        # Declare in global scope
        self.symbol_table.declare_variable('global_var', TIPO_INT, 1, 1)
        
        # Enter new scope
        self.symbol_table.enter_scope('local')
        self.symbol_table.declare_variable('local_var', TIPO_FLOAT, 2, 1)
        
        # Should find both variables
        global_symbol = self.symbol_table.lookup_variable('global_var')
        local_symbol = self.symbol_table.lookup_variable('local_var')
        
        self.assertIsNotNone(global_symbol)
        self.assertIsNotNone(local_symbol)
        self.assertEqual(global_symbol.type_info.base_type, 'int')
        self.assertEqual(local_symbol.type_info.base_type, 'float')
        
        # Exit scope - local variable should not be accessible
        self.symbol_table.exit_scope()
        self.assertIsNotNone(self.symbol_table.lookup_variable('global_var'))
        self.assertIsNone(self.symbol_table.lookup_variable('local_var'))
    
    def test_variable_initialization(self):
        """Test variable initialization tracking"""
        self.symbol_table.declare_variable('x', TIPO_INT, 1, 1)
        
        # Initially not initialized
        symbol = self.symbol_table.lookup_variable('x')
        self.assertFalse(symbol.is_initialized)
        
        # Mark as initialized
        success = self.symbol_table.mark_initialized('x')
        self.assertTrue(success)
        
        symbol = self.symbol_table.lookup_variable('x')
        self.assertTrue(symbol.is_initialized)
    
    def test_symbol_table_formatting(self):
        """Test symbol table formatting"""
        self.symbol_table.declare_variable('x', TIPO_INT, 1, 5)
        self.symbol_table.declare_variable('y', TIPO_FLOAT, 2, 10)
        
        formatted = self.symbol_table.to_formatted_table()
        self.assertIn('TABLA DE SÍMBOLOS', formatted)
        self.assertIn('x', formatted)
        self.assertIn('y', formatted)
        self.assertIn('int', formatted)
        self.assertIn('float', formatted)


class TestTypeSystem(unittest.TestCase):
    """Test cases for TypeSystem class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.type_system = TypeSystem()
        self.symbol_table = SymbolTable()
    
    def test_type_compatibility_checking(self):
        """Test type compatibility verification"""
        # Same types are compatible
        self.assertTrue(self.type_system.check_compatibility(TIPO_INT, TIPO_INT))
        
        # int and float are compatible (promotion)
        self.assertTrue(self.type_system.check_compatibility(TIPO_INT, TIPO_FLOAT))
        self.assertTrue(self.type_system.check_compatibility(TIPO_FLOAT, TIPO_INT))
        
        # Incompatible types
        self.assertFalse(self.type_system.check_compatibility(TIPO_INT, TIPO_BOOLEAN))
    
    def test_type_conversion(self):
        """Test type conversion capabilities"""
        # int can convert to float
        self.assertTrue(self.type_system.can_convert(TIPO_INT, TIPO_FLOAT))
        
        # float cannot convert to int
        self.assertFalse(self.type_system.can_convert(TIPO_FLOAT, TIPO_INT))
        
        # Test actual conversion
        converted = self.type_system.perform_conversion(5, TIPO_INT, TIPO_FLOAT)
        self.assertEqual(converted, 5.0)
        self.assertIsInstance(converted, float)
    
    def test_operation_result_types(self):
        """Test operation result type calculation"""
        # Arithmetic operations
        result = self.type_system.get_operation_result_type('+', TIPO_INT, TIPO_INT)
        self.assertEqual(result.base_type, 'int')
        
        result = self.type_system.get_operation_result_type('+', TIPO_INT, TIPO_FLOAT)
        self.assertEqual(result.base_type, 'float')
        
        result = self.type_system.get_operation_result_type('*', TIPO_FLOAT, TIPO_FLOAT)
        self.assertEqual(result.base_type, 'float')
        
        # Relational operations always return boolean
        result = self.type_system.get_operation_result_type('>', TIPO_INT, TIPO_FLOAT)
        self.assertEqual(result.base_type, 'boolean')
        
        # Logical operations require boolean operands
        result = self.type_system.get_operation_result_type('&&', TIPO_BOOLEAN, TIPO_BOOLEAN)
        self.assertEqual(result.base_type, 'boolean')
        
        # Invalid operations return None
        result = self.type_system.get_operation_result_type('&&', TIPO_INT, TIPO_BOOLEAN)
        self.assertIsNone(result)
    
    def test_assignment_validation(self):
        """Test assignment validation"""
        # Valid assignments
        valid, msg = self.type_system.validate_assignment(TIPO_INT, TIPO_INT)
        self.assertTrue(valid)
        self.assertIsNone(msg)
        
        valid, msg = self.type_system.validate_assignment(TIPO_FLOAT, TIPO_INT)
        self.assertTrue(valid)
        self.assertIsNone(msg)
        
        # Invalid assignment
        valid, msg = self.type_system.validate_assignment(TIPO_INT, TIPO_BOOLEAN)
        self.assertFalse(valid)
        self.assertIsNotNone(msg)
    
    def test_operator_usage_validation(self):
        """Test operator usage validation"""
        # Valid arithmetic operation
        valid, msg = self.type_system.validate_operator_usage('+', [TIPO_INT, TIPO_FLOAT])
        self.assertTrue(valid)
        self.assertIsNone(msg)
        
        # Invalid arithmetic operation
        valid, msg = self.type_system.validate_operator_usage('+', [TIPO_INT, TIPO_BOOLEAN])
        self.assertFalse(valid)
        self.assertIsNotNone(msg)
        
        # Valid logical operation
        valid, msg = self.type_system.validate_operator_usage('&&', [TIPO_BOOLEAN, TIPO_BOOLEAN])
        self.assertTrue(valid)
        self.assertIsNone(msg)
        
        # Invalid logical operation
        valid, msg = self.type_system.validate_operator_usage('&&', [TIPO_INT, TIPO_BOOLEAN])
        self.assertFalse(valid)
        self.assertIsNotNone(msg)
    
    def test_expression_type_inference(self):
        """Test expression type inference"""
        # Create test nodes
        int_node = Nodo('NUM_INT', '42', 1, 1)
        float_node = Nodo('NUM_FLOAT', '3.14', 1, 5)
        bool_node = Nodo('TRUE', 'true', 1, 10)
        
        # Test literal type inference
        self.assertEqual(self.type_system.infer_expression_type(int_node).base_type, 'int')
        self.assertEqual(self.type_system.infer_expression_type(float_node).base_type, 'float')
        self.assertEqual(self.type_system.infer_expression_type(bool_node).base_type, 'boolean')
        
        # Test identifier type inference with symbol table
        self.symbol_table.declare_variable('x', TIPO_INT, 1, 1)
        id_node = Nodo('ID', 'x', 1, 15)
        
        inferred_type = self.type_system.infer_expression_type(id_node, self.symbol_table)
        self.assertEqual(inferred_type.base_type, 'int')


class TestErrorReporter(unittest.TestCase):
    """Test cases for ErrorReporter class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.error_reporter = ErrorReporter()
    
    def test_error_addition(self):
        """Test adding errors to the reporter"""
        # Add an error
        self.error_reporter.add_error('undeclared_variable', 'Variable x not declared', 1, 5)
        
        self.assertTrue(self.error_reporter.has_errors())
        self.assertEqual(self.error_reporter.get_error_count(), 1)
        self.assertEqual(self.error_reporter.get_error_count_by_type('undeclared_variable'), 1)
    
    def test_warning_addition(self):
        """Test adding warnings to the reporter"""
        # Add a warning
        self.error_reporter.add_warning('unused_variable', 'Variable y is unused', 2, 10)
        
        self.assertTrue(self.error_reporter.has_warnings())
        self.assertEqual(self.error_reporter.get_warning_count(), 1)
        self.assertFalse(self.error_reporter.has_errors())
    
    def test_specific_error_methods(self):
        """Test specific error addition methods"""
        # Test undeclared variable error
        self.error_reporter.add_undeclared_variable_error('x', 1, 5)
        self.assertEqual(self.error_reporter.get_error_count_by_type('undeclared_variable'), 1)
        
        # Test duplicate declaration error
        self.error_reporter.add_duplicate_declaration_error('y', 2, 10, 1)
        self.assertEqual(self.error_reporter.get_error_count_by_type('duplicate_declaration'), 1)
        
        # Test type incompatibility error
        self.error_reporter.add_type_incompatibility_error('int', 'boolean', 3, 15)
        self.assertEqual(self.error_reporter.get_error_count_by_type('type_incompatibility'), 1)
        
        # Test operator misuse error
        self.error_reporter.add_operator_misuse_error('+', ['int', 'boolean'], 4, 20)
        self.assertEqual(self.error_reporter.get_error_count_by_type('operator_misuse'), 1)
    
    def test_error_formatting(self):
        """Test error formatting for display"""
        self.error_reporter.add_undeclared_variable_error('x', 1, 5)
        self.error_reporter.add_warning('unused_variable', 'Variable y is unused', 2, 10)
        
        formatted = self.error_reporter.format_errors()
        
        self.assertIn('ERRORES SEMÁNTICOS', formatted)
        self.assertIn('x', formatted)
        self.assertIn('y', formatted)
        self.assertIn('ERROR', formatted)
        self.assertIn('WARNING', formatted)
        self.assertIn('RESUMEN', formatted)
    
    def test_error_export_format(self):
        """Test error export format for GUI"""
        self.error_reporter.add_undeclared_variable_error('x', 1, 5)
        self.error_reporter.add_warning('unused_variable', 'Variable y is unused', 2, 10)
        
        export_data = self.error_reporter.format_for_gui()
        
        self.assertIn('errors', export_data)
        self.assertIn('warnings', export_data)
        self.assertIn('summary', export_data)
        self.assertEqual(len(export_data['errors']), 1)
        self.assertEqual(len(export_data['warnings']), 1)
        self.assertEqual(export_data['summary']['total_errors'], 1)
        self.assertEqual(export_data['summary']['total_warnings'], 1)
    
    def test_error_clearing(self):
        """Test clearing all errors and warnings"""
        self.error_reporter.add_undeclared_variable_error('x', 1, 5)
        self.error_reporter.add_warning('unused_variable', 'Variable y is unused', 2, 10)
        
        self.assertTrue(self.error_reporter.has_errors())
        self.assertTrue(self.error_reporter.has_warnings())
        
        self.error_reporter.clear()
        
        self.assertFalse(self.error_reporter.has_errors())
        self.assertFalse(self.error_reporter.has_warnings())
        self.assertEqual(self.error_reporter.get_error_count(), 0)
        self.assertEqual(self.error_reporter.get_warning_count(), 0)
    
    def test_errors_by_line(self):
        """Test getting errors by line number"""
        self.error_reporter.add_undeclared_variable_error('x', 1, 5)
        self.error_reporter.add_type_incompatibility_error('int', 'boolean', 1, 10)
        self.error_reporter.add_duplicate_declaration_error('y', 2, 5)
        
        line_1_errors = self.error_reporter.get_errors_by_line(1)
        line_2_errors = self.error_reporter.get_errors_by_line(2)
        line_3_errors = self.error_reporter.get_errors_by_line(3)
        
        self.assertEqual(len(line_1_errors), 2)
        self.assertEqual(len(line_2_errors), 1)
        self.assertEqual(len(line_3_errors), 0)


class TestSemanticErrorDetector(unittest.TestCase):
    """Test cases for SemanticErrorDetector class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.error_reporter = ErrorReporter()
        self.symbol_table = SymbolTable()
        self.type_system = TypeSystem()
        self.detector = SemanticErrorDetector(
            self.error_reporter, self.symbol_table, self.type_system
        )
    
    def test_undeclared_variable_detection(self):
        """Test detection of undeclared variables"""
        # Create a node with an undeclared variable
        id_node = Nodo('ID', 'undeclared_var', 1, 5)
        
        result = self.detector.check_undeclared_variables(id_node)
        
        self.assertFalse(result)  # Should return False (error found)
        self.assertTrue(self.error_reporter.has_errors())
        self.assertEqual(self.error_reporter.get_error_count_by_type('undeclared_variable'), 1)
    
    def test_declared_variable_no_error(self):
        """Test that declared variables don't generate errors"""
        # Declare a variable
        self.symbol_table.declare_variable('declared_var', TIPO_INT, 1, 1)
        
        # Create a node using the declared variable
        id_node = Nodo('ID', 'declared_var', 2, 5)
        
        result = self.detector.check_undeclared_variables(id_node)
        
        self.assertTrue(result)  # Should return True (no error)
        self.assertFalse(self.error_reporter.has_errors())
    
    def test_duplicate_declaration_detection(self):
        """Test detection of duplicate variable declarations"""
        # Create a declaration node structure
        decl_node = Nodo('DECLARACION_VARIABLE', '', 1, 1)
        tipo_node = Nodo('TIPO', 'int', 1, 1)
        id_container = Nodo('IDENTIFICADOR', '', 1, 5)
        id_node = Nodo('ID', 'x', 1, 5)
        
        # Build the tree structure
        decl_node.agregar_hijo(tipo_node)
        decl_node.agregar_hijo(id_container)
        id_container.agregar_hijo(id_node)
        
        # First declaration should succeed
        result1 = self.detector.check_duplicate_declarations(decl_node)
        self.assertTrue(result1)
        self.assertFalse(self.error_reporter.has_errors())
        
        # Second declaration of same variable should fail
        decl_node2 = Nodo('DECLARACION_VARIABLE', '', 2, 1)
        tipo_node2 = Nodo('TIPO', 'float', 2, 1)
        id_container2 = Nodo('IDENTIFICADOR', '', 2, 5)
        id_node2 = Nodo('ID', 'x', 2, 5)
        
        decl_node2.agregar_hijo(tipo_node2)
        decl_node2.agregar_hijo(id_container2)
        id_container2.agregar_hijo(id_node2)
        
        result2 = self.detector.check_duplicate_declarations(decl_node2)
        self.assertFalse(result2)
        self.assertTrue(self.error_reporter.has_errors())
        self.assertEqual(self.error_reporter.get_error_count_by_type('duplicate_declaration'), 1)


if __name__ == '__main__':
    unittest.main()