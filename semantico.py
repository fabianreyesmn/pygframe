# Archivo: semantico.py
# Analizador Semántico para el compilador PyGFrame
# Implementa las estructuras de datos centrales y el sistema de tipos

from dataclasses import dataclass
from typing import Optional, Any, List, Dict, Union, Tuple
from datetime import datetime
from sintactico import Nodo

@dataclass
class TypeInfo:
    """Representa información de tipo de datos en el análisis semántico"""
    base_type: str  # 'int', 'float', 'void', 'boolean'
    is_array: bool = False
    array_size: Optional[int] = None
    
    def is_numeric(self) -> bool:
        """Verifica si el tipo es numérico (int o float)"""
        return self.base_type in ['int', 'float']
    
    def is_compatible_with(self, other: 'TypeInfo') -> bool:
        """Verifica si este tipo es compatible con otro tipo"""
        if not isinstance(other, TypeInfo):
            return False
        
        # Tipos exactamente iguales
        if (self.base_type == other.base_type and 
            self.is_array == other.is_array and 
            self.array_size == other.array_size):
            return True
        
        # Compatibilidad numérica: int puede convertirse a float
        if (self.base_type == 'int' and other.base_type == 'float' and 
            not self.is_array and not other.is_array):
            return True
        
        return False
    
    def can_promote_to(self, other: 'TypeInfo') -> bool:
        """Verifica si este tipo puede ser promovido automáticamente al otro"""
        if not isinstance(other, TypeInfo):
            return False
        
        # int puede ser promovido a float
        if (self.base_type == 'int' and other.base_type == 'float' and 
            not self.is_array and not other.is_array):
            return True
        
        return False
    
    def __str__(self) -> str:
        """Representación en cadena del tipo"""
        if self.is_array:
            if self.array_size:
                return f"{self.base_type}[{self.array_size}]"
            else:
                return f"{self.base_type}[]"
        return self.base_type

@dataclass
class SymbolEntry:
    """Representa una entrada en la tabla de símbolos"""
    name: str
    type_info: TypeInfo
    scope: str
    line: int
    column: int
    memory_address: Optional[int] = None
    is_initialized: bool = False
    
    def __str__(self) -> str:
        """Representación en cadena de la entrada del símbolo"""
        return f"{self.name}: {self.type_info} (scope: {self.scope}, line: {self.line})"

@dataclass
class SemanticError:
    """Representa un error semántico detectado durante el análisis"""
    error_type: str
    message: str
    line: int
    column: int
    severity: str = 'error'  # 'error', 'warning'
    
    def __str__(self) -> str:
        """Representación en cadena del error semántico"""
        return f"[{self.severity.upper()}] {self.error_type} at line {self.line}, column {self.column}: {self.message}"

class AnnotatedASTNode(Nodo):
    """Extiende la clase Nodo para incluir atributos semánticos"""
    
    def __init__(self, original_node: Nodo):
        """Inicializa un nodo anotado basado en un nodo original del AST"""
        super().__init__(
            tipo=original_node.tipo,
            valor=original_node.valor,
            linea=original_node.linea,
            columna=original_node.columna
        )
        
        # Copiar hijos del nodo original
        for hijo in original_node.hijos:
            self.agregar_hijo(hijo)
        
        # Copiar referencia al padre si existe
        self.padre = original_node.padre
        
        # Atributos semánticos
        self.semantic_type: Optional[TypeInfo] = None
        self.semantic_value: Optional[Any] = None
        self.symbol_ref: Optional[SymbolEntry] = None
        
        # Atributos adicionales para análisis semántico
        self.is_lvalue: bool = False  # Indica si puede ser lado izquierdo de asignación
        self.is_constant: bool = False  # Indica si es una constante
        
    def set_semantic_type(self, type_info: TypeInfo):
        """Establece el tipo semántico del nodo"""
        self.semantic_type = type_info
    
    def set_semantic_value(self, value: Any):
        """Establece el valor semántico del nodo"""
        self.semantic_value = value
    
    def set_symbol_reference(self, symbol_entry: SymbolEntry):
        """Establece la referencia al símbolo en la tabla de símbolos"""
        self.symbol_ref = symbol_entry
    
    def get_semantic_type(self) -> Optional[TypeInfo]:
        """Obtiene el tipo semántico del nodo"""
        return self.semantic_type
    
    def get_semantic_value(self) -> Optional[Any]:
        """Obtiene el valor semántico del nodo"""
        return self.semantic_value
    
    def get_symbol_reference(self) -> Optional[SymbolEntry]:
        """Obtiene la referencia al símbolo"""
        return self.symbol_ref
    
    def has_semantic_info(self) -> bool:
        """Verifica si el nodo tiene información semántica"""
        return (self.semantic_type is not None or 
                self.semantic_value is not None or 
                self.symbol_ref is not None)
    
    def to_dict(self):
        """Convierte el nodo anotado a diccionario incluyendo información semántica"""
        base_dict = super().to_dict()
        
        # Agregar información semántica
        semantic_info = {}
        if self.semantic_type:
            semantic_info['type'] = str(self.semantic_type)
        if self.semantic_value is not None:
            semantic_info['value'] = str(self.semantic_value)
        if self.symbol_ref:
            semantic_info['symbol'] = self.symbol_ref.name
        if self.is_lvalue:
            semantic_info['is_lvalue'] = True
        if self.is_constant:
            semantic_info['is_constant'] = True
        
        if semantic_info:
            base_dict['semantic_attributes'] = semantic_info
        
        return base_dict
    
    @classmethod
    def from_node(cls, node: Nodo) -> 'AnnotatedASTNode':
        """Crea un nodo anotado a partir de un nodo regular del AST"""
        return cls(node)
    
    def annotate_children(self):
        """Convierte todos los hijos a nodos anotados recursivamente"""
        annotated_children = []
        for hijo in self.hijos:
            if isinstance(hijo, AnnotatedASTNode):
                annotated_children.append(hijo)
            else:
                annotated_child = AnnotatedASTNode.from_node(hijo)
                annotated_child.annotate_children()  # Recursión
                annotated_children.append(annotated_child)
        
        self.hijos = annotated_children
        
        # Actualizar referencias padre
        for hijo in self.hijos:
            hijo.padre = self
    
    def annotate_with_type_info(self, type_system: 'TypeSystem', symbol_table: 'SymbolTable'):
        """
        Anota el nodo con información de tipo usando el sistema de tipos
        
        Args:
            type_system: Sistema de tipos para inferir tipos
            symbol_table: Tabla de símbolos para resolver identificadores
        """
        # Anotar tipo para expresiones
        if self.tipo in ['NUM_INT', 'NUM_FLOAT', 'BOOLEANO', 'ID', '+', '-', '*', '/', '%', '^', 
                        '>', '<', '>=', '<=', '==', '!=', '&&', '||', '=']:
            inferred_type = type_system.infer_expression_type(self, symbol_table)
            if inferred_type:
                self.set_semantic_type(inferred_type)
        
        # Anotar referencia de símbolo para identificadores
        if self.tipo == 'ID':
            symbol = symbol_table.lookup_variable(self.valor)
            if symbol:
                self.set_symbol_reference(symbol)
                # Marcar como lvalue si es una variable declarada
                self.is_lvalue = True
        
        # Anotar valores constantes
        if self.tipo == 'NUM_INT':
            try:
                self.set_semantic_value(int(self.valor))
                self.is_constant = True
            except ValueError:
                pass
        elif self.tipo == 'NUM_FLOAT':
            try:
                self.set_semantic_value(float(self.valor))
                self.is_constant = True
            except ValueError:
                pass
        elif self.tipo in ['TRUE', 'FALSE']:
            self.set_semantic_value(self.valor.lower() == 'true')
            self.is_constant = True
        
        # Anotar recursivamente los hijos
        for hijo in self.hijos:
            if isinstance(hijo, AnnotatedASTNode):
                hijo.annotate_with_type_info(type_system, symbol_table)
    
    def annotate_with_symbol_references(self, symbol_table: 'SymbolTable'):
        """
        Anota el nodo y sus hijos con referencias a símbolos de la tabla
        
        Args:
            symbol_table: Tabla de símbolos para resolver identificadores
        """
        # Anotar identificadores con sus símbolos correspondientes
        if self.tipo == 'ID':
            symbol = symbol_table.lookup_variable(self.valor)
            if symbol:
                self.set_symbol_reference(symbol)
                # Establecer propiedades adicionales
                self.is_lvalue = True
                if symbol.is_initialized:
                    # Marcar como inicializada si el símbolo lo está
                    pass
        
        # Procesar hijos recursivamente
        for hijo in self.hijos:
            if isinstance(hijo, AnnotatedASTNode):
                hijo.annotate_with_symbol_references(symbol_table)
    
    def get_annotation_summary(self) -> Dict[str, Any]:
        """
        Obtiene un resumen de las anotaciones semánticas del nodo
        
        Returns:
            Diccionario con información semántica del nodo
        """
        summary = {
            'node_type': self.tipo,
            'node_value': self.valor,
            'line': self.linea,
            'column': self.columna,
            'has_semantic_info': self.has_semantic_info()
        }
        
        if self.semantic_type:
            summary['semantic_type'] = str(self.semantic_type)
        
        if self.semantic_value is not None:
            summary['semantic_value'] = self.semantic_value
        
        if self.symbol_ref:
            summary['symbol_reference'] = {
                'name': self.symbol_ref.name,
                'type': str(self.symbol_ref.type_info),
                'scope': self.symbol_ref.scope,
                'memory_address': self.symbol_ref.memory_address
            }
        
        if self.is_lvalue:
            summary['is_lvalue'] = True
        
        if self.is_constant:
            summary['is_constant'] = True
        
        return summary
    
    def to_annotated_dict(self) -> Dict[str, Any]:
        """
        Convierte el nodo anotado a diccionario con información semántica completa
        
        Returns:
            Diccionario con estructura del nodo e información semántica
        """
        # Obtener diccionario base del nodo
        base_dict = {
            'tipo': self.tipo,
            'valor': self.valor,
            'linea': self.linea,
            'columna': self.columna,
            'hijos': []
        }
        
        # Agregar información semántica si existe
        semantic_info = {}
        
        if self.semantic_type:
            semantic_info['type'] = str(self.semantic_type)
            semantic_info['type_details'] = {
                'base_type': self.semantic_type.base_type,
                'is_array': self.semantic_type.is_array,
                'is_numeric': self.semantic_type.is_numeric()
            }
        
        if self.semantic_value is not None:
            semantic_info['value'] = self.semantic_value
        
        if self.symbol_ref:
            semantic_info['symbol'] = {
                'name': self.symbol_ref.name,
                'type': str(self.symbol_ref.type_info),
                'scope': self.symbol_ref.scope,
                'line': self.symbol_ref.line,
                'column': self.symbol_ref.column,
                'memory_address': self.symbol_ref.memory_address,
                'is_initialized': self.symbol_ref.is_initialized
            }
        
        # Agregar propiedades adicionales
        properties = {}
        if self.is_lvalue:
            properties['is_lvalue'] = True
        if self.is_constant:
            properties['is_constant'] = True
        
        if properties:
            semantic_info['properties'] = properties
        
        # Agregar información semántica al diccionario si existe
        if semantic_info:
            base_dict['semantic_attributes'] = semantic_info
        
        # Procesar hijos recursivamente
        for hijo in self.hijos:
            if isinstance(hijo, AnnotatedASTNode):
                base_dict['hijos'].append(hijo.to_annotated_dict())
            else:
                # Convertir nodo regular a diccionario básico
                base_dict['hijos'].append(hijo.to_dict())
        
        return base_dict
    
    def to_formatted_string(self, indent: int = 0) -> str:
        """
        Convierte el AST anotado a una representación en cadena formateada
        
        Args:
            indent: Nivel de indentación para la representación jerárquica
            
        Returns:
            Cadena formateada del AST con anotaciones semánticas
        """
        indent_str = "  " * indent
        result = f"{indent_str}{self.tipo}"
        
        # Agregar valor si existe
        if self.valor:
            result += f": {self.valor}"
        
        # Agregar información de posición
        result += f" (L{self.linea}, C{self.columna})"
        
        # Agregar información semántica
        semantic_parts = []
        
        if self.semantic_type:
            semantic_parts.append(f"tipo={self.semantic_type}")
        
        if self.semantic_value is not None:
            semantic_parts.append(f"valor={self.semantic_value}")
        
        if self.symbol_ref:
            semantic_parts.append(f"símbolo={self.symbol_ref.name}@{self.symbol_ref.scope}")
        
        if self.is_lvalue:
            semantic_parts.append("lvalue")
        
        if self.is_constant:
            semantic_parts.append("constante")
        
        if semantic_parts:
            result += f" [{', '.join(semantic_parts)}]"
        
        result += "\n"
        
        # Procesar hijos
        for hijo in self.hijos:
            if isinstance(hijo, AnnotatedASTNode):
                result += hijo.to_formatted_string(indent + 1)
            else:
                # Para nodos no anotados, usar representación básica
                hijo_str = f"{indent_str}  {hijo.tipo}"
                if hijo.valor:
                    hijo_str += f": {hijo.valor}"
                hijo_str += f" (L{hijo.linea}, C{hijo.columna})\n"
                result += hijo_str
        
        return result
    
    @staticmethod
    def create_annotated_ast(root_node: Nodo, type_system: 'TypeSystem', 
                           symbol_table: 'SymbolTable') -> 'AnnotatedASTNode':
        """
        Crea un AST completamente anotado a partir de un nodo raíz
        
        Args:
            root_node: Nodo raíz del AST original
            type_system: Sistema de tipos para inferir información de tipos
            symbol_table: Tabla de símbolos para resolver referencias
            
        Returns:
            Nodo raíz del AST anotado con información semántica completa
        """
        # Crear nodo anotado desde el nodo original
        annotated_root = AnnotatedASTNode.from_node(root_node)
        
        # Convertir todos los hijos a nodos anotados
        annotated_root.annotate_children()
        
        # Anotar con información de tipos y símbolos
        annotated_root.annotate_with_type_info(type_system, symbol_table)
        annotated_root.annotate_with_symbol_references(symbol_table)
        
        return annotated_root

