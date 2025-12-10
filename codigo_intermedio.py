# archivo: codigo_intermedio.py

from typing import List, Tuple, Optional, Callable
from semantico import integrate_with_existing_analyzers, AnnotatedASTNode

# =========================
#   GENERADOR DE TAC
# =========================

class TACGenerator:
    def __init__(self):
        self.instructions: List[str] = []
        self.temp_count = 0
        self.label_count = 0

    def new_temp(self) -> str:
        self.temp_count += 1
        return f"t{self.temp_count}"

    def new_label(self, base: str = "L") -> str:
        self.label_count += 1
        return f"{base}{self.label_count}"

    def emit(self, text: str):
        self.instructions.append(text)

    # --------- ENTRADA PRINCIPAL DESDE EL AST ---------
    def generate_program(self, root: AnnotatedASTNode):
        if root is None:
            return
        self._gen_stmt(root)

    # --------- GENERACIÓN PARA SENTENCIAS ----------
    def _gen_stmt(self, node: AnnotatedASTNode):
        if node is None:
            return
        t = node.tipo

        # Nodos “contenedor”
        if t in ("PROGRAMA", "LISTA_DECLARACION", "LISTA_SENTENCIAS",
                 "DECLARACION_VARIABLE", "IDENTIFICADOR"):
            for h in node.hijos:
                self._gen_stmt(h)

        # Asignación:  ID = expresión;
        elif t == "=":
            if len(node.hijos) >= 2:
                id_node = node.hijos[0]
                sent_expr = node.hijos[1]
                expr_node = sent_expr.hijos[0] if sent_expr.hijos else None
                place = self._gen_expr(expr_node)
                self.emit(f"{id_node.valor} = {place}")

        # Salida: cout << ...
        elif t == "SENT_OUT":
            if node.hijos:
                salida = node.hijos[0]
                for parte in salida.hijos:
                    if parte.tipo == "CADENA":
                        # parte.valor ya viene con comillas
                        self.emit(f"PRINT_STR {parte.valor}")
                    else:
                        place = self._gen_expr(parte)
                        self.emit(f"PRINT {place}")

        # Entrada: cin >> id;
        elif t == "SENT_IN":
            if node.hijos:
                id_node = node.hijos[0]
                self.emit(f"READ {id_node.valor}")

        # If / else
        elif t == "SELECCION":
            # hijos: expr, LISTA_SENTENCIAS, [ELSE]
            expr_node = node.hijos[0] if node.hijos else None
            then_node = node.hijos[1] if len(node.hijos) > 1 else None

            else_node = None
            if len(node.hijos) > 2:
                for h in node.hijos[2:]:
                    if h.tipo == "ELSE":
                        else_node = h
                        break

            cond_place = self._gen_expr(expr_node)
            label_else = self.new_label("L_else")
            label_end = self.new_label("L_endif")

            self.emit(f"IF_FALSE {cond_place} GOTO {label_else}")
            if then_node:
                self._gen_stmt(then_node)
            self.emit(f"GOTO {label_end}")
            self.emit(f"LABEL {label_else}")
            if else_node and else_node.hijos:
                self._gen_stmt(else_node.hijos[0])  # LISTA_SENTENCIAS del else
            self.emit(f"LABEL {label_end}")

        # While
        elif t == "ITERACION":
            # hijos: expr, LISTA_SENTENCIAS
            expr_node = node.hijos[0] if node.hijos else None
            body_node = node.hijos[1] if len(node.hijos) > 1 else None
            label_start = self.new_label("L_while")
            label_end = self.new_label("L_endwhile")

            self.emit(f"LABEL {label_start}")
            cond_place = self._gen_expr(expr_node)
            self.emit(f"IF_FALSE {cond_place} GOTO {label_end}")
            if body_node:
                self._gen_stmt(body_node)
            self.emit(f"GOTO {label_start}")
            self.emit(f"LABEL {label_end}")

        else:
            # Por defecto, seguir recorriendo hijos
            for h in node.hijos:
                self._gen_stmt(h)

    # --------- GENERACIÓN PARA EXPRESIONES ----------
    def _gen_expr(self, node: AnnotatedASTNode):
        if node is None:
            return "0"
        t = node.tipo

        # Contenedores
        if t in ("SENT_EXPRESION", "COMPONENTE"):
            if node.hijos:
                return self._gen_expr(node.hijos[0])
            return "0"

        # Literales e identificadores
        if t in ("NUM_INT", "NUM_FLOAT"):
            return node.valor
        if t == "ID":
            return node.valor

        # Operadores binarios
        if t in ("+", "-", "*", "/", "%", "^",
                 ">", "<", ">=", "<=", "==", "!=",
                 "&&", "||"):
            izquierda = self._gen_expr(node.hijos[0])
            derecha = self._gen_expr(node.hijos[1])
            temp = self.new_temp()
            self.emit(f"{temp} = {izquierda} {t} {derecha}")
            return temp

        # Operador lógico unario (por si aparece '!')
        if t in ("!", "NOT"):
            op = self._gen_expr(node.hijos[0]) if node.hijos else "0"
            temp = self.new_temp()
            self.emit(f"{temp} = ! {op}")
            return temp

        # Cualquier otro nodo con hijos
        if node.hijos:
            return self._gen_expr(node.hijos[-1])

        return "0"


