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
        self.tree.tag_configure('variable', foreground='#e5c07b')
        self.tree.tag_configure('operador', foreground='#61afef')
        self.tree.tag_configure('tipo', foreground='#98c379')
        self.tree.tag_configure('literal', foreground='#d19a66')
        
        # Configurar evento para doble clic
        self.tree.bind('<Double-1>', self.toggle_nodo)
        
        # Construir el árbol visual directamente
        self.construir_arbol()
    
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
    
    def _get_display_value(self, info, es_lado_izquierdo_asignacion=False, contexto_variables=None):
        """
        Obtiene el valor a mostrar en la columna 'Valor'.
        
        REGLAS DE VISUALIZACIÓN:
        1. Literales numéricos (NUM_INT, NUM_FLOAT): mostrar su valor
        2. Booleanos (TRUE, FALSE): mostrar true/false
        3. Variables (ID):
           - Lado izquierdo de asignación: NO mostrar valor
           - Lado derecho u otros contextos: mostrar valor si está en el contexto
        4. Operadores aritméticos (+, -, *, /, %, ^): SIEMPRE mostrar resultado calculado
        5. Operadores relacionales (>, <, >=, <=, ==, !=): mostrar resultado booleano (true/false)
        6. Operadores lógicos (&&, ||): mostrar resultado booleano (true/false)
        7. Asignaciones (=): SIEMPRE mostrar el valor asignado
        
        Args:
            info: Información del nodo
            es_lado_izquierdo_asignacion: Si True, no mostrar valor (es la variable destino)
            contexto_variables: Diccionario con valores de variables calculados hasta este punto
        """
        if contexto_variables is None:
            contexto_variables = {}

        # REGLA PRIORITARIA: Si el nodo tiene un error semántico, mostrar "error"
        linea = info['linea']
        if self._node_has_error(linea):
            return 'error'
            
        tipo = info['tipo']
        
        # REGLA ESPECIAL: Variables del lado izquierdo de asignación NO muestran valor
        if es_lado_izquierdo_asignacion and tipo == 'ID':
            return ''
        
        # 1. Para literales numéricos, mostrar su valor
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
        
        # 2. Para booleanos, mostrar true/false
        if tipo in ['TRUE', 'FALSE', 'BOOLEANO']:
            return 'true' if info['valor'].lower() == 'true' else 'false'
        
        # 3. Para variables (ID), obtener su valor del contexto
        if tipo == 'ID' and not es_lado_izquierdo_asignacion:
            var_name = info['valor']
            if var_name in contexto_variables:
                val = contexto_variables[var_name]
                if isinstance(val, bool):
                    return 'true' if val else 'false'
                elif isinstance(val, (int, float)):
                    return str(val)
            return ''
        
        # 4. Para operadores relacionales, SIEMPRE calcular y mostrar resultado booleano
        if tipo in ['>', '<', '>=', '<=', '==', '!=']:
            resultado = self._calcular_valor_operacion(info, contexto_variables)
            if resultado is not None:
                return 'true' if resultado else 'false'
            return ''
        
        # 5. Para operadores lógicos, SIEMPRE calcular y mostrar resultado booleano
        if tipo in ['&&', '||']:
            resultado = self._calcular_valor_operacion(info, contexto_variables)
            if resultado is not None:
                return 'true' if resultado else 'false'
            return ''
        
        # 6. Para operadores aritméticos, SIEMPRE calcular y mostrar el resultado
        if tipo in ['+', '-', '*', '/', '%', '^']:
            resultado = self._calcular_valor_operacion(info, contexto_variables)
            if resultado is not None and isinstance(resultado, (int, float)):
                return str(resultado)
            return ''
        
        # 7. Para asignaciones (=), SIEMPRE mostrar el valor asignado
        if tipo == '=':
            if len(info['hijos']) >= 2:
                hijo_derecho = info['hijos'][1]
                hijo_der_info = self._get_node_info(hijo_derecho)
                
                # Desenvolver si es necesario (SENT_EXPRESION, COMPONENTE, etc.)
                while hijo_der_info['tipo'] in ['COMPONENTE', 'EXPRESION_SIMPLE', 'SENT_EXPRESION'] and len(hijo_der_info['hijos']) == 1:
                    hijo_derecho = hijo_der_info['hijos'][0]
                    hijo_der_info = self._get_node_info(hijo_derecho)
                
                valor = self._calcular_valor_expresion(hijo_der_info, contexto_variables)
                
                if valor is not None:
                    if isinstance(valor, bool):
                        return 'true' if valor else 'false'
                    elif isinstance(valor, (int, float)):
                        return str(valor)
            return ''
        
        # 8. Si tiene semantic_value (último recurso), usarlo
        if info['semantic_value'] is not None:
            val = info['semantic_value']
            if isinstance(val, bool):
                return 'true' if val else 'false'
            elif isinstance(val, (int, float)):
                return str(val)
        
        return ''
    
    def _calcular_valor_operacion(self, info, contexto_variables=None):
        """
        Calcula el valor de una operación aritmética, relacional o lógica.
        Retorna el resultado o None si no se puede calcular.
        
        Args:
            info: Información del nodo de operación
            contexto_variables: Diccionario con valores de variables en el contexto actual
        """
        if contexto_variables is None:
            contexto_variables = {}
            
        tipo = info['tipo']
        hijos = info['hijos']
        
        if len(hijos) < 2:
            return None
        
        # Obtener información de los operandos
        izq_info = self._get_node_info(hijos[0])
        der_info = self._get_node_info(hijos[1])
        
        # Para operadores lógicos, obtener valores booleanos
        if tipo in ['&&', '||']:
            # Calcular recursivamente los valores de los operandos
            izq_valor = self._calcular_valor_expresion(izq_info, contexto_variables)
            der_valor = self._calcular_valor_expresion(der_info, contexto_variables)
            
            # Convertir a booleano si es necesario
            if izq_valor is not None:
                if not isinstance(izq_valor, bool):
                    izq_valor = bool(izq_valor) if isinstance(izq_valor, (int, float)) else None
            
            if der_valor is not None:
                if not isinstance(der_valor, bool):
                    der_valor = bool(der_valor) if isinstance(der_valor, (int, float)) else None
            
            if izq_valor is None or der_valor is None:
                return None
            
            resultado = None
            if tipo == '&&':
                resultado = izq_valor and der_valor
            elif tipo == '||':
                resultado = izq_valor or der_valor
            
            return resultado
        
        # Para operadores relacionales, obtener valores numéricos
        if tipo in ['>', '<', '>=', '<=', '==', '!=']:
            izq_valor = self._get_valor_numerico(izq_info, contexto_variables)
            der_valor = self._get_valor_numerico(der_info, contexto_variables)
            
            if izq_valor is None or der_valor is None:
                return None
            
            try:
                resultado = None
                if tipo == '>':
                    resultado = izq_valor > der_valor
                elif tipo == '<':
                    resultado = izq_valor < der_valor
                elif tipo == '>=':
                    resultado = izq_valor >= der_valor
                elif tipo == '<=':
                    resultado = izq_valor <= der_valor
                elif tipo == '==':
                    resultado = izq_valor == der_valor
                elif tipo == '!=':
                    resultado = izq_valor != der_valor
                
                return resultado
            except (ValueError, TypeError):
                return None
        
        # Para operadores aritméticos, obtener valores numéricos
        izq_valor = self._get_valor_numerico(izq_info, contexto_variables)
        der_valor = self._get_valor_numerico(der_info, contexto_variables)
        
        if izq_valor is None or der_valor is None:
            return None
        
        # Determinar si los operandos son enteros o flotantes
        izq_es_int = isinstance(izq_valor, int) and not isinstance(izq_valor, bool)
        der_es_int = isinstance(der_valor, int) and not isinstance(der_valor, bool)
        
        try:
            # Operadores aritméticos
            if tipo == '+':
                resultado = izq_valor + der_valor
                if izq_es_int and der_es_int:
                    return int(resultado)
                return resultado
                
            elif tipo == '-':
                resultado = izq_valor - der_valor
                if izq_es_int and der_es_int:
                    return int(resultado)
                return resultado
                
            elif tipo == '*':
                resultado = izq_valor * der_valor
                if izq_es_int and der_es_int:
                    return int(resultado)
                return resultado
                
            elif tipo == '/':
                if der_valor != 0:
                    if izq_es_int and der_es_int:
                        # División entera
                        return int(izq_valor // der_valor)
                    else:
                        # División flotante
                        return izq_valor / der_valor
                return None
                
            elif tipo == '%':
                if der_valor != 0 and izq_es_int and der_es_int:
                    return int(izq_valor % der_valor)
                return None
                
            elif tipo == '^':
                resultado = izq_valor ** der_valor
                if izq_es_int and der_es_int and der_valor >= 0:
                    return int(resultado)
                return resultado
            
        except (ValueError, TypeError, ZeroDivisionError, OverflowError):
            return None
        
        return None
    
    def _calcular_valor_expresion(self, info, contexto_variables=None):
        """
        Calcula el valor de cualquier expresión (literal, variable, operación).
        Retorna el valor calculado o None.
        
        Args:
            info: Información del nodo
            contexto_variables: Diccionario con valores de variables en el contexto actual
        """
        if contexto_variables is None:
            contexto_variables = {}
            
        tipo = info['tipo']
        
        # IMPORTANTE: Desenvolver nodos COMPONENTE, SENT_EXPRESION y otros contenedores
        if tipo in ['COMPONENTE', 'EXPRESION_SIMPLE', 'FACTOR_SIMPLE', 'TERMINO_SIMPLE', 'SENT_EXPRESION'] and len(info['hijos']) == 1:
            hijo_info = self._get_node_info(info['hijos'][0])
            return self._calcular_valor_expresion(hijo_info, contexto_variables)
        
        # Literales numéricos
        if tipo == 'NUM_INT':
            try:
                resultado = int(info['valor'])
                return resultado
            except (ValueError, TypeError):
                return None
        
        if tipo == 'NUM_FLOAT':
            try:
                resultado = float(info['valor'])
                return resultado
            except (ValueError, TypeError):
                return None
        
        # Booleanos
        if tipo in ['TRUE', 'FALSE', 'BOOLEANO']:
            resultado = info['valor'].lower() == 'true'
            return resultado
        
        # Variables - buscar en el contexto
        if tipo == 'ID':
            var_name = info['valor']
            if var_name in contexto_variables:
                resultado = contexto_variables[var_name]
                return resultado
            # Si no está en el contexto, usar semantic_value si existe
            if info['semantic_value'] is not None:
                return info['semantic_value']
            return None
        
        # Operaciones relacionales - retornan booleano
        if tipo in ['>', '<', '>=', '<=', '==', '!=']:
            resultado = self._calcular_valor_operacion(info, contexto_variables)
            return resultado
        
        # Operaciones lógicas - retornan booleano
        if tipo in ['&&', '||']:
            resultado = self._calcular_valor_operacion(info, contexto_variables)
            return resultado
        
        # Operaciones aritméticas - retornan número
        if tipo in ['+', '-', '*', '/', '%', '^']:
            if info['semantic_value'] is not None:
                return info['semantic_value']
            resultado = self._calcular_valor_operacion(info, contexto_variables)
            return resultado
        
        return None
    
    def _get_valor_numerico(self, info, contexto_variables=None):
        """
        Obtiene el valor numérico de un nodo para realizar cálculos.
        Retorna un número (int o float) o None si no se puede obtener.
        IMPORTANTE: Preserva el tipo (int vs float)
        
        Args:
            info: Información del nodo
            contexto_variables: Diccionario con valores de variables en el contexto actual
        """
        if contexto_variables is None:
            contexto_variables = {}
        
        # IMPORTANTE: Desenvolver nodos COMPONENTE y otros contenedores
        if info['tipo'] in ['COMPONENTE', 'EXPRESION_SIMPLE', 'FACTOR_SIMPLE', 'TERMINO_SIMPLE', 'SENT_EXPRESION'] and len(info['hijos']) == 1:
            hijo_info = self._get_node_info(info['hijos'][0])
            return self._get_valor_numerico(hijo_info, contexto_variables)
            
        # Si tiene semantic_value, usarlo
        if info['semantic_value'] is not None:
            val = info['semantic_value']
            # Si es booleano, convertir a int (true=1, false=0)
            if isinstance(val, bool):
                resultado = 1 if val else 0
                return resultado
            return val
        
        # Para literales numéricos ENTEROS
        if info['tipo'] == 'NUM_INT':
            try:
                resultado = int(info['valor'])
                return resultado
            except (ValueError, TypeError):
                return None
        
        # Para literales numéricos FLOTANTES
        if info['tipo'] == 'NUM_FLOAT':
            try:
                resultado = float(info['valor'])
                return resultado
            except (ValueError, TypeError):
                return None
        
        # Para booleanos (true=1, false=0)
        if info['tipo'] in ['TRUE', 'FALSE', 'BOOLEANO']:
            resultado = 1 if info['valor'].lower() == 'true' else 0
            return resultado
        
        # Para variables - buscar en el contexto
        if info['tipo'] == 'ID':
            var_name = info['valor']
            if var_name in contexto_variables:
                val = contexto_variables[var_name]
                # Si es booleano, convertir a int
                if isinstance(val, bool):
                    resultado = 1 if val else 0
                    return resultado
                return val
            return None
        
        # Para operaciones, calcular recursivamente
        if info['tipo'] in ['+', '-', '*', '/', '%', '^', '>', '<', '>=', '<=', '==', '!=']:
            resultado = self._calcular_valor_operacion(info, contexto_variables)
            # Si el resultado es booleano, convertir a int para cálculos numéricos
            if isinstance(resultado, bool):
                resultado_int = 1 if resultado else 0
                return resultado_int
            return resultado
        
        return None
    
    def _get_valor_booleano(self, info, contexto_variables=None):
        """
        Obtiene el valor booleano de un nodo.
        Retorna True, False, o None si no se puede obtener.
        
        Args:
            info: Información del nodo
            contexto_variables: Diccionario con valores de variables en el contexto actual
        """
        if contexto_variables is None:
            contexto_variables = {}
        
        # Si tiene semantic_value booleano, usarlo
        if info['semantic_value'] is not None:
            if isinstance(info['semantic_value'], bool):
                return info['semantic_value']
        
        # Para literales booleanos
        if info['tipo'] in ['TRUE', 'FALSE', 'BOOLEANO']:
            return info['valor'].lower() == 'true'
        
        # Para variables - buscar en el contexto
        if info['tipo'] == 'ID':
            var_name = info['valor']
            if var_name in contexto_variables:
                val = contexto_variables[var_name]
                if isinstance(val, bool):
                    return val
                # Convertir números a booleano (0=false, !=0=true)
                if isinstance(val, (int, float)):
                    return val != 0
            return None
        
        # Para operaciones relacionales y lógicas
        if info['tipo'] in ['>', '<', '>=', '<=', '==', '!=', '&&', '||']:
            return self._calcular_valor_operacion(info, contexto_variables)
        
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
        # Nodos que NO queremos mostrar
        nodos_ocultos = {
            'LISTA_DECLARACION', 'EXPRESION_SIMPLE', 'FACTOR_SIMPLE',
            'TERMINO_SIMPLE', 'LISTA_SENTENCIA', 'SENTENCIA_SIMPLE',
            'COMPONENTE', 'SENT_EXPRESION', 'IDENTIFICADOR', 'LISTA_SENTENCIAS',
            'SALIDA'
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
    
    def construir_arbol(self, parent='', nodo=None, nivel=0, parent_info=None, contexto_variables=None):
        """Construye recursivamente el árbol visual con información semántica"""
        if nodo is None:
            nodo = self.annotated_ast
        
        if contexto_variables is None:
            contexto_variables = {}
        
        # Obtener información del nodo
        info = self._get_node_info(nodo)
        
        # DEBUG: Mostrar información del nodo y contexto
        indent = "  " * nivel
        print(f"{indent}[DEBUG] Procesando nodo: {info['tipo']} | valor={info['valor']} | Contexto actual: {contexto_variables}")
        
        # Verificar si debe mostrarse
        if not self.es_nodo_visible(info['tipo'], info['valor']):
            # No mostrar este nodo, pero sí procesar sus hijos
            print(f"{indent}[DEBUG] Nodo NO visible, procesando hijos...")
            for hijo in info['hijos']:
                contexto_variables = self.construir_arbol(parent, hijo, nivel, info, contexto_variables)
            print(f"{indent}[DEBUG] Contexto después de hijos no visibles: {contexto_variables}")
            return contexto_variables
        
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
        
        # Determinar si este nodo es el lado izquierdo de una asignación
        es_lado_izq = False
        if parent_info and parent_info['tipo'] == '=' and len(parent_info['hijos']) >= 2:
            # Desenvolver para comparar correctamente
            primer_hijo = parent_info['hijos'][0]
            primer_hijo_info = self._get_node_info(primer_hijo)
            while primer_hijo_info['tipo'] in ['COMPONENTE', 'EXPRESION_SIMPLE'] and len(primer_hijo_info['hijos']) == 1:
                primer_hijo = primer_hijo_info['hijos'][0]
                primer_hijo_info = self._get_node_info(primer_hijo)
            
            if primer_hijo == nodo or (hasattr(nodo, 'linea') and hasattr(primer_hijo, 'linea') and 
                                       nodo.linea == primer_hijo.linea and nodo.columna == primer_hijo.columna):
                es_lado_izq = True
                print(f"{indent}[DEBUG] Este nodo ES el lado izquierdo de una asignación")
        
        # Obtener el valor a mostrar CON el contexto ACTUAL
        valor_display = self._get_display_value(info, es_lado_izquierdo_asignacion=es_lado_izq, contexto_variables=contexto_variables)
        print(f"{indent}[DEBUG] Valor a mostrar: '{valor_display}'")
        
        # Preparar valores para las columnas
        valores = (
            info['tipo'],
            valor_display,
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
                open=nivel < 2
            )
        else:
            node_id = self.tree.insert(
                parent, 'end',
                text=texto_nodo,
                values=valores,
                open=nivel < 2
            )
        
        # Procesar hijos recursivamente
        print(f"{indent}[DEBUG] Procesando {len(info['hijos'])} hijos...")
        for i, hijo in enumerate(info['hijos']):
            print(f"{indent}[DEBUG] Procesando hijo {i+1}/{len(info['hijos'])}")
            contexto_variables = self.construir_arbol(node_id, hijo, nivel + 1, info, contexto_variables)
            print(f"{indent}[DEBUG] Contexto después del hijo {i+1}: {contexto_variables}")
        
        # DESPUÉS de procesar los hijos, actualizar el contexto si este nodo es una asignación
        if info['tipo'] == '=':
            print(f"{indent}[DEBUG] Este nodo es una ASIGNACIÓN, actualizando contexto...")
            if len(info['hijos']) >= 2:
                hijo_izq = info['hijos'][0]
                hijo_izq_info = self._get_node_info(hijo_izq)
                
                # Desenvolver el hijo izquierdo si es necesario
                while hijo_izq_info['tipo'] in ['COMPONENTE', 'EXPRESION_SIMPLE', 'SENT_EXPRESION'] and len(hijo_izq_info['hijos']) == 1:
                    hijo_izq = hijo_izq_info['hijos'][0]
                    hijo_izq_info = self._get_node_info(hijo_izq)
                
                print(f"{indent}[DEBUG] Hijo izquierdo: {hijo_izq_info['tipo']} = {hijo_izq_info['valor']}")
                
                if hijo_izq_info['tipo'] == 'ID':
                    var_name = hijo_izq_info['valor']
                    hijo_der = info['hijos'][1]
                    hijo_der_info = self._get_node_info(hijo_der)
                    
                    # Desenvolver el hijo derecho si es necesario
                    while hijo_der_info['tipo'] in ['COMPONENTE', 'EXPRESION_SIMPLE', 'SENT_EXPRESION'] and len(hijo_der_info['hijos']) == 1:
                        hijo_der = hijo_der_info['hijos'][0]
                        hijo_der_info = self._get_node_info(hijo_der)
                    
                    print(f"{indent}[DEBUG] Hijo derecho: {hijo_der_info['tipo']} = {hijo_der_info['valor']}")
                    print(f"{indent}[DEBUG] Calculando valor de expresión con contexto: {contexto_variables}")
                    
                    valor = self._calcular_valor_expresion(hijo_der_info, contexto_variables)
                    
                    print(f"{indent}[DEBUG] Valor calculado: {valor}")
                    
                    if valor is not None:
                        # Crear una copia del contexto para no modificar el original
                        contexto_variables = contexto_variables.copy()
                        contexto_variables[var_name] = valor
                        print(f"{indent}[DEBUG] *** Variable {var_name} asignada con valor {valor} ***")
                        print(f"{indent}[DEBUG] *** Contexto actualizado: {contexto_variables} ***")
        
        print(f"{indent}[DEBUG] Retornando contexto: {contexto_variables}")
        # Retornar el contexto actualizado para que se propague a los nodos hermanos
        return contexto_variables
    
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