class ASTAnnotator:
    """
    Clase utilitaria para anotar ASTs con información semántica
    Proporciona métodos de alto nivel para el proceso de anotación
    """
    
    def __init__(self, type_system: 'TypeSystem', symbol_table: 'SymbolTable'):
        """
        Inicializa el anotador de AST
        
        Args:
            type_system: Sistema de tipos para inferir información de tipos
            symbol_table: Tabla de símbolos para resolver referencias
        """
        self.type_system = type_system
        self.symbol_table = symbol_table
    
    def annotate_ast(self, ast_root: Nodo) -> AnnotatedASTNode:
        """
        Anota un AST completo con información semántica
        
        Args:
            ast_root: Nodo raíz del AST original
            
        Returns:
            AST anotado con información semántica completa
        """
        return AnnotatedASTNode.create_annotated_ast(ast_root, self.type_system, self.symbol_table)
    
    def annotate_expression(self, expr_node: Nodo) -> AnnotatedASTNode:
        """
        Anota una expresión específica con información de tipo
        
        Args:
            expr_node: Nodo de expresión a anotar
            
        Returns:
            Nodo de expresión anotado
        """
        annotated_expr = AnnotatedASTNode.from_node(expr_node)
        annotated_expr.annotate_children()
        annotated_expr.annotate_with_type_info(self.type_system, self.symbol_table)
        return annotated_expr
    
    def annotate_identifier(self, id_node: Nodo) -> AnnotatedASTNode:
        """
        Anota un identificador con su referencia de símbolo
        
        Args:
            id_node: Nodo identificador a anotar
            
        Returns:
            Nodo identificador anotado con referencia de símbolo
        """
        if id_node.tipo != 'ID':
            raise ValueError("El nodo debe ser de tipo 'ID'")
        
        annotated_id = AnnotatedASTNode.from_node(id_node)
        annotated_id.annotate_with_symbol_references(self.symbol_table)
        return annotated_id
    
    def get_expression_type(self, expr_node: Nodo) -> Optional[TypeInfo]:
        """
        Obtiene el tipo de una expresión sin crear un nodo anotado
        
        Args:
            expr_node: Nodo de expresión
            
        Returns:
            Información de tipo de la expresión o None si no se puede determinar
        """
        return self.type_system.infer_expression_type(expr_node, self.symbol_table)
    
    def validate_and_annotate(self, ast_root: Nodo) -> Tuple[AnnotatedASTNode, List[str]]:
        """
        Valida y anota un AST, retornando errores encontrados
        
        Args:
            ast_root: Nodo raíz del AST original
            
        Returns:
            Tupla con (AST anotado, lista de errores de validación)
        """
        errors = []
        
        # Crear AST anotado
        annotated_ast = self.annotate_ast(ast_root)
        
        # Validar tipos en el AST
        is_valid, type_errors = self.type_system.validate_expression_types(ast_root, self.symbol_table)
        if not is_valid:
            errors.extend(type_errors)
        
        return annotated_ast, errors
    
    def export_annotated_ast(self, annotated_ast: AnnotatedASTNode, 
                           format_type: str = 'dict') -> Union[Dict[str, Any], str]:
        """
        Exporta el AST anotado en el formato especificado
        
        Args:
            annotated_ast: AST anotado a exportar
            format_type: Formato de exportación ('dict', 'json', 'formatted_string')
            
        Returns:
            AST exportado en el formato solicitado
        """
        if format_type == 'dict':
            return annotated_ast.to_annotated_dict()
        elif format_type == 'formatted_string':
            return annotated_ast.to_formatted_string()
        elif format_type == 'json':
            import json
            return json.dumps(annotated_ast.to_annotated_dict(), indent=2, ensure_ascii=False)
        else:
            raise ValueError(f"Formato no soportado: {format_type}")
    
    def save_annotated_ast_to_file(self, annotated_ast: AnnotatedASTNode, 
                                 filename: str, format_type: str = 'json') -> bool:
        """
        Guarda el AST anotado en un archivo
        
        Args:
            annotated_ast: AST anotado a guardar
            filename: Nombre del archivo de destino
            format_type: Formato de archivo ('json', 'formatted_string')
            
        Returns:
            True si se guardó exitosamente, False en caso de error
        """
        try:
            content = self.export_annotated_ast(annotated_ast, format_type)
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return True
        except Exception as e:
            print(f"Error al guardar AST anotado: {e}")
            return False
    
    def get_nodes_by_type(self, annotated_ast: AnnotatedASTNode, 
                         node_type: str) -> List[AnnotatedASTNode]:
        """
        Obtiene todos los nodos de un tipo específico del AST anotado
        
        Args:
            annotated_ast: AST anotado a buscar
            node_type: Tipo de nodo a buscar
            
        Returns:
            Lista de nodos que coinciden con el tipo especificado
        """
        nodes = []
        
        if annotated_ast.tipo == node_type:
            nodes.append(annotated_ast)
        
        for hijo in annotated_ast.hijos:
            if isinstance(hijo, AnnotatedASTNode):
                nodes.extend(self.get_nodes_by_type(hijo, node_type))
        
        return nodes
    
    def get_nodes_with_semantic_info(self, annotated_ast: AnnotatedASTNode) -> List[AnnotatedASTNode]:
        """
        Obtiene todos los nodos que tienen información semántica
        
        Args:
            annotated_ast: AST anotado a buscar
            
        Returns:
            Lista de nodos con información semántica
        """
        nodes = []
        
        if annotated_ast.has_semantic_info():
            nodes.append(annotated_ast)
        
        for hijo in annotated_ast.hijos:
            if isinstance(hijo, AnnotatedASTNode):
                nodes.extend(self.get_nodes_with_semantic_info(hijo))
        
        return nodes
    
    def generate_annotation_report(self, annotated_ast: AnnotatedASTNode) -> str:
        """
        Genera un reporte de las anotaciones semánticas en el AST
        
        Args:
            annotated_ast: AST anotado a analizar
            
        Returns:
            Reporte formateado de las anotaciones
        """
        report = "REPORTE DE ANOTACIONES SEMÁNTICAS\n"
        report += "=" * 50 + "\n\n"
        
        # Contar nodos por tipo
        all_nodes = self._get_all_nodes(annotated_ast)
        nodes_with_semantic = self.get_nodes_with_semantic_info(annotated_ast)
        
        report += f"Total de nodos: {len(all_nodes)}\n"
        report += f"Nodos con información semántica: {len(nodes_with_semantic)}\n"
        report += f"Porcentaje anotado: {len(nodes_with_semantic)/len(all_nodes)*100:.1f}%\n\n"
        
        # Detalles por tipo de nodo
        type_counts = {}
        for node in nodes_with_semantic:
            if node.tipo not in type_counts:
                type_counts[node.tipo] = 0
            type_counts[node.tipo] += 1
        
        if type_counts:
            report += "NODOS ANOTADOS POR TIPO:\n"
            report += "-" * 30 + "\n"
            for node_type, count in sorted(type_counts.items()):
                report += f"{node_type}: {count}\n"
            report += "\n"
        
        # Información de símbolos referenciados
        symbol_refs = [node for node in nodes_with_semantic if node.symbol_ref]
        if symbol_refs:
            report += "REFERENCIAS DE SÍMBOLOS:\n"
            report += "-" * 30 + "\n"
            for node in symbol_refs:
                report += f"Variable '{node.symbol_ref.name}' (tipo: {node.symbol_ref.type_info}) "
                report += f"en línea {node.linea}\n"
            report += "\n"
        
        return report
    
    def _get_all_nodes(self, node: AnnotatedASTNode) -> List[AnnotatedASTNode]:
        """Obtiene todos los nodos del AST recursivamente"""
        nodes = [node]
        for hijo in node.hijos:
            if isinstance(hijo, AnnotatedASTNode):
                nodes.extend(self._get_all_nodes(hijo))
        return nodes

class SymbolTable:
    """Maneja la tabla de símbolos con soporte para ámbitos anidados"""
    
    def __init__(self):
        """Inicializa la tabla de símbolos con el ámbito global"""
        self.scopes = []  # Pila de ámbitos
        self.symbols = {}  # Diccionario de símbolos por ámbito
        self.current_scope_id = 0  # ID único para cada ámbito
        self.memory_counter = 1000  # Contador para direcciones de memoria
        
        # Crear ámbito global
        self.enter_scope("global")
    
    def enter_scope(self, scope_name: str = None):
        """Entra a un nuevo ámbito"""
        if scope_name is None:
            scope_name = f"scope_{self.current_scope_id}"
        
        scope_id = f"{scope_name}_{self.current_scope_id}"
        self.current_scope_id += 1
        
        self.scopes.append(scope_id)
        self.symbols[scope_id] = {}
        
        return scope_id
    
    def exit_scope(self):
        """Sale del ámbito actual"""
        if len(self.scopes) > 1:  # No permitir salir del ámbito global
            scope_id = self.scopes.pop()
            return scope_id
        return None
    
    def get_current_scope(self) -> str:
        """Obtiene el ámbito actual"""
        return self.scopes[-1] if self.scopes else None
    
    def declare_variable(self, name: str, type_info: TypeInfo, line: int, column: int) -> bool:
        """
        Declara una variable en el ámbito actual
        Retorna True si la declaración es exitosa, False si ya existe
        """
        current_scope = self.get_current_scope()
        
        # Verificar si ya existe en el ámbito actual
        if current_scope in self.symbols and name in self.symbols[current_scope]:
            return False  # Variable ya declarada en este ámbito
        
        # Crear entrada del símbolo
        symbol_entry = SymbolEntry(
            name=name,
            type_info=type_info,
            scope=current_scope,
            line=line,
            column=column,
            memory_address=self.memory_counter,
            is_initialized=False
        )
        
        # Agregar al ámbito actual
        if current_scope not in self.symbols:
            self.symbols[current_scope] = {}
        
        self.symbols[current_scope][name] = symbol_entry
        self.memory_counter += 4  # Incrementar dirección de memoria (asumiendo 4 bytes por variable)
        
        return True
    
    def lookup_variable(self, name: str) -> Optional[SymbolEntry]:
        """
        Busca una variable en los ámbitos (desde el actual hacia el global)
        Retorna la entrada del símbolo si se encuentra, None si no existe
        """
        # Buscar desde el ámbito actual hacia el global
        for scope_id in reversed(self.scopes):
            if scope_id in self.symbols and name in self.symbols[scope_id]:
                return self.symbols[scope_id][name]
        
        return None
    
    def is_declared(self, name: str) -> bool:
        """Verifica si una variable está declarada en cualquier ámbito accesible"""
        return self.lookup_variable(name) is not None
    
    def is_declared_in_current_scope(self, name: str) -> bool:
        """Verifica si una variable está declarada en el ámbito actual"""
        current_scope = self.get_current_scope()
        return (current_scope in self.symbols and 
                name in self.symbols[current_scope])
    
    def mark_initialized(self, name: str) -> bool:
        """Marca una variable como inicializada"""
        symbol = self.lookup_variable(name)
        if symbol:
            symbol.is_initialized = True
            return True
        return False
    
    def get_all_symbols(self) -> List[SymbolEntry]:
        """Obtiene todas las entradas de símbolos de todos los ámbitos"""
        all_symbols = []
        for scope_id in self.symbols:
            for symbol in self.symbols[scope_id].values():
                all_symbols.append(symbol)
        return all_symbols
    
    def get_symbols_in_scope(self, scope_name: str = None) -> List[SymbolEntry]:
        """Obtiene todas las entradas de símbolos de un ámbito específico"""
        if scope_name is None:
            scope_name = self.get_current_scope()
        
        if scope_name in self.symbols:
            return list(self.symbols[scope_name].values())
        return []
    
    def to_formatted_table(self) -> str:
        """Genera una representación formateada de la tabla de símbolos"""
        if not any(self.symbols.values()):
            return "Tabla de símbolos vacía"
        
        resultado = "TABLA DE SÍMBOLOS:\n"
        resultado += "=" * 100 + "\n"
        resultado += "| {:<15} | {:<12} | {:<20} | {:<8} | {:<8} | {:<10} | {:<8} |\n".format(
            "NOMBRE", "TIPO", "ÁMBITO", "LÍNEA", "COLUMNA", "DIRECCIÓN", "INICIALIZADA"
        )
        resultado += "=" * 100 + "\n"
        
        # Ordenar símbolos por ámbito y luego por línea
        all_symbols = self.get_all_symbols()
        all_symbols.sort(key=lambda s: (s.scope, s.line))
        
        for symbol in all_symbols:
            resultado += "| {:<15} | {:<12} | {:<20} | {:<8} | {:<8} | {:<10} | {:<8} |\n".format(
                symbol.name,
                str(symbol.type_info),
                symbol.scope,
                symbol.line,
                symbol.column,
                symbol.memory_address or "N/A",
                "Sí" if symbol.is_initialized else "No"
            )
        
        resultado += "=" * 100 + "\n"
        return resultado
    
    def to_export_format(self) -> Dict[str, Any]:
        """Exporta la tabla de símbolos en formato diccionario para la GUI"""
        export_data = {
            'scopes': self.scopes.copy(),
            'current_scope': self.get_current_scope(),
            'symbols_by_scope': {},
            'total_symbols': 0
        }
        
        for scope_id, symbols in self.symbols.items():
            export_data['symbols_by_scope'][scope_id] = []
            for symbol in symbols.values():
                export_data['symbols_by_scope'][scope_id].append({
                    'name': symbol.name,
                    'type': str(symbol.type_info),
                    'line': symbol.line,
                    'column': symbol.column,
                    'memory_address': symbol.memory_address,
                    'is_initialized': symbol.is_initialized
                })
                export_data['total_symbols'] += 1
        
        return export_data
    
    def clear(self):
        """Limpia la tabla de símbolos y reinicia al ámbito global"""
        self.scopes.clear()
        self.symbols.clear()
        self.current_scope_id = 0
        self.memory_counter = 1000
        self.enter_scope("global")
    
    def get_scope_depth(self) -> int:
        """Obtiene la profundidad actual de ámbitos anidados"""
        return len(self.scopes)
    
    def __str__(self) -> str:
        """Representación en cadena de la tabla de símbolos"""
        return self.to_formatted_table()

