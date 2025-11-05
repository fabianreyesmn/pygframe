# Archivo: sintactico.py
# Analizador Sintáctico Descendente Recursivo para el compilador PyGFrame

import json
from typing import List, Tuple, Dict, Any, Optional

class Nodo:
    """Clase que representa un nodo del Árbol Sintáctico Abstracto (AST)"""
    def __init__(self, tipo: str, valor: str = None, linea: int = 0, columna: int = 0):
        self.tipo = tipo
        self.valor = valor
        self.linea = linea
        self.columna = columna
        self.hijos = []
        self.padre = None
    
    def agregar_hijo(self, hijo):
        """Agrega un hijo al nodo"""
        if hijo:
            hijo.padre = self
            self.hijos.append(hijo)
    
    def to_dict(self):
        """Convierte el nodo a diccionario para serialización"""
        return {
            'tipo': self.tipo,
            'valor': self.valor,
            'linea': self.linea,
            'columna': self.columna,
            'hijos': [hijo.to_dict() for hijo in self.hijos]
        }

class AnalizadorSintactico:
    def __init__(self, tokens: List[Tuple]):
        self.tokens = tokens
        self.posicion = 0
        self.token_actual = None
        self.ast = None
        self.errores = []
        self.avanzar()
    
    def avanzar(self):
        """Avanza al siguiente token"""
        if self.posicion < len(self.tokens):
            self.token_actual = self.tokens[self.posicion]
            self.posicion += 1
        else:
            self.token_actual = ('EOF', '', 0, 0)
    
    def retroceder(self):
        """Retrocede al token anterior"""
        if self.posicion > 0:
            self.posicion -= 1
            self.token_actual = self.tokens[self.posicion - 1]
    
    def coincidir(self, tipo_esperado: str) -> bool:
        """Verifica si el token actual coincide con el tipo esperado"""
        if self.token_actual[0] == tipo_esperado:
            token_anterior = self.token_actual
            self.avanzar()
            return token_anterior
        return False
    
    def error(self, mensaje: str):
        """Registra un error sintáctico"""
        linea = self.token_actual[2] if len(self.token_actual) > 2 else 0
        columna = self.token_actual[3] if len(self.token_actual) > 3 else 0
        self.errores.append({
            'tipo': 'Error Sintáctico',
            'mensaje': mensaje,
            'token': self.token_actual[1] if len(self.token_actual) > 1 else '',
            'linea': linea,
            'columna': columna
        })
    
    def analizar(self):
        """Inicia el análisis sintáctico"""
        try:
            self.ast = self.programa()
            if self.token_actual[0] != 'EOF':
                self.error(f"Se esperaba fin de archivo, se encontró: {self.token_actual[1]}")
            return self.ast, self.errores
        except Exception as e:
            self.error(f"Error inesperado: {str(e)}")
            return None, self.errores
    
    # Reglas de la gramática
    
    def programa(self):
        """programa → main { lista_declaracion }"""
        nodo = Nodo('PROGRAMA')
        
        # Verificar 'main'
        if not self.coincidir('MAIN'):
            self.error("Se esperaba 'main' al inicio del programa")
            return nodo
        
        # Verificar '{'
        if not self.coincidir('SIMBOLO') or self.tokens[self.posicion-2][1] != '{':
            self.error("Se esperaba '{' después de 'main'")
        
        # Procesar lista_declaracion
        lista_decl = self.lista_declaracion()
        if lista_decl:
            nodo.agregar_hijo(lista_decl)
        
        # Verificar '}'
        if not self.coincidir('SIMBOLO') or self.tokens[self.posicion-2][1] != '}':
            self.error("Se esperaba '}' al final del programa")
        
        return nodo
    
    def lista_declaracion(self):
        """lista_declaracion → lista_declaracion declaracion | declaracion"""
        nodo = Nodo('LISTA_DECLARACION')
        
        while (self.token_actual[0] in ['TIPO', 'IF', 'WHILE', 'DO', 'CIN', 'COUT', 'ID'] and 
               self.token_actual[0] != 'EOF'):
            
            decl = self.declaracion()
            if decl:
                nodo.agregar_hijo(decl)
            
            # Si no hay más declaraciones válidas, salir
            if self.token_actual[0] not in ['TIPO', 'IF', 'WHILE', 'DO', 'CIN', 'COUT', 'ID']:
                break
        
        return nodo if nodo.hijos else None
    
    def declaracion(self):
        """declaracion → declaracion_variable | lista_sentencias"""
        if self.token_actual[0] == 'TIPO':
            return self.declaracion_variable()
        else:
            return self.sentencia()
    
    def declaracion_variable(self):
        """declaracion_variable → tipo identificador ;"""
        nodo = Nodo('DECLARACION_VARIABLE')
        
        # Tipo
        if self.token_actual[0] == 'TIPO':
            tipo_token = self.token_actual
            tipo_nodo = Nodo('TIPO', tipo_token[1], tipo_token[2], tipo_token[3])
            nodo.agregar_hijo(tipo_nodo)
            self.avanzar()
        else:
            self.error("Se esperaba un tipo de dato")
            return nodo
        
        # Identificadores
        id_nodo = self.identificador()
        if id_nodo:
            nodo.agregar_hijo(id_nodo)
        
        # Punto y coma
        if not self.coincidir('SIMBOLO') or self.tokens[self.posicion-2][1] != ';':
            self.error("Se esperaba ';' después de la declaración de variable")
        
        return nodo
    
    def identificador(self):
        """identificador → id | identificador , id"""
        nodo = Nodo('IDENTIFICADOR')
        
        if self.token_actual[0] == 'ID':
            id_token = self.token_actual
            id_nodo = Nodo('ID', id_token[1], id_token[2], id_token[3])
            nodo.agregar_hijo(id_nodo)
            self.avanzar()
            
            # Verificar si hay más identificadores separados por coma
            while (self.token_actual[0] == 'SIMBOLO' and self.token_actual[1] == ','):
                self.avanzar()  # Consumir ','
                if self.token_actual[0] == 'ID':
                    id_token = self.token_actual
                    id_nodo = Nodo('ID', id_token[1], id_token[2], id_token[3])
                    nodo.agregar_hijo(id_nodo)
                    self.avanzar()
                else:
                    self.error("Se esperaba un identificador después de ','")
                    break
        else:
            self.error("Se esperaba un identificador")
        
        return nodo
    
    def sentencia(self):
        """sentencia → seleccion | iteracion | repeticion | sent_in | sent_out | asignacion"""
        if self.token_actual[0] == 'IF':
            return self.seleccion()
        elif self.token_actual[0] == 'WHILE':
            return self.iteracion()
        elif self.token_actual[0] == 'DO':
            return self.repeticion()
        elif self.token_actual[0] == 'CIN':
            return self.sent_in()
        elif self.token_actual[0] == 'COUT':
            return self.sent_out()
        elif self.token_actual[0] == 'ID':
            siguiente = self.ver_siguiente()
            if siguiente and siguiente[0] == 'OPERADOR_ASIG_UNARIO':
                return self.incremento_unario()
            else:
                return self.asignacion()
        else:
            self.error(f"Sentencia no reconocida: {self.token_actual[1]}")
            self.avanzar()  # Intentar continuar
            return None
        
    def ver_siguiente(self):
        if self.posicion < len(self.tokens):
            return self.tokens[self.posicion]
        return None
        
    def incremento_unario(self):
        """incremento_unario → ID OPERADOR_ASIG_UNARIO ';'"""
        nodo = Nodo('INCREMENTO_UNARIO')

        if self.token_actual[0] == 'ID':
            id_token = self.token_actual
            id_nodo = Nodo('ID', id_token[1], id_token[2], id_token[3])
            nodo.agregar_hijo(id_nodo)
            self.avanzar()
        else:
            self.error("Se esperaba un identificador antes de '++' o '--'")
            return nodo

        if self.token_actual[0] == 'OPERADOR_ASIG_UNARIO':
            op_token = self.token_actual
            op_nodo = Nodo('OPERADOR_ASIG_UNARIO', op_token[1], op_token[2], op_token[3])
            nodo.agregar_hijo(op_nodo)
            self.avanzar()
        else:
            self.error("Se esperaba '++' o '--' después del identificador")
            return nodo

        if not self.coincidir('SIMBOLO') or self.tokens[self.posicion - 2][1] != ';':
            self.error("Se esperaba ';' al final del incremento o decremento")

        return nodo
    
    def es_operador_asignacion(self, token_tipo, token_valor):
        """Verifica si el token es un operador de asignación válido"""
        if token_tipo == 'ASIGNACION' and token_valor == '=':
            return True
        elif token_tipo == 'OPERADOR_ASIGNACION' and token_valor in ['+=', '-=', '*=', '/=', '%=', '^=']:
            return True
        return False
    
    def asignacion(self):
        """asignacion → id = sent_expresion"""
        if self.token_actual[0] == 'ID':
            id_token = self.token_actual
            id_nodo = Nodo('ID', id_token[1], id_token[2], id_token[3])
            self.avanzar()
        else:
            self.error("Se esperaba un identificador en la asignación")
            return Nodo('ASIGNACION')

        if not self.coincidir('ASIGNACION'):
            self.error("Se esperaba '=' en la asignación")

        expr = self.sent_expresion()
        if not expr:
            self.error("Expresión inválida en la asignación")
            return Nodo('ASIGNACION')

        nodo = Nodo('=', '=', id_token[2], id_token[3])
        nodo.agregar_hijo(id_nodo)
        nodo.agregar_hijo(expr)
        return nodo
    
    def sent_expresion(self):
        """sent_expresion → expresion ; | ;"""
        nodo = Nodo('SENT_EXPRESION')
        
        # Verificar si es solo punto y coma
        if self.token_actual[0] == 'SIMBOLO' and self.token_actual[1] == ';':
            self.avanzar()
            return nodo
        
        # Procesar expresión
        expr = self.expresion()
        if expr:
            nodo.agregar_hijo(expr)
        
        # Punto y coma
        if not self.coincidir('SIMBOLO') or self.tokens[self.posicion-2][1] != ';':
            self.error("Se esperaba ';' al final de la expresión")
        
        return nodo
    
    def seleccion(self):
        """seleccion → if expresion then lista_sentencias [ else lista_sentencias ] end"""
        nodo = Nodo('SELECCION')
        
        # 'if'
        if self.token_actual[0] == 'IF':
            self.avanzar()
        else:
            self.error("Se esperaba 'if'")
            return nodo
        
        # Expresión
        expr = self.expresion()
        if expr:
            nodo.agregar_hijo(expr)
        
        # 'then'
        if not self.coincidir('THEN'):
            self.error("Se esperaba 'then'")
            return nodo
        
        # Lista de sentencias del if
        lista_sent = self.lista_sentencias()
        if lista_sent:
            nodo.agregar_hijo(lista_sent)
        
        # Verificar 'else' opcional
        if self.token_actual[0] == 'ELSE':
            else_nodo = Nodo('ELSE')
            nodo.agregar_hijo(else_nodo)
            self.avanzar()
            
            lista_sent_else = self.lista_sentencias()
            if lista_sent_else:
                else_nodo.agregar_hijo(lista_sent_else)
        
        # 'end'
        if not self.coincidir('END'):
            self.error("Se esperaba 'end' al final de la estructura if")
        
        return nodo
    
    def iteracion(self):
        """iteracion → while expresion lista_sentencias end"""
        nodo = Nodo('ITERACION')
        
        # 'while'
        if self.token_actual[0] == 'WHILE':
            self.avanzar()
        else:
            self.error("Se esperaba 'while'")
            return nodo
        
        # Expresión
        expr = self.expresion()
        if expr:
            nodo.agregar_hijo(expr)
        
        # Lista de sentencias
        lista_sent = self.lista_sentencias()
        if lista_sent:
            nodo.agregar_hijo(lista_sent)
        
        # 'end'
        if not self.coincidir('END'):
            self.error("Se esperaba 'end' al final del while")
        
        return nodo
    
    def repeticion(self):
        """repeticion → do lista_sentencias while expresion"""
        nodo = Nodo('REPETICION')
        
        # 'do'
        if self.token_actual[0] == 'DO':
            self.avanzar()
        else:
            self.error("Se esperaba 'do'")
            return nodo
        
        # Lista de sentencias
        lista_sent = self.lista_sentencias()
        if lista_sent:
            nodo.agregar_hijo(lista_sent)
        
        # 'until'
        if not self.coincidir('UNTIL'):
            self.error("Se esperaba 'until' en la estructura do-until")
        
        # Expresión
        expr = self.expresion()
        if expr:
            nodo.agregar_hijo(expr)
        
        return nodo
    
    def lista_sentencias(self):
        """lista_sentencias → lista_sentencias sentencia | ε"""
        nodo = Nodo('LISTA_SENTENCIAS')
        
        while (self.token_actual[0] in ['IF', 'WHILE', 'DO', 'CIN', 'COUT', 'ID'] and 
               self.token_actual[0] != 'EOF'):
            
            sent = self.sentencia()
            if sent:
                nodo.agregar_hijo(sent)
            else:
                break
        
        return nodo if nodo.hijos else None
    
    def sent_in(self):
        """sent_in → cin >> id ;"""
        nodo = Nodo('SENT_IN')
        
        # 'cin'
        if self.token_actual[0] == 'CIN':
            self.avanzar()
        else:
            self.error("Se esperaba 'cin'")
            return nodo
        
        # '>>'
        if not (self.token_actual[0] == 'OPERADOR_ENTRADA' and self.token_actual[1] == '>>'):
            self.error("Se esperaba '>>' después de 'cin'")
        else:
            self.avanzar()
        
        # Identificador
        if self.token_actual[0] == 'ID':
            id_token = self.token_actual
            id_nodo = Nodo('ID', id_token[1], id_token[2], id_token[3])
            nodo.agregar_hijo(id_nodo)
            self.avanzar()
        else:
            self.error("Se esperaba un identificador después de '>>'")
        
        # Punto y coma
        if not self.coincidir('SIMBOLO') or self.tokens[self.posicion-2][1] != ';':
            self.error("Se esperaba ';' al final de la sentencia cin")
        
        return nodo
    
    def sent_out(self):
        """sent_out → cout << salida"""
        nodo = Nodo('SENT_OUT')
        
        # 'cout'
        if self.token_actual[0] == 'COUT':
            self.avanzar()
        else:
            self.error("Se esperaba 'cout'")
            return nodo
        
        # '<<'
        if not (self.token_actual[0] == 'OPERADOR_SALIDA' and self.token_actual[1] == '<<'):
            self.error("Se esperaba '<<' después de 'cout'")
        else:
            self.avanzar()
        
        # Salida
        salida = self.salida()
        if salida:
            nodo.agregar_hijo(salida)

        # Punto y coma
        if not self.coincidir('SIMBOLO') or self.tokens[self.posicion - 2][1] != ';':
            self.error("Se esperaba ';' al final de la sentencia cout")
        
        return nodo
    
    def salida(self):
        """salida → cadena | expresion | cadena << expresion | expresion << cadena"""
        nodo = Nodo('SALIDA')
        
        # Verificar si es una cadena
        if self.token_actual[0] == 'CADENA':
            cadena_token = self.token_actual
            cadena_nodo = Nodo('CADENA', cadena_token[1], cadena_token[2], cadena_token[3])
            nodo.agregar_hijo(cadena_nodo)
            self.avanzar()
        else:
            # Es una expresión
            expr = self.expresion()
            if expr:
                nodo.agregar_hijo(expr)
        
        return nodo

    def expresion(self):
        """expresion → expresion_logica"""
        return self.expresion_logica()
    
    def expresion_logica(self):
        izquierda = self.expresion_relacional()

        while self.token_actual[0] == 'OPERADOR_LOGICO':
            op_token = self.token_actual
            self.avanzar()
            derecha = self.expresion_relacional()

            nodo = Nodo(op_token[1], op_token[1], op_token[2], op_token[3])  # tipo y valor = '&&', '||'
            nodo.agregar_hijo(izquierda)
            nodo.agregar_hijo(derecha)
            izquierda = nodo

        return izquierda
    
    def expresion_relacional(self):
        izquierda = self.expresion_simple()

        if self.token_actual[0] == 'OPERADOR_RELACIONAL':
            op_token = self.token_actual
            self.avanzar()
            derecha = self.expresion_simple()

            nodo = Nodo(op_token[1], op_token[1], op_token[2], op_token[3])  # tipo = '>', valor = '>'
            nodo.agregar_hijo(izquierda)
            nodo.agregar_hijo(derecha)
            return nodo

        return izquierda
    
    def expresion_simple(self):
        izquierda = self.termino()

        while self.token_actual[0] == 'OPERADOR_ARITMETICO' and self.token_actual[1] in ['+', '-', '++', '--']:
            op_token = self.token_actual
            self.avanzar()
            derecha = self.termino()

            nodo = Nodo(op_token[1], op_token[1], op_token[2], op_token[3])  # Ej: tipo = '+'
            nodo.agregar_hijo(izquierda)
            nodo.agregar_hijo(derecha)
            izquierda = nodo

        return izquierda
    
    def termino(self):
        izquierda = self.factor()

        while self.token_actual[0] == 'OPERADOR_ARITMETICO' and self.token_actual[1] in ['*', '/', '%']:
            op_token = self.token_actual
            self.avanzar()
            derecha = self.factor()

            nodo = Nodo(op_token[1], op_token[1], op_token[2], op_token[3])
            nodo.agregar_hijo(izquierda)
            nodo.agregar_hijo(derecha)
            izquierda = nodo

        return izquierda
    
    def factor(self):
        izquierda = self.componente()

        while self.token_actual[0] == 'OPERADOR_ARITMETICO' and self.token_actual[1] == '^':
            op_token = self.token_actual
            self.avanzar()
            derecha = self.componente()

            nodo = Nodo('^', '^', op_token[2], op_token[3])
            nodo.agregar_hijo(izquierda)
            nodo.agregar_hijo(derecha)
            izquierda = nodo

        return izquierda
    
    def componente(self):
        """componente → ( expresion ) | número | id | bool | op_logico componente"""
        nodo = Nodo('COMPONENTE')
        
        if self.token_actual[0] == 'SIMBOLO' and self.token_actual[1] == '(':
            self.avanzar()  # Consumir '('
            expr = self.expresion()
            if expr:
                nodo.agregar_hijo(expr)
            
            if not self.coincidir('SIMBOLO') or self.tokens[self.posicion-2][1] != ')':
                self.error("Se esperaba ')' para cerrar la expresión")
        
        elif self.token_actual[0] in ['NUM_INT', 'NUM_FLOAT']:
            num_token = self.token_actual
            num_nodo = Nodo(num_token[0], num_token[1], num_token[2], num_token[3])
            nodo.agregar_hijo(num_nodo)
            self.avanzar()
        
        elif self.token_actual[0] == 'ID':
            id_token = self.token_actual
            id_nodo = Nodo('ID', id_token[1], id_token[2], id_token[3])
            nodo.agregar_hijo(id_nodo)
            self.avanzar()

        elif self.token_actual[0] in ['TRUE', 'FALSE']:
            bool_token = self.token_actual
            bool_nodo = Nodo('BOOLEANO', bool_token[1], bool_token[2], bool_token[3])
            nodo.agregar_hijo(bool_nodo)
            self.avanzar()
        
        elif self.token_actual[0] == 'OPERADOR_LOGICO':
            op_token = self.token_actual
            op_nodo = Nodo('OPERADOR_LOGICO', op_token[1], op_token[2], op_token[3])
            nodo.agregar_hijo(op_nodo)
            self.avanzar()
            
            # Procesar componente después del operador lógico
            comp = self.componente()
            if comp:
                nodo.agregar_hijo(comp)
        
        else:
            self.error(f"Componente no reconocido: {self.token_actual[1]}")
        
        return nodo


