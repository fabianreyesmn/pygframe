# Archivo: lexico.py
# Este archivo contiene el analizador léxico actualizado con los operadores >> y <<

class AnalizadorLexico:
    def __init__(self, codigo_fuente):
        self.codigo = codigo_fuente
        self.posicion = 0
        self.caracter_actual = None
        self.tokens = []
        self.errores = []
        self.linea_actual = 1
        self.columna_actual = 1
        self.avanzar()
    
    def avanzar(self):
        """Avanza al siguiente caracter en el código fuente."""
        if self.posicion < len(self.codigo):
            self.caracter_actual = self.codigo[self.posicion]
            self.posicion += 1
            
            # Actualizar número de columna
            if self.caracter_actual == '\n':
                self.linea_actual += 1
                self.columna_actual = 1
            else:
                self.columna_actual += 1
        else:
            self.caracter_actual = None
    
    def retroceder(self):
        """Retrocede un caracter en el código fuente."""
        self.posicion -= 1
        if self.posicion >= 0:
            self.caracter_actual = self.codigo[self.posicion - 1]
            
            # Actualizar número de columna
            self.columna_actual -= 1
            if self.columna_actual < 1:
                # Si retrocedemos a la línea anterior, necesitamos calcular la columna
                # Asumimos columna 1 si esto ocurre
                self.linea_actual -= 1
                self.columna_actual = 1
        else:
            self.caracter_actual = None
    
    def es_espacio(self, c):
        """Verifica si el caracter es un espacio en blanco."""
        return c is not None and c.isspace()
    
    def es_letra(self, c):
        """Verifica si el caracter es una letra."""
        return c is not None and c.isalpha()
    
    def es_digito(self, c):
        """Verifica si el caracter es un dígito."""
        return c is not None and c.isdigit()
    
    def analizar(self):
        """Analiza el código fuente y genera los tokens."""
        while self.caracter_actual is not None:
            pos_columna_inicial = self.columna_actual - 1  # Guardamos la columna inicial del token
            pos_linea_inicial = self.linea_actual  # Guardamos la línea inicial del token
            
            # Ignorar espacios en blanco
            if self.es_espacio(self.caracter_actual):
                self.avanzar()
            
            # Identificadores y palabras clave
            elif self.es_letra(self.caracter_actual) or self.caracter_actual == '_':
                self.procesar_identificador(pos_linea_inicial, pos_columna_inicial)
            
            # Números (enteros y flotantes)
            elif self.es_digito(self.caracter_actual):
                self.procesar_numero(pos_linea_inicial, pos_columna_inicial)
            
            # Comentarios y operador de división
            elif self.caracter_actual == '/':
                self.procesar_division_o_comentario(pos_linea_inicial, pos_columna_inicial)
            
            # Operadores relacionales y asignación
            elif self.caracter_actual in ['>', '!', '=']:
                self.procesar_operador_relacional(pos_linea_inicial, pos_columna_inicial)
            
            # Operador < (puede ser relacional o parte de <<)
            elif self.caracter_actual == '<':
                self.procesar_operador_menor(pos_linea_inicial, pos_columna_inicial)
            
            # Operadores aritméticos
            elif self.caracter_actual in ['+', '-', '*', '%', '^']:
                self.procesar_operador_aritmetico(pos_linea_inicial, pos_columna_inicial)
            
            # Operadores lógicos
            elif self.caracter_actual == '&':
                col_inicial = self.columna_actual - 1
                self.avanzar()
                if self.caracter_actual == '&':
                    self.tokens.append(('OPERADOR_LOGICO', '&&', pos_linea_inicial, pos_columna_inicial))
                    self.avanzar()
                else:
                    self.tokens.append(('SIMBOLO', '&', pos_linea_inicial, pos_columna_inicial))
                    self.retroceder()
                    self.avanzar()
            
            elif self.caracter_actual == '|':
                col_inicial = self.columna_actual - 1
                self.avanzar()
                if self.caracter_actual == '|':
                    self.tokens.append(('OPERADOR_LOGICO', '||', pos_linea_inicial, pos_columna_inicial))
                    self.avanzar()
                else:
                    self.tokens.append(('SIMBOLO', '|', pos_linea_inicial, pos_columna_inicial))
                    self.retroceder()
                    self.avanzar()
            
            # Símbolos especiales
            elif self.caracter_actual in ['(', ')', '{', '}', '[', ']', ',', ';']:
                self.tokens.append(('SIMBOLO', self.caracter_actual, pos_linea_inicial, pos_columna_inicial))
                self.avanzar()
            
            # Cadenas de texto
            elif self.caracter_actual == '"':
                self.procesar_cadena(pos_linea_inicial, pos_columna_inicial)
            
            # Caracteres no reconocidos
            else:
                # Registrar el error con la línea y columna
                self.errores.append((f"Caracter no reconocido: '{self.caracter_actual}'", 
                                    pos_linea_inicial, pos_columna_inicial))
                self.avanzar()  # Avanzamos sin agregar token
        
        # Agregar token de fin de archivo
        self.tokens.append(('EOF', '', self.linea_actual, self.columna_actual))
        return self.tokens, self.errores
    
    def procesar_division_o_comentario(self, linea, columna):
        """Procesa el operador de división, comentarios o /=."""
        self.avanzar()  # Consumir el '/'
        
        if self.caracter_actual == '/':  # Comentario de línea
            self.procesar_comentario_linea(linea, columna)
        elif self.caracter_actual == '*':  # Comentario multilínea
            self.procesar_comentario_multilinea(linea, columna)
        elif self.caracter_actual == '=':  # Operador /=
            self.avanzar()  # Consumir el '='
            self.tokens.append(('OPERADOR_ASIGNACION', '/=', linea, columna))
        else:
            # Es solo el operador de división /
            self.tokens.append(('OPERADOR_ARITMETICO', '/', linea, columna))
    
    def procesar_identificador(self, linea, columna):
        """Procesa un identificador o palabra clave."""
        id_str = ''
        
        while self.caracter_actual is not None and (self.es_letra(self.caracter_actual) or 
                                                  self.es_digito(self.caracter_actual) or 
                                                  self.caracter_actual == '_'):
            id_str += self.caracter_actual
            self.avanzar()
        
        # Verificar si es una palabra clave
        palabras_clave = {
            'if': 'IF', 
            'then': 'THEN',
            'else': 'ELSE', 
            'end': 'END',
            'true': 'TRUE',
            'false': 'FALSE',
            'do': 'DO',
            'while': 'WHILE', 
            'until': 'UNTIL',
            'switch': 'SWITCH',
            'case': 'CASE',
            'for': 'FOR', 
            'return': 'RETURN', 
            'int': 'TIPO', 
            'float': 'TIPO', 
            'void': 'TIPO',
            'main': 'MAIN',
            'cin': 'CIN',
            'cout': 'COUT'
        }
        
        tipo_token = palabras_clave.get(id_str, 'ID')
        self.tokens.append((tipo_token, id_str, linea, columna))
    
    def procesar_numero(self, linea, columna):
        """Procesa un número entero o flotante."""
        num_str = ''
        es_float = False
        error_numero = False  # Bandera para detectar números mal formados
        
        # Verificar si hay signo
        if self.caracter_actual == '+' or self.caracter_actual == '-':
            num_str += self.caracter_actual
            self.avanzar()
        
        while self.caracter_actual is not None and self.es_digito(self.caracter_actual):
            num_str += self.caracter_actual
            self.avanzar()
        
        # Verificar si es un número flotante
        if self.caracter_actual == '.':
            punto_pos = len(num_str)  # Posición del punto en la cadena
            num_str += self.caracter_actual
            self.avanzar()
            
            # Verificar que después del punto hay al menos un dígito
            if not self.es_digito(self.caracter_actual):
                error_numero = True
                # Seguir consumiendo hasta encontrar un caracter no válido para números
                while (self.caracter_actual is not None and (self.es_digito(self.caracter_actual) or self.caracter_actual == '.')):
                    num_str += self.caracter_actual
                    self.avanzar()
            else:
                es_float = True
                while self.caracter_actual is not None and self.es_digito(self.caracter_actual):
                    num_str += self.caracter_actual
                    self.avanzar()
        
        if error_numero:
            # Registrar el número mal formado como error léxico
            self.errores.append((f"Número flotante mal formado: '{num_str}'", linea, columna))
            return
        elif es_float:
            self.tokens.append(('NUM_FLOAT', num_str, linea, columna))
        else:
            self.tokens.append(('NUM_INT', num_str, linea, columna))

    def procesar_cadena(self, linea, columna):
        """Procesa una cadena de texto delimitada por comillas dobles."""
        cadena = ''
        self.avanzar()  # Consumir la comilla inicial
        
        while self.caracter_actual is not None and self.caracter_actual != '"':
            if self.caracter_actual == '\n':
                # Error: cadena no cerrada
                self.errores.append((f"Cadena no cerrada: '\"' esperada", linea, columna))
                return
            cadena += self.caracter_actual
            self.avanzar()
        
        if self.caracter_actual == '"':
            self.avanzar()  # Consumir la comilla final
            self.tokens.append(('CADENA', f'"{cadena}"', linea, columna))
        else:
            # Error: EOF antes de cerrar la cadena
            self.errores.append((f"Cadena no cerrada: EOF alcanzado", linea, columna))
    
    def procesar_comentario_linea(self, linea, columna):
        """Procesa un comentario de línea."""
        comentario = '//'  # Incluimos los dos '/' iniciales
        
        while self.caracter_actual is not None and self.caracter_actual != '\n':
            comentario += self.caracter_actual
            self.avanzar()
        
        #self.tokens.append(('COMENTARIO_LINEA', comentario, linea, columna))

    def procesar_comentario_multilinea(self, linea, columna):
        """Procesa un comentario multilínea."""
        comentario = '/*'  # Incluimos los caracteres iniciales
        self.avanzar()  # Consumir el '*' después de la '/'
        
        while self.caracter_actual is not None:
            if self.caracter_actual == '*' and self.posicion < len(self.codigo) and self.codigo[self.posicion] == '/':
                comentario += '*/'  # Incluir los delimitadores de cierre
                self.avanzar()  # Consumir el '*'
                self.avanzar()  # Consumir el '/'
                break
            comentario += self.caracter_actual
            self.avanzar()
        
        #self.tokens.append(('COMENTARIO_MULTILINEA', comentario, linea, columna))
    
    def procesar_operador_relacional(self, linea, columna):
        """Procesa un operador relacional."""
        op = self.caracter_actual
        self.avanzar()
        
        # Verificar operadores de dos caracteres
        if op == '>' and self.caracter_actual == '>':
            # Operador de entrada >>
            op += self.caracter_actual
            self.avanzar()
            self.tokens.append(('OPERADOR_ENTRADA', op, linea, columna))
        elif self.caracter_actual == '=':
            op += self.caracter_actual
            self.avanzar()
            if op == '!=':
                self.tokens.append(('OPERADOR_LOGICO', op, linea, columna))  # != como operador lógico (NOT)
            else:
                self.tokens.append(('OPERADOR_RELACIONAL', op, linea, columna))
        else:
            if op == '=':
                self.tokens.append(('ASIGNACION', op, linea, columna))
            else:
                self.tokens.append(('OPERADOR_RELACIONAL', op, linea, columna))
    
    def procesar_operador_menor(self, linea, columna):
        """Procesa el operador < que puede ser relacional o parte de <<."""
        op = self.caracter_actual
        self.avanzar()
        
        if self.caracter_actual == '<':
            # Operador de salida <<
            op += self.caracter_actual
            self.avanzar()
            self.tokens.append(('OPERADOR_SALIDA', op, linea, columna))
        elif self.caracter_actual == '=':
            # Operador <=
            op += self.caracter_actual
            self.avanzar()
            self.tokens.append(('OPERADOR_RELACIONAL', op, linea, columna))
        else:
            # Operador < simple
            self.tokens.append(('OPERADOR_RELACIONAL', op, linea, columna))
    
    def procesar_operador_aritmetico(self, linea, columna):
        """Procesa un operador aritmético."""
        op = self.caracter_actual
        self.avanzar()
        
        # Verificar operadores dobles (++, --, +=, -=, *=, %=, ^=)
        if self.caracter_actual == '=':
            op += self.caracter_actual
            self.avanzar()
            self.tokens.append(('OPERADOR_ASIGNACION', op, linea, columna))
        elif (op in ['+', '-'] and self.caracter_actual == op):  # Incremento/Decremento
            op += self.caracter_actual
            self.avanzar()
            self.tokens.append(('OPERADOR_ASIG_UNARIO', op, linea, columna))
        else:
            self.tokens.append(('OPERADOR_ARITMETICO', op, linea, columna))