class TypeSystem:
    """Sistema de tipos para verificación de compatibilidad y conversiones automáticas"""
    
    def __init__(self):
        """Inicializa el sistema de tipos con reglas predefinidas"""
        # Tipos básicos soportados
        self.basic_types = {'int', 'float', 'void', 'boolean'}
        
        # Reglas de promoción automática (de -> a)
        self.promotion_rules = {
            'int': ['float'],  # int puede ser promovido a float
        }
        
        # Operadores aritméticos válidos por tipo
        self.arithmetic_operators = {
            'int': ['+', '-', '*', '/', '%', '^'],
            'float': ['+', '-', '*', '/', '^'],  # float no soporta módulo
            'boolean': [],  # boolean no soporta operadores aritméticos
            'void': []
        }
        
        # Operadores relacionales válidos por tipo
        self.relational_operators = {
            'int': ['>', '<', '>=', '<=', '==', '!='],
            'float': ['>', '<', '>=', '<=', '==', '!='],
            'boolean': ['==', '!='],
            'void': []
        }
        
        # Operadores lógicos válidos por tipo
        self.logical_operators = {
            'boolean': ['&&', '||', '!'],
            'int': [],  # int no soporta operadores lógicos directamente
            'float': [],
            'void': []
        }
    
    def get_type(self, node) -> Optional[TypeInfo]:
        """
        Obtiene el tipo de un nodo del AST
        Retorna el tipo inferido o None si no se puede determinar
        """
        if not node:
            return None
        
        # Si el nodo ya tiene tipo semántico asignado
        if hasattr(node, 'semantic_type') and node.semantic_type:
            return node.semantic_type
        
        # Inferir tipo basado en el tipo de nodo
        if node.tipo == 'NUM_INT':
            return TypeInfo('int')
        elif node.tipo == 'NUM_FLOAT':
            return TypeInfo('float')
        elif node.tipo in ['TRUE', 'FALSE', 'BOOLEANO']:
            return TypeInfo('boolean')
        elif node.tipo == 'ID':
            # Para identificadores, necesitamos consultar la tabla de símbolos
            # Esto se manejará en el analizador semántico principal
            return None
        elif node.tipo in ['+', '-', '*', '/', '%', '^']:
            # Para operadores aritméticos, calcular tipo resultado
            return self._get_arithmetic_result_type(node)
        elif node.tipo in ['>', '<', '>=', '<=', '==', '!=']:
            # Operadores relacionales siempre retornan boolean
            return TypeInfo('boolean')
        elif node.tipo in ['&&', '||']:
            # Operadores lógicos siempre retornan boolean
            return TypeInfo('boolean')
        elif node.tipo == '=':
            # Asignación retorna el tipo del lado derecho
            if len(node.hijos) >= 2:
                return self.get_type(node.hijos[1])
        
        return None
    
    def _get_arithmetic_result_type(self, node) -> Optional[TypeInfo]:
        """Calcula el tipo resultado de una operación aritmética"""
        if len(node.hijos) < 2:
            return None
        
        left_type = self.get_type(node.hijos[0])
        right_type = self.get_type(node.hijos[1])
        
        if not left_type or not right_type:
            return None
        
        return self.get_operation_result_type(node.tipo, left_type, right_type)
    
    def check_compatibility(self, type1: TypeInfo, type2: TypeInfo) -> bool:
        """
        Verifica si dos tipos son compatibles
        Considera promociones automáticas
        """
        if not type1 or not type2:
            return False
        
        # Tipos exactamente iguales
        if (type1.base_type == type2.base_type and 
            type1.is_array == type2.is_array and 
            type1.array_size == type2.array_size):
            return True
        
        # Verificar promoción automática
        if self.can_convert(type1, type2) or self.can_convert(type2, type1):
            return True
        
        return False
    
    def can_convert(self, from_type: TypeInfo, to_type: TypeInfo) -> bool:
        """
        Verifica si un tipo puede ser convertido automáticamente a otro
        """
        if not from_type or not to_type:
            return False
        
        # No conversión entre arrays y no-arrays
        if from_type.is_array != to_type.is_array:
            return False
        
        # Verificar reglas de promoción
        if from_type.base_type in self.promotion_rules:
            return to_type.base_type in self.promotion_rules[from_type.base_type]
        
        return False
    
    def perform_conversion(self, value: Any, from_type: TypeInfo, to_type: TypeInfo) -> Any:
        """
        Realiza la conversión de un valor de un tipo a otro
        """
        if not self.can_convert(from_type, to_type):
            return value  # No se puede convertir, retornar valor original
        
        # Conversión int a float
        if from_type.base_type == 'int' and to_type.base_type == 'float':
            try:
                return float(value)
            except (ValueError, TypeError):
                return value
        
        return value
    
    def get_operation_result_type(self, operator: str, left_type: TypeInfo, right_type: TypeInfo) -> Optional[TypeInfo]:
        """
        Determina el tipo resultado de una operación entre dos tipos
        """
        if not left_type or not right_type:
            return None
        
        # Operadores relacionales siempre retornan boolean
        if operator in ['>', '<', '>=', '<=', '==', '!=']:
            # Verificar que los operandos sean compatibles
            if self.check_compatibility(left_type, right_type):
                return TypeInfo('boolean')
            return None
        
        # Operadores lógicos requieren operandos boolean
        if operator in ['&&', '||']:
            if left_type.base_type == 'boolean' and right_type.base_type == 'boolean':
                return TypeInfo('boolean')
            return None
        
        # Operadores aritméticos
        if operator in ['+', '-', '*', '/', '%', '^']:
            return self._get_arithmetic_operation_result(operator, left_type, right_type)
        
        return None
    
    def _get_arithmetic_operation_result(self, operator: str, left_type: TypeInfo, right_type: TypeInfo) -> Optional[TypeInfo]:
        """Calcula el tipo resultado de operaciones aritméticas"""
        # Verificar que ambos tipos sean numéricos
        if not (left_type.is_numeric() and right_type.is_numeric()):
            return None
        
        # Verificar que el operador sea válido para ambos tipos
        if (operator not in self.arithmetic_operators.get(left_type.base_type, []) or
            operator not in self.arithmetic_operators.get(right_type.base_type, [])):
            return None
        
        # Reglas de promoción de tipos en operaciones
        if left_type.base_type == 'float' or right_type.base_type == 'float':
            # Si cualquier operando es float, el resultado es float
            return TypeInfo('float')
        elif left_type.base_type == 'int' and right_type.base_type == 'int':
            # Si ambos son int, el resultado es int
            return TypeInfo('int')
        
        return None
    
    def validate_assignment(self, target_type: TypeInfo, value_type: TypeInfo) -> Tuple[bool, Optional[str]]:
        """
        Valida si una asignación es válida
        Retorna (es_válida, mensaje_error)
        """
        if not target_type or not value_type:
            return False, "Tipos no válidos para asignación"
        
        # Tipos exactamente iguales
        if (target_type.base_type == value_type.base_type and 
            target_type.is_array == value_type.is_array):
            return True, None
        
        # Verificar conversión automática
        if self.can_convert(value_type, target_type):
            return True, None
        
        # Asignación no válida
        return False, f"No se puede asignar {value_type} a {target_type}"
    
    def validate_operator_usage(self, operator: str, operand_types: List[TypeInfo]) -> Tuple[bool, Optional[str]]:
        """
        Valida si un operador puede ser usado con los tipos de operandos dados
        """
        if not operand_types:
            return False, "No hay operandos para el operador"
        
        # Operadores unarios
        if len(operand_types) == 1:
            operand_type = operand_types[0]
            
            if operator == '!':
                if operand_type.base_type == 'boolean':
                    return True, None
                else:
                    return False, f"Operador '!' requiere operando boolean, se encontró {operand_type}"
            
            if operator in ['+', '-']:  # Operadores unarios aritméticos
                if operand_type.is_numeric():
                    return True, None
                else:
                    return False, f"Operador unario '{operator}' requiere operando numérico, se encontró {operand_type}"
        
        # Operadores binarios
        elif len(operand_types) == 2:
            left_type, right_type = operand_types
            
            # Verificar compatibilidad de tipos
            if not self.check_compatibility(left_type, right_type):
                return False, f"Tipos incompatibles para operador '{operator}': {left_type} y {right_type}"
            
            # Verificar que el operador sea válido para estos tipos
            result_type = self.get_operation_result_type(operator, left_type, right_type)
            if result_type is None:
                return False, f"Operador '{operator}' no válido para tipos {left_type} y {right_type}"
            
            return True, None
        
        return False, f"Número incorrecto de operandos para operador '{operator}'"
    
    def get_common_type(self, types: List[TypeInfo]) -> Optional[TypeInfo]:
        """
        Encuentra el tipo común más específico para una lista de tipos
        Útil para expresiones condicionales y arrays
        """
        if not types:
            return None
        
        if len(types) == 1:
            return types[0]
        
        # Comenzar con el primer tipo
        common_type = types[0]
        
        for current_type in types[1:]:
            # Si son exactamente iguales, continuar
            if (common_type.base_type == current_type.base_type and 
                common_type.is_array == current_type.is_array):
                continue
            
            # Si uno puede ser promovido al otro
            if self.can_convert(common_type, current_type):
                common_type = current_type
            elif self.can_convert(current_type, common_type):
                # Mantener common_type
                continue
            else:
                # No hay tipo común
                return None
        
        return common_type
    
    def is_valid_type(self, type_info: TypeInfo) -> bool:
        """Verifica si un tipo es válido en el sistema"""
        if not type_info:
            return False
        
        return type_info.base_type in self.basic_types
    
    def infer_expression_type(self, node, symbol_table=None) -> Optional[TypeInfo]:
        """
        Infiere el tipo de una expresión completa
        Maneja expresiones aritméticas, booleanas y de asignación
        """
        if not node:
            return None
        
        # Si ya tiene tipo asignado, retornarlo
        if hasattr(node, 'semantic_type') and node.semantic_type:
            return node.semantic_type
        
        # Literales
        if node.tipo == 'NUM_INT':
            return TypeInfo('int')
        elif node.tipo == 'NUM_FLOAT':
            return TypeInfo('float')
        elif node.tipo in ['TRUE', 'FALSE', 'BOOLEANO']:
            return TypeInfo('boolean')
        
        # Identificadores - requiere tabla de símbolos
        elif node.tipo == 'ID':
            if symbol_table:
                symbol = symbol_table.lookup_variable(node.valor)
                if symbol:
                    return symbol.type_info
            return None  # Variable no declarada
        
        # Expresiones aritméticas
        elif node.tipo in ['+', '-', '*', '/', '%', '^']:
            return self._infer_arithmetic_expression_type(node, symbol_table)
        
        # Expresiones relacionales
        elif node.tipo in ['>', '<', '>=', '<=', '==', '!=']:
            return self._infer_relational_expression_type(node, symbol_table)
        
        # Expresiones lógicas
        elif node.tipo in ['&&', '||']:
            return self._infer_logical_expression_type(node, symbol_table)
        
        # Asignación
        elif node.tipo == '=':
            return self._infer_assignment_type(node, symbol_table)
        
        # Expresiones entre paréntesis o componentes
        elif node.tipo == 'COMPONENTE' and len(node.hijos) == 1:
            return self.infer_expression_type(node.hijos[0], symbol_table)
        
        return None
    
    def _infer_arithmetic_expression_type(self, node, symbol_table=None) -> Optional[TypeInfo]:
        """Infiere el tipo de expresiones aritméticas"""
        if len(node.hijos) < 2:
            return None
        
        left_type = self.infer_expression_type(node.hijos[0], symbol_table)
        right_type = self.infer_expression_type(node.hijos[1], symbol_table)
        
        if not left_type or not right_type:
            return None
        
        # Verificar que ambos tipos sean numéricos
        if not (left_type.is_numeric() and right_type.is_numeric()):
            return None
        
        # Aplicar reglas de promoción de tipos
        return self.get_operation_result_type(node.tipo, left_type, right_type)
    
    def _infer_relational_expression_type(self, node, symbol_table=None) -> Optional[TypeInfo]:
        """Infiere el tipo de expresiones relacionales (siempre boolean)"""
        if len(node.hijos) < 2:
            return None
        
        left_type = self.infer_expression_type(node.hijos[0], symbol_table)
        right_type = self.infer_expression_type(node.hijos[1], symbol_table)
        
        if not left_type or not right_type:
            return None
        
        # Verificar compatibilidad de tipos para comparación
        if self.check_compatibility(left_type, right_type):
            return TypeInfo('boolean')
        
        return None
    
    def _infer_logical_expression_type(self, node, symbol_table=None) -> Optional[TypeInfo]:
        """Infiere el tipo de expresiones lógicas (siempre boolean)"""
        if len(node.hijos) < 2:
            return None
        
        left_type = self.infer_expression_type(node.hijos[0], symbol_table)
        right_type = self.infer_expression_type(node.hijos[1], symbol_table)
        
        if not left_type or not right_type:
            return None
        
        # Ambos operandos deben ser boolean
        if left_type.base_type == 'boolean' and right_type.base_type == 'boolean':
            return TypeInfo('boolean')
        
        return None
    
    def _infer_assignment_type(self, node, symbol_table=None) -> Optional[TypeInfo]:
        """Infiere el tipo de una asignación (tipo del lado derecho)"""
        if len(node.hijos) < 2:
            return None
        
        # El tipo de la asignación es el tipo del valor asignado (lado derecho)
        return self.infer_expression_type(node.hijos[1], symbol_table)
    
    def validate_expression_types(self, node, symbol_table=None) -> Tuple[bool, List[str]]:
        """
        Valida los tipos en una expresión completa
        Retorna (es_válida, lista_errores)
        """
        errors = []
        
        if not node:
            return False, ["Nodo de expresión nulo"]
        
        # Validar expresiones aritméticas
        if node.tipo in ['+', '-', '*', '/', '%', '^']:
            valid, error_msgs = self._validate_arithmetic_expression(node, symbol_table)
            if not valid:
                errors.extend(error_msgs)
        
        # Validar expresiones relacionales
        elif node.tipo in ['>', '<', '>=', '<=', '==', '!=']:
            valid, error_msgs = self._validate_relational_expression(node, symbol_table)
            if not valid:
                errors.extend(error_msgs)
        
        # Validar expresiones lógicas
        elif node.tipo in ['&&', '||']:
            valid, error_msgs = self._validate_logical_expression(node, symbol_table)
            if not valid:
                errors.extend(error_msgs)
        
        # Validar asignaciones
        elif node.tipo == '=':
            valid, error_msgs = self._validate_assignment_expression(node, symbol_table)
            if not valid:
                errors.extend(error_msgs)
        
        # Validar identificadores
        elif node.tipo == 'ID':
            if symbol_table and not symbol_table.is_declared(node.valor):
                errors.append(f"Variable '{node.valor}' no declarada en línea {node.linea}")
        
        # Validar recursivamente los hijos
        for hijo in node.hijos:
            child_valid, child_errors = self.validate_expression_types(hijo, symbol_table)
            errors.extend(child_errors)
        
        return len(errors) == 0, errors
    
    def _validate_arithmetic_expression(self, node, symbol_table=None) -> Tuple[bool, List[str]]:
        """Valida expresiones aritméticas"""
        errors = []
        
        if len(node.hijos) < 2:
            errors.append(f"Operador aritmético '{node.tipo}' requiere dos operandos en línea {node.linea}")
            return False, errors
        
        left_type = self.infer_expression_type(node.hijos[0], symbol_table)
        right_type = self.infer_expression_type(node.hijos[1], symbol_table)
        
        if not left_type:
            errors.append(f"No se puede determinar el tipo del operando izquierdo en línea {node.linea}")
        
        if not right_type:
            errors.append(f"No se puede determinar el tipo del operando derecho en línea {node.linea}")
        
        if left_type and right_type:
            if not (left_type.is_numeric() and right_type.is_numeric()):
                errors.append(f"Operador '{node.tipo}' requiere operandos numéricos, se encontraron {left_type} y {right_type} en línea {node.linea}")
            
            # Verificar operador específico (ej: módulo solo para enteros)
            if node.tipo == '%' and (left_type.base_type == 'float' or right_type.base_type == 'float'):
                errors.append(f"Operador módulo '%' no válido con tipos float en línea {node.linea}")
        
        return len(errors) == 0, errors
    
    def _validate_relational_expression(self, node, symbol_table=None) -> Tuple[bool, List[str]]:
        """Valida expresiones relacionales"""
        errors = []
        
        if len(node.hijos) < 2:
            errors.append(f"Operador relacional '{node.tipo}' requiere dos operandos en línea {node.linea}")
            return False, errors
        
        left_type = self.infer_expression_type(node.hijos[0], symbol_table)
        right_type = self.infer_expression_type(node.hijos[1], symbol_table)
        
        if not left_type:
            errors.append(f"No se puede determinar el tipo del operando izquierdo en línea {node.linea}")
        
        if not right_type:
            errors.append(f"No se puede determinar el tipo del operando derecho en línea {node.linea}")
        
        if left_type and right_type:
            if not self.check_compatibility(left_type, right_type):
                errors.append(f"Tipos incompatibles para comparación: {left_type} y {right_type} en línea {node.linea}")
        
        return len(errors) == 0, errors
    
    def _validate_logical_expression(self, node, symbol_table=None) -> Tuple[bool, List[str]]:
        """Valida expresiones lógicas"""
        errors = []
        
        if len(node.hijos) < 2:
            errors.append(f"Operador lógico '{node.tipo}' requiere dos operandos en línea {node.linea}")
            return False, errors
        
        left_type = self.infer_expression_type(node.hijos[0], symbol_table)
        right_type = self.infer_expression_type(node.hijos[1], symbol_table)
        
        if not left_type:
            errors.append(f"No se puede determinar el tipo del operando izquierdo en línea {node.linea}")
        
        if not right_type:
            errors.append(f"No se puede determinar el tipo del operando derecho en línea {node.linea}")
        
        if left_type and right_type:
            if left_type.base_type != 'boolean':
                errors.append(f"Operador lógico '{node.tipo}' requiere operando boolean izquierdo, se encontró {left_type} en línea {node.linea}")
            
            if right_type.base_type != 'boolean':
                errors.append(f"Operador lógico '{node.tipo}' requiere operando boolean derecho, se encontró {right_type} en línea {node.linea}")
        
        return len(errors) == 0, errors
    
    def _validate_assignment_expression(self, node, symbol_table=None) -> Tuple[bool, List[str]]:
        """Valida expresiones de asignación"""
        errors = []
        
        if len(node.hijos) < 2:
            errors.append(f"Asignación requiere variable y valor en línea {node.linea}")
            return False, errors
        
        # Verificar que el lado izquierdo sea un identificador
        left_node = node.hijos[0]
        if left_node.tipo != 'ID':
            errors.append(f"Lado izquierdo de asignación debe ser una variable en línea {node.linea}")
            return False, errors
        
        # Verificar que la variable esté declarada
        if symbol_table:
            symbol = symbol_table.lookup_variable(left_node.valor)
            if not symbol:
                errors.append(f"Variable '{left_node.valor}' no declarada en línea {node.linea}")
                return False, errors
            
            # Verificar compatibilidad de tipos
            right_type = self.infer_expression_type(node.hijos[1], symbol_table)
            if right_type:
                valid, error_msg = self.validate_assignment(symbol.type_info, right_type)
                if not valid:
                    errors.append(f"{error_msg} en línea {node.linea}")
        
        return len(errors) == 0, errors

