# Archivo: semantic_ast_visualizer.py
# Visualizador especializado para mostrar el AST con anotaciones semánticas
# Incluye resaltado de errores y información de tipos

import tkinter as tk
from tkinter import ttk

class VisualizadorASTSemantico:
    def __init__(self, parent_frame, annotated_ast, semantic_errors=None):
        self.parent_frame = parent_frame
        self.annotated_ast = annotated_ast
        self.semantic_errors = semantic_errors or []
        
        # Crear diccionario de errores por línea para búsqueda rápida
        self.errors_by_line = {}
        for error in self.semantic_errors:
            line = error.line
            if line not in self.errors_by_line:
                self.errors_by_line[line] = []
            self.errors_by_line[line].append(error)
        
        self.style = ttk.Style()
        
        # Estilo para Treeview
        self.style.configure("Semantic.Treeview",
            background="#282c34",
            foreground="#abb2bf",
            fieldbackground="#282c34",
            borderwidth=0,
            font=('Consolas', 10)
        )
        self.style.map("Semantic.Treeview",
            background=[('selected', '#61afef')],
            foreground=[('selected', '#21252b')]
        )

        # Estilo para los encabezados
        self.style.configure("Semantic.Treeview.Heading",
            background="#21252b",
            foreground="#abb2bf",
            relief="flat",
            font=('Consolas', 10, 'bold')
        )
        self.style.map("Semantic.Treeview.Heading",
            background=[('active', '#282c34')]
        )

        # Estilo para los botones
        self.style.configure('Semantic.TButton',
            background='#21252b',
            foreground='#abb2bf',
            borderwidth=1,
            padding=5,
            relief='flat'
        )
        self.style.map('Semantic.TButton',
            background=[('active', '#282c34')],
            relief=[('pressed', 'solid')]
        )
        
        # Crear el frame contenedor
        self.frame = ttk.Frame(self.parent_frame)
        self.frame.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)
        
        # Panel de controles
        self.control_frame = ttk.Frame(self.frame)
        self.control_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.btn_expandir = ttk.Button(
            self.control_frame, 
            text="Expandir Todo", 
            command=self.expandir_todo,
            style='Semantic.TButton'
        )
        self.btn_expandir.pack(side=tk.LEFT, padx=2)
        
        self.btn_colapsar = ttk.Button(
            self.control_frame, 
            text="Colapsar Todo", 
            command=self.colapsar_todo,
            style='Semantic.TButton'
        )
        self.btn_colapsar.pack(side=tk.LEFT, padx=2)
        
        # Label informativo
        info_text = f"Nodos: {self._count_nodes()} | Errores: {len(self.semantic_errors)}"
        self.info_label = ttk.Label(
            self.control_frame,
            text=info_text,
            background='#282c34',
            foreground='#61afef'
        )
        self.info_label.pack(side=tk.RIGHT, padx=10)
        
        # Treeview para mostrar el AST
        self.tree_scroll = ttk.Scrollbar(self.frame)
        self.tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Scrollbar horizontal
        self.tree_h_scroll = ttk.Scrollbar(self.frame, orient=tk.HORIZONTAL)
        self.tree_h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.tree = ttk.Treeview(
            self.frame,
            yscrollcommand=self.tree_scroll.set,
            xscrollcommand=self.tree_h_scroll.set,
            selectmode='browse',
            height=20,
            style='Semantic.Treeview'
        )
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree_scroll.config(command=self.tree.yview)
        self.tree_h_scroll.config(command=self.tree.xview)
        
        # Configurar columnas
        self.tree['columns'] = ('tipo', 'valor', 'tipo_semantico', 'linea', 'columna')
        self.tree.column('#0', width=250, minwidth=150, stretch=tk.YES)
        self.tree.column('tipo', width=120, minwidth=80, stretch=tk.NO)
        self.tree.column('valor', width=120, minwidth=80, stretch=tk.NO)
        self.tree.column('tipo_semantico', width=100, minwidth=80, stretch=tk.NO)
        self.tree.column('linea', width=60, minwidth=40, stretch=tk.NO)
        self.tree.column('columna', width=60, minwidth=40, stretch=tk.NO)
        
        # Configurar encabezados
        self.tree.heading('#0', text='Estructura del AST', anchor=tk.W)
        self.tree.heading('tipo', text='Tipo Nodo', anchor=tk.W)
        self.tree.heading('valor', text='Valor', anchor=tk.W)
        self.tree.heading('tipo_semantico', text='Tipo Semántico', anchor=tk.W)
        self.tree.heading('linea', text='Línea', anchor=tk.W)
        self.tree.heading('columna', text='Columna', anchor=tk.W)
        
        # Configurar tags para colores
        #self.tree.tag_configure('error', background='#ff6b6b', foreground='#ffffff')
        #self.tree.tag_configure('warning', background='#feca57', foreground='#2d3436')
        self.tree.tag_configure('variable', foreground='#e5c07b')
        self.tree.tag_configure('operador', foreground='#61afef')
        self.tree.tag_configure('tipo', foreground='#98c379')
        self.tree.tag_configure('literal', foreground='#d19a66')
        
        # Construir el árbol visual
        self.construir_arbol()
        
        # Configurar evento para doble clic
        self.tree.bind('<Double-1>', self.toggle_nodo)
    
    def _count_nodes(self):
        """Cuenta el número total de nodos en el AST"""
        if not self.annotated_ast:
            return 0
        
        def count_recursive(node):
            count = 1
            if hasattr(node, 'hijos'):
                for hijo in node.hijos:
                    count += count_recursive(hijo)
            elif isinstance(node, dict) and 'hijos' in node:
                for hijo in node['hijos']:
                    count += count_recursive(hijo)
            return count
        
        return count_recursive(self.annotated_ast)
    
    def _get_node_info(self, node):
        """Extrae información del nodo (maneja tanto objetos como diccionarios)"""
        if hasattr(node, 'tipo'):
            # Es un objeto AnnotatedASTNode
            return {
                'tipo': node.tipo,
                'valor': node.valor if node.valor else '',
                'linea': node.linea,
                'columna': node.columna,
                'semantic_type': str(node.semantic_type) if hasattr(node, 'semantic_type') and node.semantic_type else '',
                'semantic_value': node.semantic_value if hasattr(node, 'semantic_value') else None,
                'symbol_ref': node.symbol_ref if hasattr(node, 'symbol_ref') else None,
                'hijos': node.hijos if hasattr(node, 'hijos') else [],
                'node_obj': node  # Guardar referencia al nodo original
            }
        else:
            # Es un diccionario
            semantic_attrs = node.get('semantic_attributes', {})
            return {
                'tipo': node.get('tipo', ''),
                'valor': node.get('valor', ''),
                'linea': node.get('linea', ''),
                'columna': node.get('columna', ''),
                'semantic_type': semantic_attrs.get('type', ''),
                'semantic_value': semantic_attrs.get('value', None),
                'symbol_ref': semantic_attrs.get('symbol', None),
                'hijos': node.get('hijos', []),
                'node_obj': None
            }
    
    def _get_display_value(self, info):
        """
        Obtiene el valor a mostrar en la columna 'Valor'.
        Solo muestra valores numéricos (int, float) y booleanos (true, false).
        Para operaciones, calcula el resultado. Para variables, obtiene su valor.
        """
        tipo = info['tipo']
        
        # 1. Si tiene semantic_value, usarlo (valores calculados)
        if info['semantic_value'] is not None:
            val = info['semantic_value']
            # Formatear según tipo
            if isinstance(val, bool):
                return 'true' if val else 'false'
            elif isinstance(val, (int, float)):
                return str(val)
        
        # 2. Para literales numéricos, mostrar su valor
        if tipo == 'NUM_INT':
            try:
                return str(int(info['valor']))
            except (ValueError, TypeError):
                return ''
        
        if tipo == 'NUM_FLOAT':
            try:
                return str(float(info['valor']))
            except (ValueError, TypeError):
                return ''
        
        # 3. Para booleanos, mostrar true/false
        if tipo in ['TRUE', 'FALSE', 'BOOLEANO']:
            return 'true' if info['valor'].lower() == 'true' else 'false'
        
        # 4. Para variables (ID), intentar obtener su valor desde la tabla de símbolos
        if tipo == 'ID' and info['symbol_ref']:
            # Si la variable tiene un valor conocido en tiempo de compilación, mostrarlo
            # Por ahora, esto solo funcionaría si el análisis semántico lo calculó
            if info['semantic_value'] is not None:
                val = info['semantic_value']
                if isinstance(val, bool):
                    return 'true' if val else 'false'
                elif isinstance(val, (int, float)):
                    return str(val)
        
        # 5. Para operadores aritméticos y relacionales, intentar calcular el resultado
        if tipo in ['+', '-', '*', '/', '%', '^', '>', '<', '>=', '<=', '==', '!=', '&&', '||']:
            # Si ya fue calculado en semantic_value, usarlo
            if info['semantic_value'] is not None:
                val = info['semantic_value']
                if isinstance(val, bool):
                    return 'true' if val else 'false'
                elif isinstance(val, (int, float)):
                    return str(val)
            
            # Si no, intentar calcular desde los hijos
            resultado = self._calcular_valor_operacion(info)
            if resultado is not None:
                if isinstance(resultado, bool):
                    return 'true' if resultado else 'false'
                elif isinstance(resultado, (int, float)):
                    return str(resultado)
        
        # 6. Para asignaciones (=), mostrar el valor asignado
        if tipo == '=':
            if info['semantic_value'] is not None:
                val = info['semantic_value']
                if isinstance(val, bool):
                    return 'true' if val else 'false'
                elif isinstance(val, (int, float)):
                    return str(val)
            
            # Si no, intentar calcular desde el hijo derecho
            if len(info['hijos']) >= 2:
                hijo_derecho = info['hijos'][1]
                hijo_info = self._get_node_info(hijo_derecho)
                valor_derecho = self._get_display_value(hijo_info)
                if valor_derecho:
                    return valor_derecho
        
        # Para cualquier otro caso, no mostrar valor
        return ''
    
    def _calcular_valor_operacion(self, info):
        """
        Calcula el valor de una operación aritmética o relacional.
        Retorna el resultado o None si no se puede calcular.
        """
        tipo = info['tipo']
        hijos = info['hijos']
        
        if len(hijos) < 2:
            return None
        
        # Obtener valores de los operandos
        izq_info = self._get_node_info(hijos[0])
        der_info = self._get_node_info(hijos[1])
        
        izq_valor = self._get_valor_numerico(izq_info)
        der_valor = self._get_valor_numerico(der_info)
        
        if izq_valor is None or der_valor is None:
            return None
        
        try:
            # Operadores aritméticos
            if tipo == '+':
                return izq_valor + der_valor
            elif tipo == '-':
                return izq_valor - der_valor
            elif tipo == '*':
                return izq_valor * der_valor
            elif tipo == '/':
                if der_valor != 0:
                    return izq_valor / der_valor
                return None
            elif tipo == '%':
                if der_valor != 0 and isinstance(izq_valor, int) and isinstance(der_valor, int):
                    return izq_valor % der_valor
                return None
            elif tipo == '^':
                return izq_valor ** der_valor
            
            # Operadores relacionales
            elif tipo == '>':
                return izq_valor > der_valor
            elif tipo == '<':
                return izq_valor < der_valor
            elif tipo == '>=':
                return izq_valor >= der_valor
            elif tipo == '<=':
                return izq_valor <= der_valor
            elif tipo == '==':
                return izq_valor == der_valor
            elif tipo == '!=':
                return izq_valor != der_valor
            
            # Operadores lógicos
            elif tipo == '&&':
                return bool(izq_valor) and bool(der_valor)
            elif tipo == '||':
                return bool(izq_valor) or bool(der_valor)
            
        except (ValueError, TypeError, ZeroDivisionError, OverflowError):
            return None
        
        return None
    
    def _get_valor_numerico(self, info):
        """
        Obtiene el valor numérico de un nodo para realizar cálculos.
        Retorna un número (int o float) o None si no se puede obtener.
        """
        # Si tiene semantic_value, usarlo
        if info['semantic_value'] is not None:
            return info['semantic_value']
        
        # Para literales numéricos
        if info['tipo'] == 'NUM_INT':
            try:
                return int(info['valor'])
            except (ValueError, TypeError):
                return None
        
        if info['tipo'] == 'NUM_FLOAT':
            try:
                return float(info['valor'])
            except (ValueError, TypeError):
                return None
        
        # Para booleanos (true=1, false=0)
        if info['tipo'] in ['TRUE', 'FALSE', 'BOOLEANO']:
            return 1 if info['valor'].lower() == 'true' else 0
        
        # Para operaciones, calcular recursivamente
        if info['tipo'] in ['+', '-', '*', '/', '%', '^']:
            return self._calcular_valor_operacion(info)
        
        return None
    
    def _node_has_error(self, linea):
        """Verifica si un nodo tiene errores asociados"""
        return linea in self.errors_by_line
    
    def _get_node_tag(self, tipo, linea):
        """Determina el tag/estilo para un nodo"""
        # Primero verificar si tiene error
        if self._node_has_error(linea):
            return 'error'
        
        # Asignar color según tipo de nodo
        if tipo == 'ID':
            return 'variable'
        elif tipo in ['+', '-', '*', '/', '%', '^', '=', '>', '<', '>=', '<=', '==', '!=', '&&', '||']:
            return 'operador'
        elif tipo in ['TIPO', 'INT', 'FLOAT', 'VOID', 'BOOLEAN']:
            return 'tipo'
        elif tipo in ['NUM_INT', 'NUM_FLOAT', 'TRUE', 'FALSE']:
            return 'literal'
        
        return ''
    
    def es_nodo_visible(self, tipo, valor):
        """
        Determina si un nodo debe mostrarse en el árbol visual.
        Muestra todos los nodos relevantes para análisis semántico.
        """
        # Nodos que NO queremos mostrar (muy verbosos o innecesarios)
        nodos_ocultos = {
            'LISTA_DECLARACION', 'EXPRESION_SIMPLE', 'FACTOR_SIMPLE',
            'TERMINO_SIMPLE', 'LISTA_SENTENCIA', 'SENTENCIA_SIMPLE',
            'COMPONENTE'  # Ocultar COMPONENTE - solo mostrar sus hijos
        }
        
        if tipo in nodos_ocultos:
            return False
        
        # Mostrar nodos con valor
        if valor not in [None, '']:
            return True
        
        # Mostrar nodos estructurales importantes
        nodos_estructurales = {
            'PROGRAMA', 'DECLARACION', 'DECLARACION_VAR', 'DECLARACION_VARIABLE',
            'SENTENCIA', 'ASIGNACION', 'SELECCION', 'ITERACION', 'REPETICION',
            'EXPRESION', 'EXPRESION_BINARIA', 'OPERADOR_BINARIO', 'SENT_OUT', 'SENT_IN',
            'BLOQUE', 'ELSE'
        }
        
        return tipo in nodos_estructurales
    
    def construir_arbol(self, parent='', nodo=None, nivel=0):
        """Construye recursivamente el árbol visual con información semántica"""
        if nodo is None:
            nodo = self.annotated_ast
        
        # Obtener información del nodo
        info = self._get_node_info(nodo)
        
        # Verificar si debe mostrarse
        if not self.es_nodo_visible(info['tipo'], info['valor']):
            # No mostrar este nodo, pero sí procesar sus hijos
            for hijo in info['hijos']:
                self.construir_arbol(parent, hijo, nivel)
            return
        
        # Determinar el texto a mostrar
        if info['valor']:
            texto_nodo = str(info['valor'])
        else:
            texto_nodo = info['tipo']
        
        # Agregar información semántica al texto si está disponible
        if info['semantic_type']:
            texto_nodo += f" : {info['semantic_type']}"
        
        # Determinar el tag/color del nodo
        tag = self._get_node_tag(info['tipo'], info['linea'])
        
        # Obtener el valor a mostrar (solo numéricos y booleanos)
        valor_display = self._get_display_value(info)
        
        # Preparar valores para las columnas
        valores = (
            info['tipo'],
            valor_display,  # Solo mostrar valores calculados
            info['semantic_type'] if info['semantic_type'] else '',
            str(info['linea']) if info['linea'] else '',
            str(info['columna']) if info['columna'] else ''
        )
        
        # Insertar nodo en el árbol
        if tag:
            node_id = self.tree.insert(
                parent, 'end',
                text=texto_nodo,
                values=valores,
                tags=(tag,),
                open=nivel < 2  # Expandir los primeros 2 niveles
            )
        else:
            node_id = self.tree.insert(
                parent, 'end',
                text=texto_nodo,
                values=valores,
                open=nivel < 2
            )
        
        # Procesar hijos recursivamente
        for hijo in info['hijos']:
            self.construir_arbol(node_id, hijo, nivel + 1)
    
    def toggle_nodo(self, event):
        """Alterna entre colapsar y expandir un nodo al hacer doble clic"""
        selection = self.tree.selection()
        if not selection:
            return
        
        item = selection[0]
        if self.tree.item(item, 'open'):
            self.tree.item(item, open=False)
        else:
            self.tree.item(item, open=True)
    
    def expandir_todo(self):
        """Expande todos los nodos del árbol"""
        def expandir_recursivo(item):
            self.tree.item(item, open=True)
            for child in self.tree.get_children(item):
                expandir_recursivo(child)
        
        for item in self.tree.get_children():
            expandir_recursivo(item)
    
    def colapsar_todo(self):
        """Colapsa todos los nodos del árbol"""
        def colapsar_recursivo(item):
            self.tree.item(item, open=False)
            for child in self.tree.get_children(item):
                colapsar_recursivo(child)
        
        for item in self.tree.get_children():
            colapsar_recursivo(item)
    
    def destruir(self):
        """Limpia y destruye el visualizador"""
        self.frame.destroy()


# Función auxiliar para integrar con el IDE
def crear_visualizador_semantico(parent_frame, annotated_ast, semantic_errors=None):
    """
    Función de conveniencia para crear el visualizador semántico
    
    Args:
        parent_frame: Frame padre donde se insertará el visualizador
        annotated_ast: AST anotado con información semántica
        semantic_errors: Lista de errores semánticos (opcional)
    
    Returns:
        Instancia del VisualizadorASTSemantico
    """
    return VisualizadorASTSemantico(parent_frame, annotated_ast, semantic_errors)
