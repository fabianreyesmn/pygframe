# Archivo: ast_visualizer.py
# Visualizador de AST integrado en el IDE con capacidad de colapsar/expandir nodos
# y variables anidadas dentro de sus tipos de datos

import tkinter as tk
from tkinter import ttk
import json

class VisualizadorAST:
    def __init__(self, parent_frame, ast):
        self.parent_frame = parent_frame
        self.ast = ast
        
        self.style = ttk.Style()
        
        # Estilo para Treeview
        self.style.configure("Treeview",
            background="#282c34",
            foreground="#abb2bf",
            fieldbackground="#282c34",
            borderwidth=0
        )
        self.style.map("Treeview",
            background=[('selected', '#61afef')],
            foreground=[('selected', '#21252b')]
        )

        # Estilo para los encabezados del Treeview
        self.style.configure("Treeview.Heading",
            background="#21252b",
            foreground="#abb2bf",
            relief="flat"
        )
        self.style.map("Treeview.Heading",
            background=[('active', '#282c34')]
        )

        # Estilo para los botones
        self.style.configure('AST.TButton',
            background='#21252b',
            foreground='#abb2bf',
            borderwidth=1,
            padding=5,
            relief='flat'
        )
        self.style.map('AST.TButton',
            background=[('active', '#282c34')],
            relief=[('pressed', 'solid')]
        )
        
        # Crear el frame contenedor
        self.frame = ttk.Frame(self.parent_frame)
        self.frame.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)
        
        # Panel de controles (botones)
        self.control_frame = ttk.Frame(self.frame)
        self.control_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.btn_expandir = ttk.Button(
            self.control_frame, 
            text="Expandir Todo", 
            command=self.expandir_todo,
            style='AST.TButton'
        )
        self.btn_expandir.pack(side=tk.LEFT, padx=2)
        
        self.btn_colapsar = ttk.Button(
            self.control_frame, 
            text="Colapsar Todo", 
            command=self.colapsar_todo,
            style='AST.TButton'
        )
        self.btn_colapsar.pack(side=tk.LEFT, padx=2)
        
        # Treeview para mostrar el AST
        self.tree_scroll = ttk.Scrollbar(self.frame)
        self.tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.tree = ttk.Treeview(
            self.frame,
            yscrollcommand=self.tree_scroll.set,
            selectmode='browse',
            height=15
        )
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree_scroll.config(command=self.tree.yview)
        
        # Configurar columnas
        self.tree['columns'] = ('tipo', 'valor', 'linea', 'columna')
        self.tree.column('#0', width=200, minwidth=100, stretch=tk.YES)
        self.tree.column('tipo', width=100, minwidth=50, stretch=tk.NO)
        self.tree.column('valor', width=150, minwidth=50, stretch=tk.NO)
        self.tree.column('linea', width=50, minwidth=30, stretch=tk.NO)
        self.tree.column('columna', width=50, minwidth=30, stretch=tk.NO)
        
        # Configurar encabezados
        self.tree.heading('#0', text='Estructura del AST', anchor=tk.W)
        self.tree.heading('tipo', text='Tipo', anchor=tk.W)
        self.tree.heading('valor', text='Valor', anchor=tk.W)
        self.tree.heading('linea', text='Línea', anchor=tk.W)
        self.tree.heading('columna', text='Columna', anchor=tk.W)
        
        # Construir el árbol visual
        self.construir_arbol()
        
        # Configurar evento para colapsar/expandir
        self.tree.bind('<Double-1>', self.toggle_nodo)
    
    def es_nodo_visible(self, tipo, valor):
        """
        Determina si un nodo del AST debe mostrarse en el árbol visual.
        Ahora se muestran nodos estructurales importantes y terminales.
        """
        # Nodos que NO queremos mostrar (demasiado verbosos o redundantes)
        nodos_ocultos = {
            'LISTA_DECLARACION', 'EXPRESION_SIMPLE', 'FACTOR_SIMPLE',
            'TERMINO_SIMPLE', 'LISTA_SENTENCIA', 'SENTENCIA_SIMPLE',
            'DECLARACION_VARIABLE'
        }
        
        # Si es un nodo oculto, no mostrarlo
        if tipo in nodos_ocultos:
            return False
        
        # Siempre mostrar nodos con valor (tokens terminales)
        if valor not in [None, '']:
            return True
        
        # Nodos estructurales importantes que sí queremos mostrar
        nodos_estructurales_importantes = {
            'PROGRAMA', 'DECLARACION', 'DECLARACION_VAR', 'DECLARACION_FUNCION',
            'SENTENCIA', 'SENTENCIA_ASIGNACION', 'SENTENCIA_IF', 'SENTENCIA_WHILE',
            'SENTENCIA_FOR', 'SENTENCIA_RETURN', 'SENTENCIA_ENTRADA', 'SENTENCIA_SALIDA',
            'EXPRESION', 'EXPRESION_BINARIA', 'EXPRESION_UNARIA', 'LLAMADA_FUNCION',
            'BLOQUE', 'PARAMETROS', 'ARGUMENTOS', 'TIPO_DATO', 'SENT_OUT', 'SENT_IN',
            'OPERADOR_BINARIO', 'ASIGNACION', 'DECLARACION_VARIABLE', 'SELECCION',
            'ELSE', 'ITERACION', 'REPETICION'
        }
        
        # Mostrar si es un nodo estructural importante
        if tipo in nodos_estructurales_importantes:
            return True
        
        # Tokens importantes (operadores, palabras clave, etc.)
        tokens_importantes = {
            '+', '-', '*', '/', '%', '^', '=', '==', '!=', '<', '>', '<=', '>=',
            '&&', '||', '!', 'if', 'else', 'while', 'do', 'end', 'cin', 'cout', 'main',
            'return', 'switch', 'case', 'for', 'int', 'float', '<<', '>>', '++', '--',
            'ID', 'NUM_INT'
        }
        
        return tipo in tokens_importantes
    
    def agrupar_variables_por_tipo(self, nodo):
        """
        Reorganiza el AST para agrupar variables bajo sus tipos de datos.
        Busca patrones de declaración de variables y las anida bajo el tipo.
        """
        tipo = nodo.get('tipo')
        valor = nodo.get('valor')
        hijos = nodo.get('hijos', [])
        
        # Si es una declaración de variable, reorganizar
        if tipo == 'DECLARACION_VARIABLE':
            # Buscar el tipo de dato y las variables
            tipo_dato = None
            variables = []
            otros_hijos = []
            
            for hijo in hijos:
                if hijo.get('valor') in ['int', 'float'] or hijo.get('tipo') == 'TIPO_DATO':
                    tipo_dato = hijo
                elif hijo.get('tipo') == 'ID' or (hijo.get('tipo') == 'IDENTIFICADOR' and hijo.get('valor')):
                    variables.append(hijo)
                else:
                    # Buscar variables anidadas en estructuras más complejas
                    variables_encontradas = self.buscar_variables_en_nodo(hijo)
                    if variables_encontradas:
                        variables.extend(variables_encontradas)
                    else:
                        otros_hijos.append(hijo)
            
            # Si encontramos tipo de dato y variables, reorganizar
            if tipo_dato and variables:
                # Crear nuevo nodo del tipo de dato con variables como hijos
                nuevo_tipo_dato = {
                    'tipo': tipo_dato.get('tipo', 'TIPO_DATO'),
                    'valor': tipo_dato.get('valor'),
                    'linea': tipo_dato.get('linea', ''),
                    'columna': tipo_dato.get('columna', ''),
                    'hijos': variables  # Las variables se convierten en hijos del tipo
                }
                
                # Crear el nodo reorganizado
                nodo_reorganizado = {
                    'tipo': tipo,
                    'valor': valor,
                    'linea': nodo.get('linea', ''),
                    'columna': nodo.get('columna', ''),
                    'hijos': [nuevo_tipo_dato] + otros_hijos
                }
                
                return nodo_reorganizado
        
        # Si no es una declaración de variable, procesar hijos recursivamente
        hijos_procesados = []
        for hijo in hijos:
            hijo_procesado = self.agrupar_variables_por_tipo(hijo)
            hijos_procesados.append(hijo_procesado)
        
        # Retornar nodo con hijos procesados
        nodo_procesado = nodo.copy()
        nodo_procesado['hijos'] = hijos_procesados
        return nodo_procesado
    
    def buscar_variables_en_nodo(self, nodo):
        """
        Busca variables (IDs) recursivamente en un nodo y sus hijos.
        """
        variables = []
        
        # Si el nodo actual es una variable, agregarlo
        if nodo.get('tipo') == 'ID' and nodo.get('valor'):
            variables.append(nodo)
        
        # Buscar en los hijos
        for hijo in nodo.get('hijos', []):
            variables.extend(self.buscar_variables_en_nodo(hijo))
        
        return variables
    
    def expandir_incremento_decremento(self, nodo, contexto_padre=None):
        """
        Detecta operadores ++ y -- y los expande a su forma de asignación completa
        Retorna un nodo modificado o el nodo original si no hay cambios
        """
        tipo = nodo.get('tipo')
        valor = nodo.get('valor')
        hijos = nodo.get('hijos', [])
        
        # Detectar operadores de incremento/decremento
        if valor == '++' or valor == '--':
            variable_nombre = self.encontrar_variable_para_incremento(nodo, contexto_padre)
            
            # Determinar el operador resultante
            if valor == '++':
                operador_expandido = '+'
            else:  # valor == '--'
                operador_expandido = '-'
            
            # Crear el nodo expandido como asignación:
            # =
            # ├─ variable
            # └─ +/-
            #     ├─ variable
            #     └─ 1
            nodo_expandido = {
                'tipo': 'ASIGNACION',
                'valor': '=',
                'linea': nodo.get('linea', ''),
                'columna': nodo.get('columna', ''),
                'hijos': [
                    # Variable del lado izquierdo (a la que se asigna)
                    {
                        'tipo': 'ID',
                        'valor': variable_nombre,
                        'linea': nodo.get('linea', ''),
                        'columna': nodo.get('columna', ''),
                        'hijos': []
                    },
                    # Operación del lado derecho (variable + 1 o variable - 1)
                    {
                        'tipo': 'OPERADOR_BINARIO',
                        'valor': operador_expandido,
                        'linea': nodo.get('linea', ''),
                        'columna': nodo.get('columna', ''),
                        'hijos': [
                            # Variable (operando izquierdo)
                            {
                                'tipo': 'ID',
                                'valor': variable_nombre,
                                'linea': nodo.get('linea', ''),
                                'columna': nodo.get('columna', ''),
                                'hijos': []
                            },
                            # Número 1 (operando derecho)
                            {
                                'tipo': 'NUM_INT',
                                'valor': '1',
                                'linea': nodo.get('linea', ''),
                                'columna': nodo.get('columna', ''),
                                'hijos': []
                            }
                        ]
                    }
                ]
            }
            
            return nodo_expandido
        
        # Si no es un operador de incremento/decremento, retornar el nodo original
        return nodo
    
    def encontrar_variable_para_incremento(self, nodo_incremento, contexto_padre):
        """
        Busca exhaustivamente la variable asociada con un operador ++ o --
        """
        # Estrategias de búsqueda en orden de prioridad:
        
        # 1. Buscar en los hijos del nodo actual
        for hijo in nodo_incremento.get('hijos', []):
            if hijo.get('tipo') in ['ID', 'IDENTIFICADOR', 'VARIABLE'] and hijo.get('valor'):
                return hijo.get('valor')
        
        # 2. Si tenemos contexto padre, buscar en los hermanos
        if contexto_padre:
            for hermano in contexto_padre.get('hijos', []):
                if hermano != nodo_incremento and hermano.get('tipo') in ['ID', 'IDENTIFICADOR', 'VARIABLE'] and hermano.get('valor'):
                    return hermano.get('valor')
        
        # 3. Buscar en el contexto padre si es una expresión unaria
        if contexto_padre and contexto_padre.get('tipo') in ['EXPRESION_UNARIA', 'POSTFIX', 'PREFIX']:
            for hijo in contexto_padre.get('hijos', []):
                if hijo != nodo_incremento and hijo.get('tipo') in ['ID', 'IDENTIFICADOR', 'VARIABLE'] and hijo.get('valor'):
                    return hijo.get('valor')
        
        # 4. Si no encontramos nada, retornar un valor por defecto
        # (Esto debería ser raro si el AST está bien formado)
        return "variable_no_encontrada"
    
    def construir_arbol(self, parent='', nodo=None, contexto_padre=None):
        """Construye recursivamente el árbol visual a partir del AST"""
        if nodo is None:
            if isinstance(self.ast, dict):
                nodo = self.ast
            else:
                nodo = self.ast.to_dict() if hasattr(self.ast, 'to_dict') else {}
        
        # Primero agrupar variables por tipo
        nodo = self.agrupar_variables_por_tipo(nodo)
        
        # Expandir operadores de incremento/decremento antes de procesar
        nodo = self.expandir_incremento_decremento(nodo, contexto_padre)
        
        valor = nodo.get('valor')
        tipo = nodo.get('tipo')
        
        # Verificar si este nodo debe mostrarse
        if not self.es_nodo_visible(tipo, valor):
            # No mostrar este nodo, pero sí procesar sus hijos
            for hijo in nodo.get('hijos', []):
                self.construir_arbol(parent, hijo, nodo)
            return
        
        # Determinar el texto a mostrar en el nodo
        if valor not in [None, '']:
            # Para tipos de datos con variables anidadas, mostrar información adicional
            if valor in ['int', 'float'] and nodo.get('hijos'):
                num_variables = len([h for h in nodo.get('hijos', []) if h.get('tipo') == 'ID'])
                if num_variables > 0:
                    texto_nodo = f"{valor}"
                else:
                    texto_nodo = str(valor)
            else:
                texto_nodo = str(valor)
        else:
            # Para nodos estructurales, usar el tipo como texto
            texto_nodo = str(tipo)
        
        # Crear el nodo en el árbol visual
        node_id = self.tree.insert(
            parent, 'end', 
            text=texto_nodo,
            values=(
                tipo,
                str(valor) if valor not in [None, ''] else '',
                nodo.get('linea', ''),
                nodo.get('columna', '')
            ),
            open=True
        )
        
        # Procesar hijos recursivamente, pasando el nodo actual como contexto
        for hijo in nodo.get('hijos', []):
            self.construir_arbol(node_id, hijo, nodo)
    
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
        for item in self.tree.get_children():
            self.expandir_recursivo(item)
    
    def expandir_recursivo(self, item):
        """Función auxiliar para expandir nodos recursivamente"""
        self.tree.item(item, open=True)
        for child in self.tree.get_children(item):
            self.expandir_recursivo(child)
    
    def colapsar_todo(self):
        """Colapsa todos los nodos del árbol"""
        for item in self.tree.get_children():
            self.colapsar_recursivo(item)
    
    def colapsar_recursivo(self, item):
        """Función auxiliar para colapsar nodos recursivamente"""
        self.tree.item(item, open=False)
        for child in self.tree.get_children(item):
            self.colapsar_recursivo(child)

    def destruir(self):
        """Limpia y destruye el visualizador"""
        self.frame.destroy()