# =========================
#   INTÉRPRETE DE TAC
# =========================

class TACInterpreter:
    def __init__(
        self,
        instructions: List[str],
        read_func: Optional[Callable[[str], str]] = None,
        write_func: Optional[Callable[[str], None]] = None
    ):
        self.instructions = instructions
        self.labels = self._build_label_table()
        self.pc = 0
        self.mem: dict = {}
        self.read_func = read_func or self._default_read
        self.write_func = write_func
        self.output_lines: List[str] = []

    # ----- helpers de IO -----
    def _default_read(self, prompt: str) -> str:
        # Para usar en consola si no se pasa un callback
        return input(prompt or "> ")

    def write(self, text: str):
        s = str(text)
        self.output_lines.append(s)
        if self.write_func:
            self.write_func(s)

    # ----- labels -----
    def _build_label_table(self):
        labels = {}
        for idx, inst in enumerate(self.instructions):
            inst = inst.strip()
            if inst.startswith("LABEL "):
                nombre = inst.split(None, 1)[1].strip()
                labels[nombre] = idx
        return labels

    # ----- ejecución -----
    def run(self) -> str:
        while self.pc < len(self.instructions):
            inst = self.instructions[self.pc].strip()
            if not inst:
                self.pc += 1
                continue
            if inst.startswith("LABEL "):
                # solo marca posición
                self.pc += 1
                continue
            elif inst.startswith("GOTO "):
                label = inst.split(None, 1)[1].strip()
                self.pc = self.labels.get(label, len(self.instructions))
                continue
            elif inst.startswith("IF_FALSE "):
                # IF_FALSE cond GOTO L_x
                _, rest = inst.split("IF_FALSE", 1)
                cond_part, _, label = rest.partition("GOTO")
                cond_name = cond_part.strip()
                label = label.strip()
                cond_val = self._eval_operand(cond_name)
                if not bool(cond_val):
                    self.pc = self.labels.get(label, len(self.instructions))
                else:
                    self.pc += 1
                continue
            elif inst.startswith("READ "):
                var = inst.split(None, 1)[1].strip()
                val_str = self.read_func(f"Entrada para {var}: ")
                val = self._parse_number(val_str)
                self.mem[var] = val
                self.pc += 1
                continue
            elif inst.startswith("PRINT_STR "):
                # PRINT_STR "texto"
                text = inst[len("PRINT_STR "):].strip()
                # quitar comillas exteriores si vienen
                if text.startswith('"') and text.endswith('"'):
                    text = text[1:-1]
                self.write(text)
                self.pc += 1
                continue
            elif inst.startswith("PRINT "):
                expr = inst[len("PRINT "):].strip()
                val = self._eval_operand(expr)
                self.write(val)
                self.pc += 1
                continue
            else:
                # Asignación: x = ...
                if "=" in inst:
                    self._exec_assign(inst)
                    self.pc += 1
                else:
                    # instrucción desconocida, la saltamos
                    self.pc += 1
        return "\n".join(self.output_lines)

    # ----- asignaciones -----
    def _exec_assign(self, inst: str):
        left, right = inst.split("=", 1)
        left = left.strip()
        right = right.strip()

        tokens = right.split()
        # x = valor
        if len(tokens) == 1:
            value = self._eval_operand(tokens[0])
        # x = ! op
        elif len(tokens) == 2 and tokens[0] == "!":
            op_val = self._eval_operand(tokens[1])
            value = 0 if bool(op_val) else 1
        # x = a OP b
        elif len(tokens) == 3:
            a, op, b = tokens
            v1 = self._eval_operand(a)
            v2 = self._eval_operand(b)
            value = self._apply_op(v1, op, v2)
        else:
            value = 0
        self.mem[left] = value

    # ----- evaluación de operandos y operadores -----
    def _parse_number(self, s: str):
        s = s.strip()
        try:
            if "." in s:
                return float(s)
            return int(s)
        except ValueError:
            # Si no es número, lo tomamos como 0
            return 0

    def _eval_operand(self, tok: str):
        tok = tok.strip()
        if tok in self.mem:
            return self.mem[tok]
        # literal numérico
        try:
            return self._parse_number(tok)
        except Exception:
            return 0

    def _apply_op(self, v1, op: str, v2):
        # Aritméticos
        if op == "+":
            return v1 + v2
        if op == "-":
            return v1 - v2
        if op == "*":
            return v1 * v2
        if op == "/":
            return v1 / v2 if v2 != 0 else 0
        if op == "%":
            return v1 % v2 if v2 != 0 else 0
        if op == "^":
            return v1 ** v2

        # Relacionales -> 1 ó 0
        if op == ">":
            return 1 if v1 > v2 else 0
        if op == "<":
            return 1 if v1 < v2 else 0
        if op == ">=":
            return 1 if v1 >= v2 else 0
        if op == "<=":
            return 1 if v1 <= v2 else 0
        if op == "==":
            return 1 if v1 == v2 else 0
        if op == "!=":
            return 1 if v1 != v2 else 0

        # Lógicos (asumimos 0 = falso, !=0 = verdadero)
        if op == "&&":
            return 1 if bool(v1) and bool(v2) else 0
        if op == "||":
            return 1 if bool(v1) or bool(v2) else 0

        return 0


