# Mejoras al Analizador Semántico: Cálculo de Valores en Operaciones

## Resumen
Se implementó la funcionalidad para calcular y mostrar los valores reales de las operaciones aritméticas en el analizador semántico. Ahora, en lugar de mostrar solo el operador ('+', '-', '*', etc.) en la columna "Valor" del visualizador AST, se muestra el resultado calculado de la operación.

## Cambios Realizados

### 1. Modificación del Método `visit()` en `SemanticVisitor`
**Archivo:** `semantico.py`

Se cambió el orden de procesamiento para que los nodos hijos se procesen ANTES que el nodo padre. Esto permite un cálculo "bottom-up" donde los valores de los operandos están disponibles antes de calcular la operación.

**Antes:**
```python
# Procesar nodo padre primero
method(annotated_node)
# Luego procesar hijos
for hijo in node.hijos:
    annotated_child = self.visit(hijo)
```

**Después:**
```python
# Procesar hijos primero
for hijo in node.hijos:
    annotated_child = self.visit(hijo)
# Luego procesar nodo padre
method(annotated_node)
```

### 2. Mejora del Método `visit_operador_aritmetico()`
**Archivo:** `semantico.py`

Se agregó la llamada al método `_calculate_operation_value()` para calcular el valor de la operación después de inferir el tipo.

```python
# Calcular el valor de la operación si es posible
result_value = self._calculate_operation_value(node)
if result_value is not None:
    node.set_semantic_value(result_value)
```

### 3. Nuevo Método `_calculate_operation_value()`
**Archivo:** `semantico.py`

Método que calcula el valor de una operación aritmética si todos los operandos son conocidos. Soporta:
- Operaciones básicas: +, -, *, /, %, ^
- Cálculo recursivo de expresiones anidadas
- Manejo de errores (división por cero, overflow, etc.)

### 4. Mejora del Método `_get_node_value()`
**Archivo:** `semantico.py`

Se mejoró para:
- Buscar valores en nodos contenedores (COMPONENTE, SENT_EXPRESION, etc.)
- Calcular recursivamente operaciones anidadas
- Manejar literales numéricos (int y float)
- Retornar valores semánticos ya calculados

**Característica clave:**
```python
# Si es un nodo contenedor, buscar en sus hijos
elif len(node.hijos) == 1:
    return self._get_node_value(node.hijos[0])
```

### 5. Modificación del Método `to_dict()` en `AnnotatedASTNode`
**Archivo:** `semantico.py`

Se modificó para que use el `semantic_value` en lugar del `valor` original cuando esté disponible:

```python
# Si hay un valor semántico calculado, usarlo en lugar del valor original
if self.semantic_value is not None:
    base_dict['valor'] = self.semantic_value
```

### 6. Detección de Operadores Aritméticos en `visit()`
**Archivo:** `semantico.py`

Se agregó detección explícita de operadores aritméticos para asegurar que se procesen correctamente:

```python
# Para operadores aritméticos, usar un método específico
if node.tipo in ['+', '-', '*', '/', '%', '^']:
    self.visit_operador_aritmetico(annotated_node)
```

## Ejemplos de Resultados

### Antes:
```
Operación '+' → Valor: +
  Operando izquierdo: 3
  Operando derecho: 7
```

### Después:
```
Operación '+' → Valor: 10
  Operando izquierdo: 3
  Operando derecho: 7
```

## Operaciones Soportadas

1. **Suma (+)**: `3 + 7 = 10`
2. **Resta (-)**: `10 - 3 = 7`
3. **Multiplicación (*)**: `5 * 4 = 20`
4. **División (/)**: `8 / 2 = 4.0`
5. **Módulo (%)**: `10 % 3 = 1`
6. **Potencia (^)**: `2 ^ 3 = 8`

## Expresiones Complejas

El sistema ahora puede calcular expresiones anidadas complejas:

```
(5 - 3) * (8 / 2) = 8.0
2 + 3 - 1 = 4
24.0 + 4 - 1 / 3 * 2 + 34 - 1 = 60.33333333333333
```

## Limitaciones

- **Variables**: No se calculan valores para variables ya que no tenemos un entorno de ejecución en tiempo de compilación
- **Funciones**: No se evalúan llamadas a funciones
- **Expresiones booleanas**: Solo se calculan operaciones aritméticas, no expresiones lógicas

## Visualización en el IDE

Los valores calculados ahora se muestran automáticamente en:
1. **Pestaña "Semántico"**: En el visualizador AST, columna "Valor"
2. **Archivos de salida**: En los archivos `*_annotated_ast.txt`

## Pruebas

Se verificó el funcionamiento con el archivo `TestSemantica.txt` que contiene múltiples operaciones aritméticas complejas. Todas las operaciones se calculan correctamente.

## Compatibilidad

Los cambios son completamente compatibles con el código existente y no afectan:
- Análisis léxico
- Análisis sintáctico
- Detección de errores semánticos
- Tabla de símbolos
- Sistema de tipos

## Fecha de Implementación
6 de noviembre de 2025
