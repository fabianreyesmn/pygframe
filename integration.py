# Archivo: integration.py
# Este archivo contiene la integración entre el IDE PyGFrame y el analizador léxico

import importlib.util
import sys
import os

# Función para importar el analizador léxico desde un archivo
def importar_analizador_lexico(ruta_archivo):
    # Obtener nombre del módulo sin extensión
    nombre_modulo = os.path.splitext(os.path.basename(ruta_archivo))[0]
    
    # Importar módulo dinámicamente
    spec = importlib.util.spec_from_file_location(nombre_modulo, ruta_archivo)
    modulo = importlib.util.module_from_spec(spec)
    sys.modules[nombre_modulo] = modulo
    spec.loader.exec_module(modulo)
    
    return modulo

# Función para aplicar resaltado de sintaxis en el editor
def aplicar_resaltado(ide_instance, tokens):
    """Aplica el resaltado de sintaxis basado en los tokens del analizador léxico"""
    # Limpiar todas las etiquetas existentes
    for tag in ["number", "identifier", "comment", "keyword", "operator", "relational", "logical", "symbol", "assignment"]:
        ide_instance.editor.tag_remove(tag, "1.0", "end")
    
    # Configurar colores para cada tipo de token
    ide_instance.editor.tag_configure("number", foreground="#f2907c")  # Color 1: Números (naranja)
    ide_instance.editor.tag_configure("identifier", foreground="#d4af37")  # Color 2: Identificadores (dorado)
    ide_instance.editor.tag_configure("comment", foreground="#737373")  # Color 3: Comentarios (gris oscuro)
    ide_instance.editor.tag_configure("keyword", foreground="#FF33A1")  # Color 4: Palabras reservadas (rosa)
    ide_instance.editor.tag_configure("operator", foreground="#7cbef7")  # Color 5: Operadores aritméticos (azul claro)
    ide_instance.editor.tag_configure("relational", foreground="#87c97b")  # Color 6: Operadores relacionales (verde)
    ide_instance.editor.tag_configure("logical", foreground="#87c97b")  # Color 6: Operadores lógicos (verde)
    ide_instance.editor.tag_configure("symbol", foreground="#FFFFFF")  # Símbolos (blanco)
    ide_instance.editor.tag_configure("assignment", foreground="#a357fa")  # Asignación (morado)
    
    # Aplicar etiquetas según tipo de token
    for tipo, valor, linea, columna in tokens:
        if tipo == "EOF":
            continue
            
        # Calcular posiciones de inicio y fin en el texto
        inicio = f"{linea}.{columna-1}"
        fin = f"{linea}.{columna-1 + len(str(valor))}"
        
        # Asignar etiqueta según tipo de token
        if tipo in ["NUM_INT", "NUM_FLOAT"]:
            ide_instance.editor.tag_add("number", inicio, fin)
        elif tipo == "ID":
            ide_instance.editor.tag_add("identifier", inicio, fin)
        elif tipo in ["COMENTARIO_LINEA", "COMENTARIO_MULTILINEA"]:
            ide_instance.editor.tag_add("comment", inicio, fin)
        elif tipo in ["IF", "ELSE", "WHILE", "FOR", "RETURN", "TIPO", "END", "DO", "SWITCH", "CASE", "MAIN", "CIN", "COUT"]:
            ide_instance.editor.tag_add("keyword", inicio, fin)
        elif tipo == "OPERADOR_ARITMETICO":
            ide_instance.editor.tag_add("operator", inicio, fin)
        elif tipo == "OPERADOR_RELACIONAL":
            ide_instance.editor.tag_add("relational", inicio, fin)
        elif tipo == "OPERADOR_LOGICO":
            ide_instance.editor.tag_add("logical", inicio, fin)
        elif tipo == "SIMBOLO":
            ide_instance.editor.tag_add("symbol", inicio, fin)
        elif tipo == "ASIGNACION":
            ide_instance.editor.tag_add("assignment", inicio, fin)

# Modificar la función lexical_analysis en la clase CustomIDE
def integrar_analizador_lexico(ide_instance):
    # Ruta al archivo del analizador léxico
    ruta_analizador = "lexico.py"
    
    try:
        # Importar el analizador léxico
        modulo_analizador = importar_analizador_lexico(ruta_analizador)
        
        # Obtener el código del editor
        codigo_fuente = ide_instance.editor.get('1.0', 'end')
        
        # Ejecutar el análisis léxico
        tokens, errores = modulo_analizador.analizar_codigo(codigo_fuente)
        
        # Formatear y mostrar resultados en la pestaña correspondiente
        resultado_formateado = modulo_analizador.formatear_resultados(tokens)
        ide_instance.lexico_tab.delete('1.0', 'end')
        ide_instance.lexico_tab.insert('1.0', resultado_formateado)
        
        # Aplicar resaltado de sintaxis en el editor
        aplicar_resaltado(ide_instance, tokens)
        
        # Cambiar a la pestaña léxico
        ide_instance.right_tabs.select(0)  # Seleccionar la primera pestaña (Léxico)
        
        # Formatear y mostrar errores en la pestaña de errores léxicos
        errores_formateados = modulo_analizador.formatear_errores(errores)
        ide_instance.errores_lexicos_tab.delete('1.0', 'end')
        ide_instance.errores_lexicos_tab.insert('1.0', errores_formateados)
        
        # Cambiar a la pestaña de errores léxicos si hay errores
        if errores:
            ide_instance.bottom_tabs.select(0)  # Seleccionar la primera pestaña (Errores Léxicos)
        
        return True
    
    except Exception as e:
        # Mostrar error en la pestaña de errores léxicos
        ide_instance.errores_lexicos_tab.delete('1.0', 'end')
        ide_instance.errores_lexicos_tab.insert('1.0', f"Error al ejecutar el analizador léxico: {str(e)}")
        ide_instance.bottom_tabs.select(0)
        return False