# Función principal para analizar desde archivo de tokens
def analizar_desde_archivo(archivo_tokens):
    """Analiza tokens desde un archivo y retorna el AST y errores"""
    try:
        with open(archivo_tokens, 'r', encoding='utf-8') as f:
            contenido = f.read().strip()
            
        # Parsear tokens del archivo (formato: TIPO VALOR LINEA COLUMNA)
        tokens = []
        for linea in contenido.split('\n'):
            if linea.strip():
                partes = linea.strip().split()
                if len(partes) >= 4:
                    tipo = partes[0]
                    valor = ' '.join(partes[1:-2])  # El valor puede contener espacios
                    linea_num = int(partes[-2])
                    columna_num = int(partes[-1])
                    tokens.append((tipo, valor, linea_num, columna_num))
        
        # Realizar análisis sintáctico
        analizador = AnalizadorSintactico(tokens)
        ast, errores = analizador.analizar()
        
        return ast, errores, tokens
        
    except Exception as e:
        return None, [{'tipo': 'Error', 'mensaje': f'Error al leer archivo: {str(e)}', 'linea': 0, 'columna': 0}], []

def analizar_desde_tokens(tokens):
    """Analiza una lista de tokens directamente"""
    analizador = AnalizadorSintactico(tokens)
    return analizador.analizar()

def formatear_errores(errores):
    """Formatea los errores para mostrar en el IDE"""
    if not errores:
        return "No se encontraron errores sintácticos"
    
    resultado = "ERRORES SINTÁCTICOS:\n"
    resultado += "-" * 80 + "\n"
    resultado += "| {:<15} | {:<40} | {:<8} | {:<8} |\n".format("TIPO", "DESCRIPCIÓN", "LÍNEA", "COLUMNA")
    resultado += "-" * 80 + "\n"
    
    for error in errores:
        resultado += "| {:<15} | {:<40} | {:<8} | {:<8} |\n".format(
            error.get('tipo', 'Error'),
            error.get('mensaje', '')[:40],
            error.get('linea', 0),
            error.get('columna', 0)
        )
    
    return resultado

def guardar_ast_json(ast, archivo_salida):
    """Guarda el AST en formato JSON"""
    if ast:
        with open(archivo_salida, 'w', encoding='utf-8') as f:
            json.dump(ast.to_dict(), f, indent=2, ensure_ascii=False)