# Función para utilizar el analizador léxico
def analizar_codigo(codigo_fuente):
    analizador = AnalizadorLexico(codigo_fuente)
    tokens, errores = analizador.analizar()
    return tokens, errores

# Función para formatear los resultados para mostrarlos en el IDE
def formatear_resultados(tokens, formato_completo=True):
    if formato_completo:
        # Versión original con formato para mostrar en la pestaña
        resultado = "ANÁLISIS LÉXICO:\n"
        resultado += "-" * 80 + "\n"
        resultado += "| {:<20} | {:<20} | {:<8} | {:<8} |\n".format("TIPO", "VALOR", "LÍNEA", "COLUMNA")
        resultado += "-" * 80 + "\n"
        
        for token in tokens:
            tipo, valor, linea, columna = token
            # Truncar valores largos para la visualización
            if len(str(valor)) > 18:
                valor_mostrado = str(valor)[:15] + "..."
            else:
                valor_mostrado = str(valor)
            resultado += "| {:<20} | {:<20} | {:<8} | {:<8} |\n".format(tipo, valor_mostrado, linea, columna)
    else:
        # Versión simplificada solo con valores de tokens para guardar en archivo
        resultado = ""
        for token in tokens:
            _, valor, _, _ = token  # Solo tomamos el valor, ignoramos tipo, línea y columna
            if valor.strip():  # Solo agregamos si el valor no está vacío
                resultado += f"{valor}\n"
    
    return resultado

# Función para formatear los errores para mostrarlos en el IDE
def formatear_errores(errores):
    if not errores:
        return "No se encontraron errores léxicos"
    
    resultado = "ERRORES LÉXICOS:\n"
    resultado += "-" * 80 + "\n"
    resultado += "| {:<40} | {:<15} | {:<15} |\n".format("DESCRIPCIÓN", "LÍNEA", "COLUMNA")
    resultado += "-" * 80 + "\n"
    
    for error in errores:
        mensaje, linea, columna = error
        resultado += "| {:<40} | {:<15} | {:<15} |\n".format(mensaje, linea, columna)
    
    return resultado