# Constantes para tipos predefinidos
TIPO_INT = TypeInfo('int')
TIPO_FLOAT = TypeInfo('float')
TIPO_VOID = TypeInfo('void')
TIPO_BOOLEAN = TypeInfo('boolean')

# Diccionario de tipos básicos para fácil acceso
TIPOS_BASICOS = {
    'int': TIPO_INT,
    'float': TIPO_FLOAT,
    'void': TIPO_VOID,
    'boolean': TIPO_BOOLEAN
}

def crear_tipo_desde_string(tipo_str: str) -> TypeInfo:
    """Crea un objeto TypeInfo a partir de una cadena de tipo"""
    if tipo_str in TIPOS_BASICOS:
        return TIPOS_BASICOS[tipo_str]
    else:
        # Para tipos no reconocidos, crear un tipo básico
        return TypeInfo(tipo_str)

def es_tipo_valido(tipo_str: str) -> bool:
    """Verifica si una cadena representa un tipo válido"""
    return tipo_str in TIPOS_BASICOS

class ErrorReporter:
    """Maneja la detección, recolección y formateo de errores semánticos"""
    
    def __init__(self):
        """Inicializa el reportador de errores"""
        self.errors = []  # Lista de errores semánticos
        self.warnings = []  # Lista de advertencias
        self.error_counts = {
            'undeclared_variable': 0,
            'duplicate_declaration': 0,
            'type_incompatibility': 0,
            'invalid_conversion': 0,
            'operator_misuse': 0,
            'other': 0
        }
    
    def add_error(self, error_type: str, message: str, line: int, column: int, severity: str = 'error'):
        """
        Agrega un error o advertencia al reporte
        
        Args:
            error_type: Tipo de error ('undeclared_variable', 'duplicate_declaration', etc.)
            message: Mensaje descriptivo del error
            line: Número de línea donde ocurre el error
            column: Número de columna donde ocurre el error
            severity: Severidad del error ('error' o 'warning')
        """
        semantic_error = SemanticError(
            error_type=error_type,
            message=message,
            line=line,
            column=column,
            severity=severity
        )
        
        if severity == 'error':
            self.errors.append(semantic_error)
        else:
            self.warnings.append(semantic_error)
        
        # Actualizar contadores
        if error_type in self.error_counts:
            self.error_counts[error_type] += 1
        else:
            self.error_counts['other'] += 1
    
    def add_undeclared_variable_error(self, variable_name: str, line: int, column: int):
        """Agrega un error de variable no declarada"""
        message = f"Variable '{variable_name}' no declarada"
        self.add_error('undeclared_variable', message, line, column)
    
    def add_duplicate_declaration_error(self, variable_name: str, line: int, column: int, 
                                      original_line: int = None):
        """Agrega un error de declaración duplicada"""
        if original_line:
            message = f"Variable '{variable_name}' ya declarada en línea {original_line}"
        else:
            message = f"Variable '{variable_name}' ya declarada en el ámbito actual"
        self.add_error('duplicate_declaration', message, line, column)
    
    def add_type_incompatibility_error(self, expected_type: str, found_type: str, 
                                     line: int, column: int, context: str = ""):
        """Agrega un error de incompatibilidad de tipos"""
        if context:
            message = f"Incompatibilidad de tipos en {context}: se esperaba {expected_type}, se encontró {found_type}"
        else:
            message = f"Incompatibilidad de tipos: se esperaba {expected_type}, se encontró {found_type}"
        self.add_error('type_incompatibility', message, line, column)
    
    def add_invalid_conversion_error(self, from_type: str, to_type: str, line: int, column: int):
        """Agrega un error de conversión inválida"""
        message = f"Conversión inválida de {from_type} a {to_type}"
        self.add_error('invalid_conversion', message, line, column)
    
    def add_operator_misuse_error(self, operator: str, operand_types: List[str], 
                                line: int, column: int):
        """Agrega un error de uso incorrecto de operador"""
        types_str = ", ".join(operand_types)
        message = f"Operador '{operator}' no válido para tipos: {types_str}"
        self.add_error('operator_misuse', message, line, column)
    
    def add_assignment_error(self, variable_name: str, variable_type: str, 
                           value_type: str, line: int, column: int):
        """Agrega un error específico de asignación"""
        message = f"No se puede asignar valor de tipo {value_type} a variable '{variable_name}' de tipo {variable_type}"
        self.add_error('type_incompatibility', message, line, column)
    
    def add_warning(self, warning_type: str, message: str, line: int, column: int):
        """Agrega una advertencia al reporte"""
        self.add_error(warning_type, message, line, column, severity='warning')
    
    def has_errors(self) -> bool:
        """Verifica si hay errores reportados"""
        return len(self.errors) > 0
    
    def has_warnings(self) -> bool:
        """Verifica si hay advertencias reportadas"""
        return len(self.warnings) > 0
    
    def get_errors(self) -> List[SemanticError]:
        """Obtiene la lista de errores"""
        return self.errors.copy()
    
    def get_warnings(self) -> List[SemanticError]:
        """Obtiene la lista de advertencias"""
        return self.warnings.copy()
    
    def get_all_issues(self) -> List[SemanticError]:
        """Obtiene todos los errores y advertencias combinados"""
        return self.errors + self.warnings
    
    def get_error_count(self) -> int:
        """Obtiene el número total de errores"""
        return len(self.errors)
    
    def get_warning_count(self) -> int:
        """Obtiene el número total de advertencias"""
        return len(self.warnings)
    
    def get_error_count_by_type(self, error_type: str) -> int:
        """Obtiene el número de errores de un tipo específico"""
        return self.error_counts.get(error_type, 0)
    
    def clear(self):
        """Limpia todos los errores y advertencias"""
        self.errors.clear()
        self.warnings.clear()
        for key in self.error_counts:
            self.error_counts[key] = 0
    
    def format_errors(self) -> str:
        """Formatea los errores para mostrar en la GUI"""
        if not self.has_errors() and not self.has_warnings():
            return "No se encontraron errores semánticos"
        
        resultado = "ERRORES SEMÁNTICOS:\n"
        resultado += "=" * 100 + "\n"
        resultado += "| {:<12} | {:<15} | {:<50} | {:<8} | {:<8} |\n".format(
            "SEVERIDAD", "TIPO", "DESCRIPCIÓN", "LÍNEA", "COLUMNA"
        )
        resultado += "=" * 100 + "\n"
        
        # Mostrar errores primero
        all_issues = sorted(self.get_all_issues(), key=lambda x: (x.line, x.column))
        
        for issue in all_issues:
            # Truncar descripción si es muy larga
            descripcion = issue.message
            if len(descripcion) > 48:
                descripcion = descripcion[:45] + "..."
            
            resultado += "| {:<12} | {:<15} | {:<50} | {:<8} | {:<8} |\n".format(
                issue.severity.upper(),
                issue.error_type,
                descripcion,
                issue.line,
                issue.column
            )
        
        resultado += "=" * 100 + "\n"
        
        # Agregar resumen
        resultado += f"\nRESUMEN:\n"
        resultado += f"- Errores: {self.get_error_count()}\n"
        resultado += f"- Advertencias: {self.get_warning_count()}\n"
        
        # Mostrar conteo por tipo si hay errores
        if self.has_errors():
            resultado += f"\nERRORES POR TIPO:\n"
            for error_type, count in self.error_counts.items():
                if count > 0:
                    resultado += f"- {error_type.replace('_', ' ').title()}: {count}\n"
        
        return resultado
    
    def format_for_gui(self) -> Dict[str, Any]:
        """Formatea los errores para la interfaz gráfica"""
        return {
            'errors': [
                {
                    'type': error.error_type,
                    'message': error.message,
                    'line': error.line,
                    'column': error.column,
                    'severity': error.severity
                }
                for error in self.errors
            ],
            'warnings': [
                {
                    'type': warning.error_type,
                    'message': warning.message,
                    'line': warning.line,
                    'column': warning.column,
                    'severity': warning.severity
                }
                for warning in self.warnings
            ],
            'summary': {
                'total_errors': self.get_error_count(),
                'total_warnings': self.get_warning_count(),
                'error_counts': self.error_counts.copy()
            }
        }
    
    def export_to_file(self, filename: str):
        """Exporta los errores a un archivo de texto"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(self.format_errors())
            return True
        except Exception as e:
            print(f"Error al exportar errores a archivo: {e}")
            return False
    
    def get_errors_by_line(self, line_number: int) -> List[SemanticError]:
        """Obtiene todos los errores y advertencias de una línea específica"""
        return [issue for issue in self.get_all_issues() if issue.line == line_number]
    
    def get_most_severe_error(self) -> Optional[SemanticError]:
        """Obtiene el error más severo (primer error si hay errores, sino primera advertencia)"""
        if self.errors:
            return min(self.errors, key=lambda x: (x.line, x.column))
        elif self.warnings:
            return min(self.warnings, key=lambda x: (x.line, x.column))
        return None
    
    def __str__(self) -> str:
        """Representación en cadena del reportador de errores"""
        return self.format_errors()

class SemanticErrorDetector:
    """Detecta errores semánticos específicos durante el análisis del AST"""
    
    def __init__(self, error_reporter: ErrorReporter, symbol_table: SymbolTable, type_system: TypeSystem):
        """
        Inicializa el detector de errores semánticos
        
        Args:
            error_reporter: Instancia del reportador de errores
            symbol_table: Tabla de símbolos para verificar declaraciones
            type_system: Sistema de tipos para verificar compatibilidad
        """
        self.error_reporter = error_reporter
        self.symbol_table = symbol_table
        self.type_system = type_system
    
    def check_undeclared_variables(self, node) -> bool:
        """
        Verifica si hay variables no declaradas en el nodo y sus hijos
        
        Args:
            node: Nodo del AST a verificar
            
        Returns:
            True si no hay errores, False si se encontraron variables no declaradas
        """
        if not node:
            return True
        
        errors_found = False
        
        # Verificar si el nodo actual es un identificador
        if node.tipo == 'ID':
            if not self.symbol_table.is_declared(node.valor):
                self.error_reporter.add_undeclared_variable_error(
                    node.valor, node.linea, node.columna
                )
                errors_found = True
        
        # Verificar recursivamente en los hijos
        for hijo in node.hijos:
            if not self.check_undeclared_variables(hijo):
                errors_found = True
        
        return not errors_found
    
    def check_duplicate_declarations(self, node) -> bool:
        """
        Verifica declaraciones duplicadas en el nodo actual
        
        Args:
            node: Nodo del AST a verificar (debe ser DECLARACION_VARIABLE)
            
        Returns:
            True si no hay duplicados, False si se encontró una declaración duplicada
        """
        if not node or node.tipo != 'DECLARACION_VARIABLE':
            return True
        
        # Buscar el tipo y los identificadores en la declaración
        tipo_nodo = None
        identificadores = []
        
        for hijo in node.hijos:
            if hijo.tipo == 'TIPO':
                tipo_nodo = hijo
            elif hijo.tipo == 'IDENTIFICADOR':
                # Recopilar todos los IDs en la declaración
                for id_hijo in hijo.hijos:
                    if id_hijo.tipo == 'ID':
                        identificadores.append(id_hijo)
        
        if not tipo_nodo or not identificadores:
            return True
        
        # Verificar cada identificador
        errors_found = False
        tipo_info = crear_tipo_desde_string(tipo_nodo.valor)
        
        for id_nodo in identificadores:
            variable_name = id_nodo.valor
            
            # Verificar si ya está declarada en el ámbito actual
            if self.symbol_table.is_declared_in_current_scope(variable_name):
                # Buscar la declaración original para obtener su línea
                existing_symbol = self.symbol_table.lookup_variable(variable_name)
                original_line = existing_symbol.line if existing_symbol else None
                
                self.error_reporter.add_duplicate_declaration_error(
                    variable_name, id_nodo.linea, id_nodo.columna, original_line
                )
                errors_found = True
            else:
                # Declarar la variable si no hay duplicado
                self.symbol_table.declare_variable(
                    variable_name, tipo_info, id_nodo.linea, id_nodo.columna
                )
        
        return not errors_found
    
    def check_type_compatibility(self, node) -> bool:
        """
        Verifica la compatibilidad de tipos en expresiones y asignaciones
        
        Args:
            node: Nodo del AST a verificar
            
        Returns:
            True si no hay errores de tipo, False si se encontraron incompatibilidades
        """
        if not node:
            return True
        
        errors_found = False
        
        # Verificar asignaciones
        if node.tipo == '=':
            if not self._check_assignment_compatibility(node):
                errors_found = True
        
        # Verificar operaciones aritméticas
        elif node.tipo in ['+', '-', '*', '/', '%', '^']:
            if not self._check_arithmetic_compatibility(node):
                errors_found = True
        
        # Verificar operaciones relacionales
        elif node.tipo in ['>', '<', '>=', '<=', '==', '!=']:
            if not self._check_relational_compatibility(node):
                errors_found = True
        
        # Verificar operaciones lógicas
        elif node.tipo in ['&&', '||']:
            if not self._check_logical_compatibility(node):
                errors_found = True
        
        # Verificar recursivamente en los hijos
        for hijo in node.hijos:
            if not self.check_type_compatibility(hijo):
                errors_found = True
        
        return not errors_found
    
    def _check_assignment_compatibility(self, node) -> bool:
        """Verifica la compatibilidad de tipos en una asignación"""
        if len(node.hijos) < 2:
            return True
        
        left_node = node.hijos[0]
        right_node = node.hijos[1]
        
        # El lado izquierdo debe ser un identificador
        if left_node.tipo != 'ID':
            self.error_reporter.add_error(
                'invalid_assignment',
                "El lado izquierdo de la asignación debe ser una variable",
                node.linea, node.columna
            )
            return False
        
        # Verificar que la variable esté declarada
        symbol = self.symbol_table.lookup_variable(left_node.valor)
        if not symbol:
            # Este error ya se maneja en check_undeclared_variables
            return False
        
        # Obtener el tipo del lado derecho
        right_type = self.type_system.infer_expression_type(right_node, self.symbol_table)
        if not right_type:
            self.error_reporter.add_error(
                'type_inference_failed',
                f"No se puede determinar el tipo de la expresión en la asignación",
                right_node.linea, right_node.columna
            )
            return False
        
        # Verificar compatibilidad de tipos
        is_valid, error_msg = self.type_system.validate_assignment(symbol.type_info, right_type)
        if not is_valid:
            self.error_reporter.add_assignment_error(
                left_node.valor, str(symbol.type_info), str(right_type),
                node.linea, node.columna
            )
            return False
        
        return True
    
    def _check_arithmetic_compatibility(self, node) -> bool:
        """Verifica la compatibilidad de tipos en operaciones aritméticas"""
        if len(node.hijos) < 2:
            return True
        
        left_type = self.type_system.infer_expression_type(node.hijos[0], self.symbol_table)
        right_type = self.type_system.infer_expression_type(node.hijos[1], self.symbol_table)
        
        if not left_type or not right_type:
            return True  # Los errores de inferencia se manejan en otro lugar
        
        # Verificar que ambos tipos sean numéricos
        if not (left_type.is_numeric() and right_type.is_numeric()):
            self.error_reporter.add_operator_misuse_error(
                node.tipo, [str(left_type), str(right_type)],
                node.linea, node.columna
            )
            return False
        
        # Verificar operador específico (ej: módulo solo para enteros)
        if node.tipo == '%':
            if left_type.base_type == 'float' or right_type.base_type == 'float':
                self.error_reporter.add_error(
                    'operator_misuse',
                    f"Operador módulo '%' no válido con tipos float",
                    node.linea, node.columna
                )
                return False
        
        return True
    
    def _check_relational_compatibility(self, node) -> bool:
        """Verifica la compatibilidad de tipos en operaciones relacionales"""
        if len(node.hijos) < 2:
            return True
        
        left_type = self.type_system.infer_expression_type(node.hijos[0], self.symbol_table)
        right_type = self.type_system.infer_expression_type(node.hijos[1], self.symbol_table)
        
        if not left_type or not right_type:
            return True  # Los errores de inferencia se manejan en otro lugar
        
        # Verificar compatibilidad para comparación
        if not self.type_system.check_compatibility(left_type, right_type):
            self.error_reporter.add_type_incompatibility_error(
                str(left_type), str(right_type),
                node.linea, node.columna,
                f"comparación con operador '{node.tipo}'"
            )
            return False
        
        return True
    
    def _check_logical_compatibility(self, node) -> bool:
        """Verifica la compatibilidad de tipos en operaciones lógicas"""
        if len(node.hijos) < 2:
            return True
        
        left_type = self.type_system.infer_expression_type(node.hijos[0], self.symbol_table)
        right_type = self.type_system.infer_expression_type(node.hijos[1], self.symbol_table)
        
        if not left_type or not right_type:
            return True  # Los errores de inferencia se manejan en otro lugar
        
        # Ambos operandos deben ser boolean
        if left_type.base_type != 'boolean':
            self.error_reporter.add_type_incompatibility_error(
                'boolean', str(left_type),
                node.hijos[0].linea, node.hijos[0].columna,
                f"operando izquierdo del operador '{node.tipo}'"
            )
            return False
        
        if right_type.base_type != 'boolean':
            self.error_reporter.add_type_incompatibility_error(
                'boolean', str(right_type),
                node.hijos[1].linea, node.hijos[1].columna,
                f"operando derecho del operador '{node.tipo}'"
            )
            return False
        
        return True
    
    def check_invalid_conversions(self, node) -> bool:
        """
        Verifica conversiones de tipo inválidas
        
        Args:
            node: Nodo del AST a verificar
            
        Returns:
            True si no hay conversiones inválidas, False si se encontraron errores
        """
        if not node:
            return True
        
        errors_found = False
        
        # Verificar conversiones en asignaciones
        if node.tipo == '=' and len(node.hijos) >= 2:
            left_node = node.hijos[0]
            right_node = node.hijos[1]
            
            if left_node.tipo == 'ID':
                symbol = self.symbol_table.lookup_variable(left_node.valor)
                if symbol:
                    right_type = self.type_system.infer_expression_type(right_node, self.symbol_table)
                    if right_type:
                        # Verificar si la conversión es válida
                        if not self.type_system.can_convert(right_type, symbol.type_info):
                            # Solo reportar si no son compatibles de ninguna manera
                            if not self.type_system.check_compatibility(right_type, symbol.type_info):
                                self.error_reporter.add_invalid_conversion_error(
                                    str(right_type), str(symbol.type_info),
                                    node.linea, node.columna
                                )
                                errors_found = True
        
        # Verificar recursivamente en los hijos
        for hijo in node.hijos:
            if not self.check_invalid_conversions(hijo):
                errors_found = True
        
        return not errors_found

# Funciones utilitarias para trabajar con ASTs anotados

def create_fully_annotated_ast(ast_root: Nodo, symbol_table: SymbolTable, 
                              type_system: TypeSystem) -> AnnotatedASTNode:
    """
    Función de conveniencia para crear un AST completamente anotado
    
    Args:
        ast_root: Nodo raíz del AST original
        symbol_table: Tabla de símbolos construida
        type_system: Sistema de tipos configurado
        
    Returns:
        AST completamente anotado con información semántica
    """
    annotator = ASTAnnotator(type_system, symbol_table)
    return annotator.annotate_ast(ast_root)

def export_annotated_ast_to_json(annotated_ast: AnnotatedASTNode, filename: str) -> bool:
    """
    Exporta un AST anotado a un archivo JSON
    
    Args:
        annotated_ast: AST anotado a exportar
        filename: Nombre del archivo de destino
        
    Returns:
        True si se exportó exitosamente, False en caso de error
    """
    try:
        import json
        
        ast_dict = annotated_ast.to_annotated_dict()
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(ast_dict, f, indent=2, ensure_ascii=False)
        
        return True
    except Exception as e:
        print(f"Error al exportar AST anotado a JSON: {e}")
        return False

def export_annotated_ast_to_text(annotated_ast: AnnotatedASTNode, filename: str) -> bool:
    """
    Exporta un AST anotado a un archivo de texto formateado
    
    Args:
        annotated_ast: AST anotado a exportar
        filename: Nombre del archivo de destino
        
    Returns:
        True si se exportó exitosamente, False en caso de error
    """
    try:
        formatted_content = annotated_ast.to_formatted_string()
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("AST ANOTADO CON INFORMACIÓN SEMÁNTICA\n")
            f.write("=" * 50 + "\n\n")
            f.write(formatted_content)
        
        return True
    except Exception as e:
        print(f"Error al exportar AST anotado a texto: {e}")
        return False

def compare_ast_annotations(ast1: AnnotatedASTNode, ast2: AnnotatedASTNode) -> Dict[str, Any]:
    """
    Compara las anotaciones semánticas entre dos ASTs
    
    Args:
        ast1: Primer AST anotado
        ast2: Segundo AST anotado
        
    Returns:
        Diccionario con resultados de la comparación
    """
    comparison = {
        'structure_match': True,
        'annotation_differences': [],
        'summary': {
            'ast1_annotated_nodes': 0,
            'ast2_annotated_nodes': 0,
            'matching_annotations': 0
        }
    }
    
    def compare_nodes(node1: AnnotatedASTNode, node2: AnnotatedASTNode, path: str = "root"):
        # Verificar estructura básica
        if node1.tipo != node2.tipo or node1.valor != node2.valor:
            comparison['structure_match'] = False
            return
        
        # Contar nodos anotados
        if node1.has_semantic_info():
            comparison['summary']['ast1_annotated_nodes'] += 1
        if node2.has_semantic_info():
            comparison['summary']['ast2_annotated_nodes'] += 1
        
        # Comparar anotaciones semánticas
        if node1.has_semantic_info() and node2.has_semantic_info():
            if (str(node1.semantic_type) == str(node2.semantic_type) and
                node1.semantic_value == node2.semantic_value):
                comparison['summary']['matching_annotations'] += 1
            else:
                comparison['annotation_differences'].append({
                    'path': path,
                    'node_type': node1.tipo,
                    'ast1_type': str(node1.semantic_type) if node1.semantic_type else None,
                    'ast2_type': str(node2.semantic_type) if node2.semantic_type else None,
                    'ast1_value': node1.semantic_value,
                    'ast2_value': node2.semantic_value
                })
        elif node1.has_semantic_info() != node2.has_semantic_info():
            comparison['annotation_differences'].append({
                'path': path,
                'node_type': node1.tipo,
                'difference': 'One node has annotations, the other does not'
            })
        
        # Comparar hijos recursivamente
        if len(node1.hijos) == len(node2.hijos):
            for i, (child1, child2) in enumerate(zip(node1.hijos, node2.hijos)):
                if isinstance(child1, AnnotatedASTNode) and isinstance(child2, AnnotatedASTNode):
                    compare_nodes(child1, child2, f"{path}.child[{i}]")
    
    compare_nodes(ast1, ast2)
    return comparison

def validate_ast_annotations(annotated_ast: AnnotatedASTNode, 
                           symbol_table: SymbolTable) -> List[str]:
    """
    Valida que las anotaciones del AST sean consistentes con la tabla de símbolos
    
    Args:
        annotated_ast: AST anotado a validar
        symbol_table: Tabla de símbolos de referencia
        
    Returns:
        Lista de errores de validación encontrados
    """
    errors = []
    
    def validate_node(node: AnnotatedASTNode, path: str = "root"):
        # Validar referencias de símbolos
        if node.tipo == 'ID' and node.symbol_ref:
            # Verificar que el símbolo existe en la tabla
            actual_symbol = symbol_table.lookup_variable(node.valor)
            if not actual_symbol:
                errors.append(f"Nodo en {path}: referencia a símbolo inexistente '{node.valor}'")
            elif actual_symbol != node.symbol_ref:
                errors.append(f"Nodo en {path}: referencia de símbolo inconsistente para '{node.valor}'")
        
        # Validar tipos semánticos
        if node.semantic_type and node.tipo == 'ID' and node.symbol_ref:
            if str(node.semantic_type) != str(node.symbol_ref.type_info):
                errors.append(f"Nodo en {path}: tipo semántico inconsistente con símbolo")
        
        # Validar valores constantes
        if node.is_constant and node.semantic_value is None:
            errors.append(f"Nodo en {path}: marcado como constante pero sin valor semántico")
        
        # Validar hijos recursivamente
        for i, hijo in enumerate(node.hijos):
            if isinstance(hijo, AnnotatedASTNode):
                validate_node(hijo, f"{path}.child[{i}]")
    
    validate_node(annotated_ast)
    return errors

def get_annotation_statistics(annotated_ast: AnnotatedASTNode) -> Dict[str, Any]:
    """
    Obtiene estadísticas sobre las anotaciones en un AST
    
    Args:
        annotated_ast: AST anotado a analizar
        
    Returns:
        Diccionario con estadísticas de anotación
    """
    stats = {
        'total_nodes': 0,
        'annotated_nodes': 0,
        'nodes_with_type': 0,
        'nodes_with_value': 0,
        'nodes_with_symbol_ref': 0,
        'constant_nodes': 0,
        'lvalue_nodes': 0,
        'types_distribution': {},
        'node_types_distribution': {}
    }
    
    def analyze_node(node: AnnotatedASTNode):
        stats['total_nodes'] += 1
        
        # Contar distribución de tipos de nodo
        if node.tipo not in stats['node_types_distribution']:
            stats['node_types_distribution'][node.tipo] = 0
        stats['node_types_distribution'][node.tipo] += 1
        
        # Analizar anotaciones semánticas
        if node.has_semantic_info():
            stats['annotated_nodes'] += 1
        
        if node.semantic_type:
            stats['nodes_with_type'] += 1
            type_str = str(node.semantic_type)
            if type_str not in stats['types_distribution']:
                stats['types_distribution'][type_str] = 0
            stats['types_distribution'][type_str] += 1
        
        if node.semantic_value is not None:
            stats['nodes_with_value'] += 1
        
        if node.symbol_ref:
            stats['nodes_with_symbol_ref'] += 1
        
        if node.is_constant:
            stats['constant_nodes'] += 1
        
        if node.is_lvalue:
            stats['lvalue_nodes'] += 1
        
        # Analizar hijos recursivamente
        for hijo in node.hijos:
            if isinstance(hijo, AnnotatedASTNode):
                analyze_node(hijo)
    
    analyze_node(annotated_ast)
    
    # Calcular porcentajes
    if stats['total_nodes'] > 0:
        stats['annotation_percentage'] = (stats['annotated_nodes'] / stats['total_nodes']) * 100
        stats['type_annotation_percentage'] = (stats['nodes_with_type'] / stats['total_nodes']) * 100
    else:
        stats['annotation_percentage'] = 0
        stats['type_annotation_percentage'] = 0
    
    return stats

class SemanticVisitor:
    """
    Implementa el patrón visitor para recorrer y procesar nodos del AST
    durante el análisis semántico
    """
    
    def __init__(self, symbol_table: SymbolTable, type_system: TypeSystem, error_reporter: ErrorReporter):
        """
        Inicializa el visitor semántico
        
        Args:
            symbol_table: Tabla de símbolos para gestionar declaraciones
            type_system: Sistema de tipos para verificación de compatibilidad
            error_reporter: Reportador de errores para registrar problemas
        """
        self.symbol_table = symbol_table
        self.type_system = type_system
        self.error_reporter = error_reporter
        self.error_detector = SemanticErrorDetector(error_reporter, symbol_table, type_system)
    
    def visit(self, node) -> AnnotatedASTNode:
        """
        Visita un nodo del AST y retorna su versión anotada
        
        Args:
            node: Nodo del AST a visitar
            
        Returns:
            Nodo anotado con información semántica
        """
        if not node:
            return None
        
        # Crear nodo anotado
        annotated_node = AnnotatedASTNode.from_node(node)
        
        # Procesar según el tipo de nodo
        method_name = f'visit_{node.tipo.lower()}'
        if hasattr(self, method_name):
            method = getattr(self, method_name)
            method(annotated_node)
        else:
            # Procesamiento genérico
            self.visit_generic(annotated_node)
        
        # Visitar hijos recursivamente
        annotated_children = []
        for hijo in node.hijos:
            annotated_child = self.visit(hijo)
            if annotated_child:
                annotated_children.append(annotated_child)
        
        annotated_node.hijos = annotated_children
        
        # Actualizar referencias padre
        for hijo in annotated_node.hijos:
            hijo.padre = annotated_node
        
        return annotated_node
    
    def visit_generic(self, node: AnnotatedASTNode):
        """Procesamiento genérico para nodos no especializados"""
        # Inferir tipo si es posible
        inferred_type = self.type_system.infer_expression_type(node, self.symbol_table)
        if inferred_type:
            node.set_semantic_type(inferred_type)
    
    def visit_declaracion_variable(self, node: AnnotatedASTNode):
        """Procesa declaraciones de variables"""
        # Verificar duplicados y agregar a tabla de símbolos
        self.error_detector.check_duplicate_declarations(node)
    
    def visit_id(self, node: AnnotatedASTNode):
        """Procesa identificadores"""
        # Buscar en tabla de símbolos
        symbol = self.symbol_table.lookup_variable(node.valor)
        if symbol:
            node.set_symbol_reference(symbol)
            node.set_semantic_type(symbol.type_info)
            node.is_lvalue = True
        else:
            # Reportar variable no declarada
            self.error_reporter.add_undeclared_variable_error(
                node.valor, node.linea, node.columna
            )
    
    def visit_num_int(self, node: AnnotatedASTNode):
        """Procesa números enteros"""
        node.set_semantic_type(TypeInfo('int'))
        try:
            node.set_semantic_value(int(node.valor))
            node.is_constant = True
        except ValueError:
            pass
    
    def visit_num_float(self, node: AnnotatedASTNode):
        """Procesa números flotantes"""
        node.set_semantic_type(TypeInfo('float'))
        try:
            node.set_semantic_value(float(node.valor))
            node.is_constant = True
        except ValueError:
            pass
    
    def visit_booleano(self, node: AnnotatedASTNode):
        """Procesa valores booleanos"""
        node.set_semantic_type(TypeInfo('boolean'))
        node.set_semantic_value(node.valor.lower() == 'true')
        node.is_constant = True
    
    def visit_asignacion(self, node: AnnotatedASTNode):
        """Procesa asignaciones (operador =)"""
        # Verificar compatibilidad de tipos
        self.error_detector.check_type_compatibility(node)
        
        # El tipo de la asignación es el tipo del lado derecho
        if len(node.hijos) >= 2:
            right_type = self.type_system.infer_expression_type(node.hijos[1], self.symbol_table)
            if right_type:
                node.set_semantic_type(right_type)
    
    def visit_operador_aritmetico(self, node: AnnotatedASTNode):
        """Procesa operadores aritméticos (+, -, *, /, %, ^)"""
        # Verificar compatibilidad de operandos
        self.error_detector.check_type_compatibility(node)
        
        # Calcular tipo resultado
        if len(node.hijos) >= 2:
            left_type = self.type_system.infer_expression_type(node.hijos[0], self.symbol_table)
            right_type = self.type_system.infer_expression_type(node.hijos[1], self.symbol_table)
            
            if left_type and right_type:
                result_type = self.type_system.get_operation_result_type(node.tipo, left_type, right_type)
                if result_type:
                    node.set_semantic_type(result_type)
    
    def visit_operador_relacional(self, node: AnnotatedASTNode):
        """Procesa operadores relacionales (>, <, >=, <=, ==, !=)"""
        # Verificar compatibilidad de operandos
        self.error_detector.check_type_compatibility(node)
        
        # Los operadores relacionales siempre retornan boolean
        node.set_semantic_type(TypeInfo('boolean'))
    
    def visit_operador_logico(self, node: AnnotatedASTNode):
        """Procesa operadores lógicos (&&, ||)"""
        # Verificar que los operandos sean boolean
        self.error_detector.check_type_compatibility(node)
        
        # Los operadores lógicos siempre retornan boolean
        node.set_semantic_type(TypeInfo('boolean'))
    
    def visit_seleccion(self, node: AnnotatedASTNode):
        """Procesa estructuras if-then-else"""
        # Entrar a nuevo ámbito
        scope_name = f"if_{node.linea}"
        self.symbol_table.enter_scope(scope_name)
        
        # Procesar condición (debe ser boolean)
        # El procesamiento de hijos se hace automáticamente
        
        # Salir del ámbito al final del procesamiento
        # Nota: esto se manejará en el análisis principal
    
    def visit_iteracion(self, node: AnnotatedASTNode):
        """Procesa estructuras while"""
        # Entrar a nuevo ámbito
        scope_name = f"while_{node.linea}"
        self.symbol_table.enter_scope(scope_name)
        
        # El procesamiento de hijos se hace automáticamente
    
    def visit_repeticion(self, node: AnnotatedASTNode):
        """Procesa estructuras do-until"""
        # Entrar a nuevo ámbito
        scope_name = f"do_until_{node.linea}"
        self.symbol_table.enter_scope(scope_name)
        
        # El procesamiento de hijos se hace automáticamente

class SemanticAnalyzer:
    """
    Analizador semántico principal que orquesta todos los componentes
    del análisis semántico
    """
    
    def __init__(self, ast=None, tokens=None):
        """
        Inicializa el analizador semántico
        
        Args:
            ast: AST generado por el analizador sintáctico
            tokens: Lista de tokens del analizador léxico (opcional)
        """
        self.ast = ast
        self.tokens = tokens
        
        # Inicializar componentes principales
        self.symbol_table = SymbolTable()
        self.type_system = TypeSystem()
        self.error_reporter = ErrorReporter()
        self.error_detector = SemanticErrorDetector(
            self.error_reporter, self.symbol_table, self.type_system
        )
        self.visitor = SemanticVisitor(
            self.symbol_table, self.type_system, self.error_reporter
        )
        self.annotator = ASTAnnotator(self.type_system, self.symbol_table)
        
        # Resultados del análisis
        self.annotated_ast = None
        self.analysis_completed = False
    
    def analyze(self) -> Tuple[Optional[AnnotatedASTNode], SymbolTable, List[SemanticError]]:
        """
        Realiza el análisis semántico completo
        
        Returns:
            Tupla con (AST anotado, tabla de símbolos, lista de errores)
        """
        if not self.ast:
            self.error_reporter.add_error(
                'analysis_error', 
                'No hay AST disponible para análisis semántico',
                0, 0
            )
            return None, self.symbol_table, self.error_reporter.get_errors()
        
        try:
            # Fase 1: Construcción de tabla de símbolos y detección de declaraciones duplicadas
            self._build_symbol_table(self.ast)
            
            # Fase 2: Verificación de variables no declaradas
            self.error_detector.check_undeclared_variables(self.ast)
            
            # Fase 3: Verificación de compatibilidad de tipos
            self.error_detector.check_type_compatibility(self.ast)
            
            # Fase 4: Verificación de conversiones inválidas
            self.error_detector.check_invalid_conversions(self.ast)
            
            # Fase 5: Anotación del AST con información semántica
            self.annotated_ast = self.visitor.visit(self.ast)
            
            # Marcar análisis como completado
            self.analysis_completed = True
            
            return self.annotated_ast, self.symbol_table, self.error_reporter.get_errors()
            
        except Exception as e:
            self.error_reporter.add_error(
                'analysis_error',
                f'Error durante el análisis semántico: {str(e)}',
                0, 0
            )
            return None, self.symbol_table, self.error_reporter.get_errors()
    
    def _build_symbol_table(self, node):
        """
        Construye la tabla de símbolos procesando declaraciones de variables
        
        Args:
            node: Nodo del AST a procesar
        """
        if not node:
            return
        
        # Procesar declaraciones de variables
        if node.tipo == 'DECLARACION_VARIABLE':
            self.error_detector.check_duplicate_declarations(node)
        
        # Procesar estructuras de control que crean nuevos ámbitos
        elif node.tipo in ['SELECCION', 'ITERACION', 'REPETICION']:
            # Entrar a un nuevo ámbito
            scope_name = f"{node.tipo.lower()}_{node.linea}"
            self.symbol_table.enter_scope(scope_name)
            
            # Procesar hijos en el nuevo ámbito
            for hijo in node.hijos:
                self._build_symbol_table(hijo)
            
            # Salir del ámbito
            self.symbol_table.exit_scope()
        else:
            # Procesar hijos normalmente
            for hijo in node.hijos:
                self._build_symbol_table(hijo)
    
    def get_symbol_table(self) -> SymbolTable:
        """Obtiene la tabla de símbolos construida"""
        return self.symbol_table
    
    def get_errors(self) -> List[SemanticError]:
        """Obtiene la lista de errores semánticos encontrados"""
        return self.error_reporter.get_errors()
    
    def get_warnings(self) -> List[SemanticError]:
        """Obtiene la lista de advertencias encontradas"""
        return self.error_reporter.get_warnings()
    
    def has_errors(self) -> bool:
        """Verifica si se encontraron errores durante el análisis"""
        return self.error_reporter.has_errors()
    
    def has_warnings(self) -> bool:
        """Verifica si se encontraron advertencias durante el análisis"""
        return self.error_reporter.has_warnings()
    
    def get_annotated_ast(self) -> Optional[AnnotatedASTNode]:
        """Obtiene el AST anotado con información semántica"""
        return self.annotated_ast
    
    def format_results(self) -> str:
        """
        Formatea los resultados del análisis semántico para mostrar
        
        Returns:
            Cadena formateada con los resultados del análisis
        """
        if not self.analysis_completed:
            return "Análisis semántico no completado"
        
        resultado = "RESULTADOS DEL ANÁLISIS SEMÁNTICO\n"
        resultado += "=" * 60 + "\n\n"
        
        # Información general
        resultado += f"Estado del análisis: {'Completado' if self.analysis_completed else 'Incompleto'}\n"
        resultado += f"Errores encontrados: {self.error_reporter.get_error_count()}\n"
        resultado += f"Advertencias encontradas: {self.error_reporter.get_warning_count()}\n"
        resultado += f"Variables declaradas: {len(self.symbol_table.get_all_symbols())}\n\n"
        
        # Tabla de símbolos
        resultado += "TABLA DE SÍMBOLOS:\n"
        resultado += "-" * 40 + "\n"
        resultado += self.symbol_table.to_formatted_table() + "\n"
        
        # Errores y advertencias
        if self.error_reporter.has_errors() or self.error_reporter.has_warnings():
            resultado += "\nERRORES Y ADVERTENCIAS:\n"
            resultado += "-" * 40 + "\n"
            resultado += self.error_reporter.format_errors() + "\n"
        
        # Estadísticas del AST anotado
        if self.annotated_ast:
            stats = get_annotation_statistics(self.annotated_ast)
            resultado += "\nESTADÍSTICAS DEL AST ANOTADO:\n"
            resultado += "-" * 40 + "\n"
            resultado += f"Total de nodos: {stats['total_nodes']}\n"
            resultado += f"Nodos anotados: {stats['annotated_nodes']} ({stats['annotation_percentage']:.1f}%)\n"
            resultado += f"Nodos con tipo: {stats['nodes_with_type']}\n"
            resultado += f"Nodos con valor: {stats['nodes_with_value']}\n"
            resultado += f"Referencias de símbolos: {stats['nodes_with_symbol_ref']}\n"
        
        return resultado
    
    def export_results(self, base_filename: str = "semantic_analysis") -> Dict[str, bool]:
        """
        Exporta los resultados del análisis a archivos
        
        Args:
            base_filename: Nombre base para los archivos de salida
            
        Returns:
            Diccionario con el estado de cada exportación
        """
        export_status = {}
        
        try:
            # Exportar tabla de símbolos
            symbol_table_file = f"{base_filename}_symbol_table.txt"
            with open(symbol_table_file, 'w', encoding='utf-8') as f:
                f.write(self.symbol_table.to_formatted_table())
            export_status['symbol_table'] = True
        except Exception as e:
            print(f"Error exportando tabla de símbolos: {e}")
            export_status['symbol_table'] = False
        
        try:
            # Exportar errores
            errors_file = f"{base_filename}_errors.txt"
            with open(errors_file, 'w', encoding='utf-8') as f:
                f.write(self.error_reporter.format_errors())
            export_status['errors'] = True
        except Exception as e:
            print(f"Error exportando errores: {e}")
            export_status['errors'] = False
        
        try:
            # Exportar AST anotado
            if self.annotated_ast:
                ast_file = f"{base_filename}_annotated_ast.txt"
                with open(ast_file, 'w', encoding='utf-8') as f:
                    f.write(self.annotated_ast.to_formatted_string())
                export_status['annotated_ast'] = True
            else:
                export_status['annotated_ast'] = False
        except Exception as e:
            print(f"Error exportando AST anotado: {e}")
            export_status['annotated_ast'] = False
        
        try:
            # Exportar resumen completo
            summary_file = f"{base_filename}_summary.txt"
            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write(self.format_results())
            export_status['summary'] = True
        except Exception as e:
            print(f"Error exportando resumen: {e}")
            export_status['summary'] = False
        
        return export_status
    
    def reset(self):
        """Reinicia el analizador para un nuevo análisis"""
        self.symbol_table.clear()
        self.error_reporter.clear()
        self.annotated_ast = None
        self.analysis_completed = False
    
    def set_ast(self, ast):
        """Establece un nuevo AST para análisis"""
        self.ast = ast
        self.reset()
    
    def set_tokens(self, tokens):
        """Establece los tokens del análisis léxico"""
        self.tokens = tokens
    
    def get_analysis_summary(self) -> Dict[str, Any]:
        """
        Obtiene un resumen del análisis en formato diccionario
        
        Returns:
            Diccionario con información resumida del análisis
        """
        summary = {
            'analysis_completed': self.analysis_completed,
            'has_errors': self.has_errors(),
            'has_warnings': self.has_warnings(),
            'error_count': self.error_reporter.get_error_count(),
            'warning_count': self.error_reporter.get_warning_count(),
            'symbol_count': len(self.symbol_table.get_all_symbols()),
            'scopes': self.symbol_table.scopes.copy(),
            'current_scope': self.symbol_table.get_current_scope()
        }
        
        if self.annotated_ast:
            ast_stats = get_annotation_statistics(self.annotated_ast)
            summary['ast_statistics'] = ast_stats
        
        return summary
    
    def validate_analysis(self) -> Tuple[bool, List[str]]:
        """
        Valida la consistencia del análisis realizado
        
        Returns:
            Tupla con (es_válido, lista_de_problemas)
        """
        validation_errors = []
        
        # Verificar que el análisis esté completado
        if not self.analysis_completed:
            validation_errors.append("Análisis semántico no completado")
        
        # Verificar consistencia del AST anotado
        if self.annotated_ast:
            ast_errors = validate_ast_annotations(self.annotated_ast, self.symbol_table)
            validation_errors.extend(ast_errors)
        
        # Verificar que todos los símbolos referenciados existan
        for error in self.error_reporter.get_errors():
            if error.error_type == 'undeclared_variable':
                # Verificar que efectivamente no esté declarada
                var_name = error.message.split("'")[1] if "'" in error.message else ""
                if var_name and self.symbol_table.is_declared(var_name):
                    validation_errors.append(f"Inconsistencia: variable '{var_name}' reportada como no declarada pero existe en tabla de símbolos")
        
        return len(validation_errors) == 0, validation_errors
    
    def perform_comprehensive_check(self, ast_root) -> bool:
        """
        Realiza una verificación completa de errores semánticos en el AST
        
        Args:
            ast_root: Nodo raíz del AST
            
        Returns:
            True si no hay errores, False si se encontraron errores
        """
        if not ast_root:
            return True
        
        all_checks_passed = True
        
        # 1. Verificar declaraciones duplicadas y construir tabla de símbolos
        all_checks_passed &= self._process_declarations(ast_root)
        
        # 2. Verificar variables no declaradas
        all_checks_passed &= self.check_undeclared_variables(ast_root)
        
        # 3. Verificar compatibilidad de tipos
        all_checks_passed &= self.check_type_compatibility(ast_root)
        
        # 4. Verificar conversiones inválidas
        all_checks_passed &= self.check_invalid_conversions(ast_root)
        
        return all_checks_passed
    
    def _process_declarations(self, node) -> bool:
        """Procesa todas las declaraciones en el AST y verifica duplicados"""
        if not node:
            return True
        
        errors_found = False
        
        # Si es una declaración de variable, verificar duplicados
        if node.tipo == 'DECLARACION_VARIABLE':
            if not self.check_duplicate_declarations(node):
                errors_found = True
        
        # Procesar estructuras de control que crean nuevos ámbitos
        elif node.tipo in ['SELECCION', 'ITERACION', 'REPETICION']:
            # Entrar a un nuevo ámbito
            scope_name = f"{node.tipo.lower()}_{node.linea}"
            self.symbol_table.enter_scope(scope_name)
            
            # Procesar hijos en el nuevo ámbito
            for hijo in node.hijos:
                if not self._process_declarations(hijo):
                    errors_found = True
            
            # Salir del ámbito
            self.symbol_table.exit_scope()
        else:
            # Procesar hijos normalmente
            for hijo in node.hijos:
                if not self._process_declarations(hijo):
                    errors_found = True
        
        return not errors_found

# Funciones para procesamiento de archivos y integración con analizadores existentes

def process_test_file(filename: str = "TestSemantica.txt") -> Tuple[Optional[AnnotatedASTNode], SymbolTable, List[SemanticError], str]:
    """
    Procesa un archivo de prueba completo a través de todas las fases del compilador
    
    Args:
        filename: Nombre del archivo de prueba a procesar
        
    Returns:
        Tupla con (AST anotado, tabla de símbolos, errores, reporte completo)
    """
    try:
        # Importar módulos necesarios
        import lexico
        import sintactico
        
        # Leer archivo de prueba
        with open(filename, 'r', encoding='utf-8') as f:
            codigo_fuente = f.read()
        
        # Fase 1: Análisis léxico
        tokens, errores_lexicos = lexico.analizar_codigo(codigo_fuente)
        
        if errores_lexicos:
            error_msg = f"Errores léxicos encontrados: {len(errores_lexicos)}"
            return None, SymbolTable(), [SemanticError('lexical_error', error_msg, 0, 0)], error_msg
        
        # Fase 2: Análisis sintáctico
        parser = sintactico.AnalizadorSintactico(tokens)
        ast, errores_sintacticos = parser.analizar()
        
        if errores_sintacticos:
            error_msg = f"Errores sintácticos encontrados: {len(errores_sintacticos)}"
            return None, SymbolTable(), [SemanticError('syntactic_error', error_msg, 0, 0)], error_msg
        
        if not ast:
            error_msg = "No se pudo generar el AST"
            return None, SymbolTable(), [SemanticError('ast_error', error_msg, 0, 0)], error_msg
        
        # Fase 3: Análisis semántico
        semantic_analyzer = SemanticAnalyzer(ast, tokens)
        annotated_ast, symbol_table, semantic_errors = semantic_analyzer.analyze()
        
        # Generar reporte completo
        reporte = generate_complete_analysis_report(
            filename, tokens, ast, annotated_ast, symbol_table, semantic_errors
        )
        
        return annotated_ast, symbol_table, semantic_errors, reporte
        
    except FileNotFoundError:
        error_msg = f"Archivo '{filename}' no encontrado"
        return None, SymbolTable(), [SemanticError('file_error', error_msg, 0, 0)], error_msg
    except Exception as e:
        error_msg = f"Error procesando archivo: {str(e)}"
        return None, SymbolTable(), [SemanticError('processing_error', error_msg, 0, 0)], error_msg

def generate_complete_analysis_report(filename: str, tokens: List, ast, annotated_ast: Optional[AnnotatedASTNode], 
                                    symbol_table: SymbolTable, semantic_errors: List[SemanticError]) -> str:
    """
    Genera un reporte completo del análisis de todas las fases
    
    Args:
        filename: Nombre del archivo procesado
        tokens: Lista de tokens del análisis léxico
        ast: AST del análisis sintáctico
        annotated_ast: AST anotado del análisis semántico
        symbol_table: Tabla de símbolos construida
        semantic_errors: Lista de errores semánticos
        
    Returns:
        Reporte completo formateado
    """
    reporte = f"REPORTE COMPLETO DE ANÁLISIS - {filename}\n"
    reporte += "=" * 80 + "\n\n"
    
    # Información general
    reporte += "RESUMEN GENERAL:\n"
    reporte += "-" * 40 + "\n"
    reporte += f"Archivo procesado: {filename}\n"
    reporte += f"Tokens generados: {len(tokens) if tokens else 0}\n"
    reporte += f"AST generado: {'Sí' if ast else 'No'}\n"
    reporte += f"AST anotado: {'Sí' if annotated_ast else 'No'}\n"
    reporte += f"Errores semánticos: {len(semantic_errors)}\n"
    reporte += f"Variables declaradas: {len(symbol_table.get_all_symbols())}\n\n"
    
    # Tabla de símbolos
    reporte += "TABLA DE SÍMBOLOS:\n"
    reporte += "-" * 40 + "\n"
    reporte += symbol_table.to_formatted_table() + "\n"
    
    # Errores semánticos
    if semantic_errors:
        reporte += "ERRORES SEMÁNTICOS DETECTADOS:\n"
        reporte += "-" * 40 + "\n"
        error_reporter = ErrorReporter()
        for error in semantic_errors:
            error_reporter.errors.append(error)
        reporte += error_reporter.format_errors() + "\n"
    else:
        reporte += "No se encontraron errores semánticos.\n\n"
    
    # Estadísticas del AST anotado
    if annotated_ast:
        stats = get_annotation_statistics(annotated_ast)
        reporte += "ESTADÍSTICAS DEL AST ANOTADO:\n"
        reporte += "-" * 40 + "\n"
        reporte += f"Total de nodos: {stats['total_nodes']}\n"
        reporte += f"Nodos anotados: {stats['annotated_nodes']} ({stats['annotation_percentage']:.1f}%)\n"
        reporte += f"Nodos con información de tipo: {stats['nodes_with_type']}\n"
        reporte += f"Nodos con valor semántico: {stats['nodes_with_value']}\n"
        reporte += f"Referencias de símbolos: {stats['nodes_with_symbol_ref']}\n"
        reporte += f"Nodos constantes: {stats['constant_nodes']}\n"
        reporte += f"Nodos lvalue: {stats['lvalue_nodes']}\n\n"
        
        # Distribución de tipos
        if stats['types_distribution']:
            reporte += "DISTRIBUCIÓN DE TIPOS:\n"
            for tipo, count in stats['types_distribution'].items():
                reporte += f"  {tipo}: {count}\n"
            reporte += "\n"
    
    # AST anotado (versión resumida)
    if annotated_ast:
        reporte += "AST ANOTADO (ESTRUCTURA):\n"
        reporte += "-" * 40 + "\n"
        reporte += annotated_ast.to_formatted_string()[:2000]  # Limitar tamaño
        if len(annotated_ast.to_formatted_string()) > 2000:
            reporte += "\n... (truncado para brevedad)\n"
        reporte += "\n"
    
    return reporte

def save_analysis_results(filename: str, annotated_ast: Optional[AnnotatedASTNode], 
                         symbol_table: SymbolTable, semantic_errors: List[SemanticError],
                         base_output_name: str = "semantic_analysis_output") -> Dict[str, bool]:
    """
    Guarda los resultados del análisis semántico en archivos separados
    
    Args:
        filename: Nombre del archivo fuente procesado
        annotated_ast: AST anotado generado
        symbol_table: Tabla de símbolos construida
        semantic_errors: Lista de errores encontrados
        base_output_name: Nombre base para los archivos de salida
        
    Returns:
        Diccionario con el estado de cada archivo guardado
    """
    save_status = {}
    
    try:
        # Guardar tabla de símbolos
        symbol_file = f"{base_output_name}_symbol_table.txt"
        with open(symbol_file, 'w', encoding='utf-8') as f:
            f.write(f"TABLA DE SÍMBOLOS - {filename}\n")
            f.write("=" * 50 + "\n\n")
            f.write(symbol_table.to_formatted_table())
        save_status['symbol_table'] = True
    except Exception as e:
        print(f"Error guardando tabla de símbolos: {e}")
        save_status['symbol_table'] = False
    
    try:
        # Guardar errores semánticos
        errors_file = f"{base_output_name}_errors.txt"
        with open(errors_file, 'w', encoding='utf-8') as f:
            f.write(f"ERRORES SEMÁNTICOS - {filename}\n")
            f.write("=" * 50 + "\n\n")
            if semantic_errors:
                error_reporter = ErrorReporter()
                for error in semantic_errors:
                    error_reporter.errors.append(error)
                f.write(error_reporter.format_errors())
            else:
                f.write("No se encontraron errores semánticos.")
        save_status['errors'] = True
    except Exception as e:
        print(f"Error guardando errores: {e}")
        save_status['errors'] = False
    
    try:
        # Guardar AST anotado
        if annotated_ast:
            ast_file = f"{base_output_name}_annotated_ast.txt"
            with open(ast_file, 'w', encoding='utf-8') as f:
                f.write(f"AST ANOTADO - {filename}\n")
                f.write("=" * 50 + "\n\n")
                f.write(annotated_ast.to_formatted_string())
            save_status['annotated_ast'] = True
        else:
            save_status['annotated_ast'] = False
    except Exception as e:
        print(f"Error guardando AST anotado: {e}")
        save_status['annotated_ast'] = False
    
    return save_status

def analyze_test_semantica() -> str:
    """
    Función de conveniencia para analizar específicamente TestSemantica.txt
    
    Returns:
        Reporte completo del análisis
    """
    annotated_ast, symbol_table, errors, reporte = process_test_file("TestSemantica.txt")
    
    # Guardar resultados
    save_status = save_analysis_results(
        "TestSemantica.txt", annotated_ast, symbol_table, errors, "TestSemantica_results"
    )
    
    # Agregar información sobre archivos guardados
    reporte += "\nARCHIVOS GENERADOS:\n"
    reporte += "-" * 40 + "\n"
    for file_type, success in save_status.items():
        status = "✓" if success else "✗"
        reporte += f"{status} {file_type}: TestSemantica_results_{file_type}.txt\n"
    
    return reporte

def integrate_with_existing_analyzers(codigo_fuente: str) -> Tuple[Optional[AnnotatedASTNode], SymbolTable, List[SemanticError]]:
    """
    Integra el análisis semántico con los analizadores léxico y sintáctico existentes
    
    Args:
        codigo_fuente: Código fuente a analizar
        
    Returns:
        Tupla con (AST anotado, tabla de símbolos, errores semánticos)
    """
    try:
        # Importar módulos existentes
        import lexico
        import sintactico
        
        # Análisis léxico
        tokens, errores_lexicos = lexico.analizar_codigo(codigo_fuente)
        
        if errores_lexicos:
            return None, SymbolTable(), [SemanticError('lexical_error', 'Errores léxicos encontrados', 0, 0)]
        
        # Análisis sintáctico
        parser = sintactico.AnalizadorSintactico(tokens)
        ast, errores_sintacticos = parser.analizar()
        
        if errores_sintacticos or not ast:
            return None, SymbolTable(), [SemanticError('syntactic_error', 'Errores sintácticos encontrados', 0, 0)]
        
        # Análisis semántico
        semantic_analyzer = SemanticAnalyzer(ast, tokens)
        annotated_ast, symbol_table, semantic_errors = semantic_analyzer.analyze()
        
        return annotated_ast, symbol_table, semantic_errors
        
    except ImportError as e:
        error_msg = f"Error importando analizadores: {str(e)}"
        return None, SymbolTable(), [SemanticError('import_error', error_msg, 0, 0)]
    except Exception as e:
        error_msg = f"Error en integración: {str(e)}"
        return None, SymbolTable(), [SemanticError('integration_error', error_msg, 0, 0)]

def create_semantic_analysis_for_gui(codigo_fuente: str) -> Dict[str, Any]:
    """
    Crea un análisis semántico formateado para la interfaz gráfica
    
    Args:
        codigo_fuente: Código fuente a analizar
        
    Returns:
        Diccionario con resultados formateados para la GUI
    """
    try:
        # Realizar análisis completo
        annotated_ast, symbol_table, semantic_errors = integrate_with_existing_analyzers(codigo_fuente)
        
        # Formatear resultados para GUI
        gui_results = {
            'success': True,
            'annotated_ast': annotated_ast.to_formatted_string() if annotated_ast else "No se pudo generar AST anotado",
            'symbol_table': symbol_table.to_formatted_table(),
            'errors': [],
            'error_count': len(semantic_errors),
            'has_errors': len(semantic_errors) > 0
        }
        
        # Formatear errores
        if semantic_errors:
            error_reporter = ErrorReporter()
            for error in semantic_errors:
                error_reporter.errors.append(error)
            gui_results['errors'] = error_reporter.format_errors()
        else:
            gui_results['errors'] = "No se encontraron errores semánticos"
        
        return gui_results
        
    except Exception as e:
        return {
            'success': False,
            'error_message': str(e),
            'annotated_ast': "",
            'symbol_table': "",
            'errors': f"Error durante el análisis: {str(e)}",
            'error_count': 1,
            'has_errors': True
        }

def export_semantic_analysis_files(annotated_ast: Optional[AnnotatedASTNode], 
                                 symbol_table: SymbolTable, 
                                 semantic_errors: List[SemanticError],
                                 base_filename: str = "semantic_analysis") -> Dict[str, bool]:
    """
    Exporta los resultados del análisis semántico a archivos formateados
    
    Args:
        annotated_ast: AST anotado con información semántica
        symbol_table: Tabla de símbolos construida
        semantic_errors: Lista de errores semánticos encontrados
        base_filename: Nombre base para los archivos de salida
        
    Returns:
        Diccionario con el estado de cada archivo exportado
    """
    export_status = {}
    
    # 1. Exportar tabla de símbolos formateada
    try:
        symbol_table_file = f"{base_filename}_symbol_table.txt"
        with open(symbol_table_file, 'w', encoding='utf-8') as f:
            f.write("TABLA DE SÍMBOLOS - ANÁLISIS SEMÁNTICO\n")
            f.write("=" * 80 + "\n")
            f.write(f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(symbol_table.to_formatted_table())
            
            # Agregar estadísticas adicionales
            all_symbols = symbol_table.get_all_symbols()
            f.write(f"\n\nESTADÍSTICAS:\n")
            f.write("-" * 40 + "\n")
            f.write(f"Total de variables declaradas: {len(all_symbols)}\n")
            f.write(f"Ámbitos creados: {len(symbol_table.scopes)}\n")
            f.write(f"Ámbito actual: {symbol_table.get_current_scope()}\n")
            
            # Distribución por tipo
            type_distribution = {}
            for symbol in all_symbols:
                type_str = str(symbol.type_info)
                type_distribution[type_str] = type_distribution.get(type_str, 0) + 1
            
            if type_distribution:
                f.write(f"\nDISTRIBUCIÓN POR TIPO:\n")
                for tipo, count in sorted(type_distribution.items()):
                    f.write(f"  {tipo}: {count} variable(s)\n")
        
        export_status['symbol_table'] = True
    except Exception as e:
        print(f"Error exportando tabla de símbolos: {e}")
        export_status['symbol_table'] = False
    
    # 2. Exportar reporte de errores semánticos
    try:
        errors_file = f"{base_filename}_errors.txt"
        with open(errors_file, 'w', encoding='utf-8') as f:
            f.write("REPORTE DE ERRORES SEMÁNTICOS\n")
            f.write("=" * 80 + "\n")
            f.write(f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            if semantic_errors:
                # Crear reportador temporal para formatear
                error_reporter = ErrorReporter()
                for error in semantic_errors:
                    error_reporter.add_error(error.error_type, error.message, 
                                           error.line, error.column, error.severity)
                
                f.write(error_reporter.format_errors())
                
                # Agregar análisis detallado de errores
                f.write(f"\n\nANÁLISIS DETALLADO DE ERRORES:\n")
                f.write("-" * 50 + "\n")
                
                # Agrupar errores por tipo
                errors_by_type = {}
                for error in semantic_errors:
                    if error.error_type not in errors_by_type:
                        errors_by_type[error.error_type] = []
                    errors_by_type[error.error_type].append(error)
                
                for error_type, errors in errors_by_type.items():
                    f.write(f"\n{error_type.replace('_', ' ').title()}:\n")
                    for error in errors:
                        f.write(f"  - Línea {error.line}, Columna {error.column}: {error.message}\n")
            else:
                f.write("✓ No se encontraron errores semánticos\n")
                f.write("\nEl código fuente pasó todas las verificaciones semánticas:\n")
                f.write("- Variables declaradas correctamente\n")
                f.write("- Tipos compatibles en todas las operaciones\n")
                f.write("- No hay variables no declaradas\n")
                f.write("- No hay declaraciones duplicadas\n")
        
        export_status['errors'] = True
    except Exception as e:
        print(f"Error exportando errores: {e}")
        export_status['errors'] = False
    
    # 3. Exportar AST anotado
    try:
        if annotated_ast:
            ast_file = f"{base_filename}_annotated_ast.txt"
            with open(ast_file, 'w', encoding='utf-8') as f:
                f.write("AST ANOTADO CON INFORMACIÓN SEMÁNTICA\n")
                f.write("=" * 80 + "\n")
                f.write(f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                # Agregar estadísticas del AST
                stats = get_annotation_statistics(annotated_ast)
                f.write("ESTADÍSTICAS DEL AST ANOTADO:\n")
                f.write("-" * 40 + "\n")
                f.write(f"Total de nodos: {stats['total_nodes']}\n")
                f.write(f"Nodos anotados: {stats['annotated_nodes']} ({stats['annotation_percentage']:.1f}%)\n")
                f.write(f"Nodos con tipo: {stats['nodes_with_type']}\n")
                f.write(f"Nodos con valor: {stats['nodes_with_value']}\n")
                f.write(f"Referencias de símbolos: {stats['nodes_with_symbol_ref']}\n")
                f.write(f"Nodos constantes: {stats['constant_nodes']}\n")
                f.write(f"Nodos lvalue: {stats['lvalue_nodes']}\n\n")
                
                # Distribución de tipos
                if stats['types_distribution']:
                    f.write("DISTRIBUCIÓN DE TIPOS EN EL AST:\n")
                    f.write("-" * 40 + "\n")
                    for tipo, count in sorted(stats['types_distribution'].items()):
                        f.write(f"  {tipo}: {count} nodo(s)\n")
                    f.write("\n")
                
                # AST formateado
                f.write("ESTRUCTURA DEL AST ANOTADO:\n")
                f.write("-" * 40 + "\n")
                f.write(annotated_ast.to_formatted_string())
            
            export_status['annotated_ast'] = True
        else:
            export_status['annotated_ast'] = False
    except Exception as e:
        print(f"Error exportando AST anotado: {e}")
        export_status['annotated_ast'] = False
    
    # 4. Exportar AST anotado en formato JSON
    try:
        if annotated_ast:
            json_file = f"{base_filename}_annotated_ast.json"
            import json
            
            ast_dict = annotated_ast.to_annotated_dict()
            
            # Agregar metadatos
            output_data = {
                'metadata': {
                    'generated_at': datetime.now().isoformat(),
                    'generator': 'PyGFrame Semantic Analyzer',
                    'version': '1.0'
                },
                'statistics': get_annotation_statistics(annotated_ast),
                'annotated_ast': ast_dict
            }
            
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            
            export_status['annotated_ast_json'] = True
        else:
            export_status['annotated_ast_json'] = False
    except Exception as e:
        print(f"Error exportando AST anotado JSON: {e}")
        export_status['annotated_ast_json'] = False
    
    # 5. Exportar resumen completo
    try:
        summary_file = f"{base_filename}_summary.txt"
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("RESUMEN COMPLETO DEL ANÁLISIS SEMÁNTICO\n")
            f.write("=" * 80 + "\n")
            f.write(f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Información general
            f.write("INFORMACIÓN GENERAL:\n")
            f.write("-" * 40 + "\n")
            f.write(f"AST anotado generado: {'Sí' if annotated_ast else 'No'}\n")
            f.write(f"Variables declaradas: {len(symbol_table.get_all_symbols())}\n")
            f.write(f"Errores semánticos: {len(semantic_errors)}\n")
            f.write(f"Estado del análisis: {'Exitoso' if len(semantic_errors) == 0 else 'Con errores'}\n\n")
            
            # Resumen de archivos generados
            f.write("ARCHIVOS GENERADOS:\n")
            f.write("-" * 40 + "\n")
            for file_type, success in export_status.items():
                status = "✓" if success else "✗"
                f.write(f"{status} {file_type}: {base_filename}_{file_type}.txt\n")
            f.write("\n")
            
            # Tabla de símbolos resumida
            f.write("TABLA DE SÍMBOLOS (RESUMEN):\n")
            f.write("-" * 40 + "\n")
            all_symbols = symbol_table.get_all_symbols()
            if all_symbols:
                for symbol in all_symbols:
                    f.write(f"  {symbol.name} ({symbol.type_info}) - Línea {symbol.line}\n")
            else:
                f.write("  No hay variables declaradas\n")
            f.write("\n")
            
            # Errores resumidos
            if semantic_errors:
                f.write("ERRORES ENCONTRADOS (RESUMEN):\n")
                f.write("-" * 40 + "\n")
                for error in semantic_errors[:10]:  # Mostrar solo los primeros 10
                    f.write(f"  Línea {error.line}: {error.message}\n")
                if len(semantic_errors) > 10:
                    f.write(f"  ... y {len(semantic_errors) - 10} errores más\n")
            else:
                f.write("✓ No se encontraron errores semánticos\n")
        
        export_status['summary'] = True
    except Exception as e:
        print(f"Error exportando resumen: {e}")
        export_status['summary'] = False
    
    return export_status

# Función principal para testing
def main():
    """Función principal para probar el analizador semántico"""
    print("Iniciando análisis semántico de TestSemantica.txt...")
    
    try:
        reporte = analyze_test_semantica()
        print(reporte)
        
        print("\n" + "="*60)
        print("Análisis completado. Revise los archivos generados.")
        
    except Exception as e:
        print(f"Error durante el análisis: {e}")

if __name__ == "__main__":
    main()