# =========================
#   HELPERS PARA GUI / IDE
# =========================

def generar_tac_desde_fuente(codigo_fuente: str):
    """Devuelve (instrucciones_TAC, errores_semánticos)"""
    annotated_ast, symbol_table, semantic_errors = integrate_with_existing_analyzers(codigo_fuente)
    if annotated_ast is None:
        return [], semantic_errors

    gen = TACGenerator()
    gen.generate_program(annotated_ast)
    return gen.instructions, semantic_errors


def ejecutar_tac_desde_fuente(
    codigo_fuente: str,
    read_func: Optional[Callable[[str], str]] = None,
    write_func: Optional[Callable[[str], None]] = None
) -> Tuple[str, bool]:
    """
    Ejecuta el código fuente pasando por:
    léxico -> sintáctico -> semántico -> TAC -> VM

    Return:
      (salida_texto_completa, hubo_errores_graves)
    """
    instructions, semantic_errors = generar_tac_desde_fuente(codigo_fuente)

    errores_graves = [
        e for e in semantic_errors
        if getattr(e, "error_type", "") in ("semantic_error", "type_error")
    ]
    hubo_errores = len(errores_graves) > 0

    if not instructions:
        return "No se generaron instrucciones TAC (¿errores de análisis?).", True

    vm = TACInterpreter(
        instructions,
        read_func=read_func,
        write_func=write_func
    )
    salida = vm.run()
    return salida, hubo_errores
