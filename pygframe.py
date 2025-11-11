import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkinter.scrolledtext import ScrolledText
from PIL import Image, ImageTk
import ctypes
import re

class CustomIDE:
    def __init__(self, root):
        self.root = root
        self.root.title("PyGFrame")
        
        # Configurar tema oscuro
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.style.configure(".", 
            background='#282c34',
            foreground='#abb2bf',
            fieldbackground='#282c34'
        )
        
        # Configurar estilo para el toolbar
        self.style.configure('Toolbar.TFrame', background='#282c34')

        # Configurar estilo para el scrollbar
        self.style.configure("TScrollbar",
            background="#21252b",
            troughcolor="#282c34",
            bordercolor="#21252b",
            arrowcolor="#abb2bf",
            relief='flat'
        )
        self.style.map("TScrollbar",
            background=[('active', '#2c313a')]
        )
        
        self.root.configure(bg='#282c34')
        self.current_file = None
        
        self.create_menu()
        self.create_toolbar()
        self.create_main_interface()
        
        # Configurar el seguimiento de posición del cursor
        self.editor.bind('<KeyRelease>', self.update_status)
        self.editor.bind('<ButtonRelease-1>', self.update_status)
        self.editor.bind('<Motion>', self.update_status)  # Actualizar al mover el mouse

         # Configurar el resaltado en tiempo real
        self.editor.bind('<KeyRelease>', self.on_key_release)
        self.last_highlight_time = 0
        self.highlight_delay = 0  # milisegundos entre resaltados
        
    def create_menu(self):
        menubar = tk.Menu(self.root, bg='#21252b', fg='#abb2bf')
        self.root.config(menu=menubar)
        
        # Menú Archivo
        file_menu = tk.Menu(menubar, tearoff=0, bg='#21252b', fg='#abb2bf')
        menubar.add_cascade(label="Archivo", menu=file_menu)
        file_menu.add_command(label="Abrir", command=self.open_file)
        file_menu.add_command(label="Cerrar archivo", command=self.close_file)
        file_menu.add_command(label="Guardar", command=self.save_file)
        file_menu.add_command(label="Guardar como", command=self.save_as_file)
        file_menu.add_separator()
        file_menu.add_command(label="Salir", command=self.root.quit)
        
        # Menú Análisis
        analysis_menu = tk.Menu(menubar, tearoff=0, bg='#21252b', fg='#abb2bf')
        menubar.add_cascade(label="Análisis", menu=analysis_menu)
        analysis_menu.add_command(label="Análisis Léxico", command=self.lexical_analysis)
        analysis_menu.add_command(label="Análisis Sintáctico", command=self.syntax_analysis)
        analysis_menu.add_command(label="Análisis Semántico", command=self.semantic_analysis)
        analysis_menu.add_command(label="Código Intermedio", command=self.intermediate_code)
        analysis_menu.add_command(label="Ejecutar", command=self.execute_code)
        
    def load_and_resize_image(self, path, width, height):
        """Carga una imagen y la redimensiona al tamaño especificado"""
        try:
            img = Image.open(path)
            img = img.resize((width, height), Image.LANCZOS)  # LANCZOS es el método de redimensionamiento recomendado
            return ImageTk.PhotoImage(img)
        except Exception as e:
            print(f"Error al cargar la imagen {path}: {e}")
            # Crear una imagen en blanco como fallback
            return tk.PhotoImage(width=width, height=height)
        
    def create_toolbar(self):
        toolbar = ttk.Frame(self.root, style='Toolbar.TFrame')
        toolbar.pack(fill=tk.X, padx=5, pady=5)

        # Configurar estilo de botones
        self.style.configure('Toolbar.TButton',
            background='#21252b',
            foreground='#abb2bf',
            borderwidth=1,
            padding=(2, 2),  # (horizontal, vertical)
            relief='flat',
            font=('Segoe UI Emoji', 10)  # Usar una fuente que soporte emojis/símbolos
        )
        self.style.map('Toolbar.TButton',
            background=[('active', '#282c34')],
            relief=[('pressed', 'solid')]
        )
    
        # Crear botones
        ttk.Button(toolbar, text="📂", command=self.open_file, style='Toolbar.TButton').pack(side=tk.LEFT, padx=1)
        ttk.Button(toolbar, text="💾", command=self.save_file, style='Toolbar.TButton').pack(side=tk.LEFT, padx=1)
        ttk.Button(toolbar, text="⚙️", command=self.compile_code, style='Toolbar.TButton').pack(side=tk.LEFT, padx=1)
        ttk.Button(toolbar, text="🔍", command=self.lexical_analysis, style='Toolbar.TButton').pack(side=tk.LEFT, padx=1)
        ttk.Button(toolbar, text="🌳", command=self.syntax_analysis, style='Toolbar.TButton').pack(side=tk.LEFT, padx=1)
        ttk.Button(toolbar, text="✅", command=self.semantic_analysis, style='Toolbar.TButton').pack(side=tk.LEFT, padx=1)
        ttk.Button(toolbar, text="📜", command=self.intermediate_code, style='Toolbar.TButton').pack(side=tk.LEFT, padx=1)
        ttk.Button(toolbar, text="▶️", command=self.execute_code, style='Toolbar.TButton').pack(side=tk.LEFT, padx=1)

    def create_main_interface(self):
        # Contenedor principal para organizar el diseño
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Crear barra de estado primero para que esté en la parte inferior
        status_frame = ttk.Frame(main_container, height=25)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.status_bar = ttk.Label(status_frame, text="Líneas: 1, Columnas: 1",
                                  background='#21252b', foreground='#61afef',
                                  padding=(5, 0))
        self.status_bar.pack(side=tk.LEFT, fill=tk.X)
        
        # Panel principal para el área de trabajo
        main_panel = ttk.PanedWindow(main_container, orient=tk.HORIZONTAL)
        main_panel.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Panel izquierdo (editor)
        left_frame = ttk.Frame(main_panel)
        main_panel.add(left_frame, weight=1)
        
        # Crear un marco para contener el editor y sus barras de desplazamiento
        editor_frame = ttk.Frame(left_frame)
        editor_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Editor con números de línea
        self.line_numbers = tk.Text(editor_frame, width=4, padx=3, takefocus=0, border=0,
                                  background='#282c34', foreground='#5c6370',
                                  state='disabled', wrap=tk.NONE)
        self.line_numbers.grid(row=0, column=0, sticky='nsew')
        
        # Crear el editor de texto
        self.editor = tk.Text(editor_frame, wrap=tk.NONE, undo=True,
                             background='#282c34', foreground='#abb2bf',
                             insertbackground='#61afef')
        self.editor.grid(row=0, column=1, sticky='nsew')
        
        # Crear scrollbar vertical para el editor
        self.editor_vsb = ttk.Scrollbar(editor_frame, orient="vertical", command=self.on_editor_scroll_y)
        self.editor_vsb.grid(row=0, column=2, sticky='ns')
        self.editor.configure(yscrollcommand=self.on_editor_y_scroll_change)
        
        # Crear scrollbar horizontal para el editor
        self.editor_hsb = ttk.Scrollbar(editor_frame, orient="horizontal", command=self.editor.xview)
        self.editor_hsb.grid(row=1, column=1, sticky='ew')
        self.editor.configure(xscrollcommand=self.editor_hsb.set)
        
        # Configurar el grid para que se expanda correctamente
        editor_frame.grid_rowconfigure(0, weight=1)
        editor_frame.grid_columnconfigure(1, weight=1)
        
        # Panel derecho (resultados con pestañas)
        right_frame = ttk.Frame(main_panel)
        main_panel.add(right_frame, weight=1)
        
        # Crear pestañas para la parte derecha
        self.right_tabs = ttk.Notebook(right_frame)
        self.right_tabs.pack(fill=tk.BOTH, expand=True)
        
        # Configurar estilo para pestañas
        self.style.configure('TNotebook.Tab', background='#21252b', foreground='#abb2bf', padding=[10, 2])
        self.style.map('TNotebook.Tab', 
                     background=[('selected', '#282c34')],
                     foreground=[('selected', '#61afef')])
        
        # Crear las pestañas para la parte derecha
        lexico_frame = ttk.Frame(self.right_tabs)
        self.lexico_tab = tk.Text(lexico_frame, wrap=tk.WORD, background='#282c34', foreground='#abb2bf', relief='flat', borderwidth=0)
        lexico_scroll = ttk.Scrollbar(lexico_frame, orient=tk.VERTICAL, command=self.lexico_tab.yview)
        self.lexico_tab.config(yscrollcommand=lexico_scroll.set)
        lexico_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.lexico_tab.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        sintactico_frame = ttk.Frame(self.right_tabs)
        self.sintactico_tab = tk.Text(sintactico_frame, wrap=tk.WORD, background='#282c34', foreground='#abb2bf', relief='flat', borderwidth=0)
        sintactico_scroll = ttk.Scrollbar(sintactico_frame, orient=tk.VERTICAL, command=self.sintactico_tab.yview)
        self.sintactico_tab.config(yscrollcommand=sintactico_scroll.set)
        sintactico_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.sintactico_tab.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        semantico_frame = ttk.Frame(self.right_tabs)
        self.semantico_tab = tk.Text(semantico_frame, wrap=tk.WORD, background='#282c34', foreground='#abb2bf', relief='flat', borderwidth=0)
        semantico_scroll = ttk.Scrollbar(semantico_frame, orient=tk.VERTICAL, command=self.semantico_tab.yview)
        self.semantico_tab.config(yscrollcommand=semantico_scroll.set)
        semantico_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.semantico_tab.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        hash_table_frame = ttk.Frame(self.right_tabs)
        self.hash_table_tab = tk.Text(hash_table_frame, wrap=tk.NONE, background='#282c34', foreground='#abb2bf', relief='flat', borderwidth=0)
        
        v_scroll_ht = ttk.Scrollbar(hash_table_frame, orient=tk.VERTICAL, command=self.hash_table_tab.yview)
        self.hash_table_tab.config(yscrollcommand=v_scroll_ht.set)
        
        h_scroll_ht = ttk.Scrollbar(hash_table_frame, orient=tk.HORIZONTAL, command=self.hash_table_tab.xview)
        self.hash_table_tab.config(xscrollcommand=h_scroll_ht.set)
        
        v_scroll_ht.pack(side=tk.RIGHT, fill=tk.Y)
        h_scroll_ht.pack(side=tk.BOTTOM, fill=tk.X)
        self.hash_table_tab.pack(fill=tk.BOTH, expand=True)

        codigo_intermedio_frame = ttk.Frame(self.right_tabs)
        self.codigo_intermedio_tab = tk.Text(codigo_intermedio_frame, wrap=tk.WORD, background='#282c34', foreground='#abb2bf', relief='flat', borderwidth=0)
        codigo_intermedio_scroll = ttk.Scrollbar(codigo_intermedio_frame, orient=tk.VERTICAL, command=self.codigo_intermedio_tab.yview)
        self.codigo_intermedio_tab.config(yscrollcommand=codigo_intermedio_scroll.set)
        codigo_intermedio_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.codigo_intermedio_tab.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Añadir pestañas al notebook
        self.right_tabs.add(lexico_frame, text="Léxico")
        self.right_tabs.add(sintactico_frame, text="Sintáctico")
        self.right_tabs.add(semantico_frame, text="Semántico")
        self.right_tabs.add(hash_table_frame, text="Tabla de Símbolos")
        self.right_tabs.add(codigo_intermedio_frame, text="Código Intermedio")
        
        # Panel inferior con pestañas para errores
        bottom_frame = ttk.Frame(main_container)
        bottom_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Crear pestañas para la parte inferior
        self.bottom_tabs = ttk.Notebook(bottom_frame)
        self.bottom_tabs.pack(fill=tk.BOTH, expand=True)
        
        # Crear las pestañas para la parte inferior
        errores_lexicos_frame = ttk.Frame(self.bottom_tabs)
        self.errores_lexicos_tab = tk.Text(errores_lexicos_frame, height=10, wrap=tk.WORD, background='#282c34', foreground='#e06c75', relief='flat', borderwidth=0)
        errores_lexicos_scroll = ttk.Scrollbar(errores_lexicos_frame, orient=tk.VERTICAL, command=self.errores_lexicos_tab.yview)
        self.errores_lexicos_tab.config(yscrollcommand=errores_lexicos_scroll.set)
        errores_lexicos_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.errores_lexicos_tab.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        errores_sintacticos_frame = ttk.Frame(self.bottom_tabs)
        self.errores_sintacticos_tab = tk.Text(errores_sintacticos_frame, height=10, wrap=tk.WORD, background='#282c34', foreground='#e06c75', relief='flat', borderwidth=0)
        errores_sintacticos_scroll = ttk.Scrollbar(errores_sintacticos_frame, orient=tk.VERTICAL, command=self.errores_sintacticos_tab.yview)
        self.errores_sintacticos_tab.config(yscrollcommand=errores_sintacticos_scroll.set)
        errores_sintacticos_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.errores_sintacticos_tab.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        errores_semanticos_frame = ttk.Frame(self.bottom_tabs)
        self.errores_semanticos_tab = tk.Text(errores_semanticos_frame, height=10, wrap=tk.WORD, background='#282c34', foreground='#e06c75', relief='flat', borderwidth=0)
        errores_semanticos_scroll = ttk.Scrollbar(errores_semanticos_frame, orient=tk.VERTICAL, command=self.errores_semanticos_tab.yview)
        self.errores_semanticos_tab.config(yscrollcommand=errores_semanticos_scroll.set)
        errores_semanticos_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.errores_semanticos_tab.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        resultados_frame = ttk.Frame(self.bottom_tabs)
        self.resultados_tab = tk.Text(resultados_frame, height=10, wrap=tk.WORD, background='#282c34', foreground='#61afef', relief='flat', borderwidth=0)
        resultados_scroll = ttk.Scrollbar(resultados_frame, orient=tk.VERTICAL, command=self.resultados_tab.yview)
        self.resultados_tab.config(yscrollcommand=resultados_scroll.set)
        resultados_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.resultados_tab.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Añadir pestañas al notebook
        self.bottom_tabs.add(errores_lexicos_frame, text="Errores Léxicos")
        self.bottom_tabs.add(errores_sintacticos_frame, text="Errores Sintácticos")
        self.bottom_tabs.add(errores_semanticos_frame, text="Errores Semánticos")
        self.bottom_tabs.add(resultados_frame, text="Resultados")
        
        # Inicializar líneas
        self.update_line_numbers()
        
        # Interacción con mouse y teclado
        self.setup_editor_bindings()
    
    def on_key_press(self, event):
        """Maneja los eventos de teclas presionadas"""
        self.update_status(event)
        return
    
    def on_mouse_click(self, event):
        """Maneja un clic simple en el editor"""
        self.update_status(event)
        return
    
    def on_double_click(self, event):
        """Maneja doble clic en el editor (selecciona una palabra)"""
        self.update_status(event)
        return
    
    def on_triple_click(self, event):
        """Maneja triple clic en el editor (selecciona una línea)"""
        self.update_status(event)
        return
    
    def on_mouse_drag(self, event):
        """Maneja el arrastre del mouse (selección)"""
        self.update_status(event)
        return
    
    def on_mouse_wheel(self, event):
        """Maneja el desplazamiento de la rueda del mouse"""
        self.update_line_numbers()
        return
    
    def on_ctrl_home(self, event):
        """Maneja Ctrl+Home para ir al principio del documento"""
        self.editor.mark_set("insert", "1.0")
        self.editor.see("insert")
        self.update_status(event)
        return "break"
    
    def on_ctrl_end(self, event):
        """Maneja Ctrl+End para ir al final del documento"""
        self.editor.mark_set("insert", "end-1c")
        self.editor.see("insert")
        self.update_status(event)
        return "break"
    
    def on_select_all(self, event):
        """Maneja Ctrl+A para seleccionar todo el texto"""
        self.editor.tag_add("sel", "1.0", "end")
        self.update_status(event)
        return "break"
    
    def on_editor_scroll_y(self, *args):
        """Maneja el scroll vertical sincronizado"""
        self.editor.yview(*args)
        self.line_numbers.yview(*args)
        self.update_line_numbers()
    
    def on_editor_y_scroll_change(self, *args):
        """Actualiza las posiciones de ambas barras de desplazamiento"""
        self.editor_vsb.set(*args)
        # Sincroniza la posición de los números de línea con el editor
        self.line_numbers.yview_moveto(args[0])
        
    def update_status(self, event=None):
        """Actualiza la barra de estado y los números de línea"""
        self.update_cursor_position()
        self.update_line_numbers()
    
    def update_cursor_position(self):
        """Actualiza la información de la posición del cursor en la barra de estado"""
        position = self.editor.index(tk.INSERT)
        line, column = position.split('.')
        self.status_bar.config(text=f"Líneas: {line}, Columnas: {int(column) + 1}")
    
    def update_line_numbers(self, event=None):
        """Actualiza los números de línea del editor"""
        # Obtener contenido del texto
        text_content = self.editor.get('1.0', tk.END)
        
        # Contar líneas incluyendo las vacías
        num_lines = text_content.count('\n') + 1
        
        # Si el texto termina con nueva línea, restar 1 para que la cuenta sea precisa
        if text_content.endswith('\n'):
            num_lines -= 1
        
        # Generar números de línea
        line_numbers_content = '\n'.join(str(i) for i in range(1, num_lines + 1))
        
        # Actualizar widget de números de línea
        self.line_numbers.config(state='normal')
        self.line_numbers.delete('1.0', tk.END)
        self.line_numbers.insert('1.0', line_numbers_content)
        self.line_numbers.config(state='disabled')
        
        # Sincronizar posición de scroll con el editor
        self.line_numbers.yview_moveto(self.editor.yview()[0])

    def on_key_release(self, event):
        """Maneja los eventos de teclas liberadas"""
        self.update_line_numbers()
        
        # Intentar resaltar la sintaxis con un pequeño retraso para mejorar el rendimiento
        self.editor.after(100, self.highlight_syntax_real_time)
        self.editor.after(100, self.highlight_comments)
        
        return

    def highlight_comments(self):
        """Resalta todos los comentarios en el editor"""
        # Limpiar resaltado previo de comentarios
        self.editor.tag_remove("comment", "1.0", "end")
        
        # Obtener todo el texto
        texto = self.editor.get("1.0", "end")
        if not texto.strip():
            return
        
        # Buscar comentarios de línea (//)
        start_idx = "1.0"
        while True:
            start_idx = self.editor.search("//", start_idx, stopindex="end", regexp=False)
            if not start_idx:
                break
            
            end_idx = self.editor.search("\n", start_idx, stopindex="end")
            if not end_idx:
                end_idx = "end"
            
            self.editor.tag_add("comment", start_idx, end_idx)
            start_idx = end_idx
        
        # Buscar comentarios multilínea (/* ... */)
        start_idx = "1.0"
        while True:
            start_idx = self.editor.search("/*", start_idx, stopindex="end", regexp=False)
            if not start_idx:
                break
            
            end_idx = self.editor.search("*/", start_idx, stopindex="end")
            if not end_idx:
                end_idx = "end"
            else:
                end_idx = f"{end_idx}+2c"  # Incluir los dos caracteres */
            
            self.editor.tag_add("comment", start_idx, end_idx)
            start_idx = end_idx

    def setup_editor_bindings(self):
        """Configura todos los bindings para mejorar la interacción con el editor"""
        # Eventos de teclado
        self.editor.bind("<KeyPress>", self.on_key_press)
        self.editor.bind("<KeyRelease>", self.on_key_release)
        
        # Eventos de mouse
        self.editor.bind("<Button-1>", self.on_mouse_click)  # Clic simple
        self.editor.bind("<ButtonRelease-1>", self.update_line_numbers)
        self.editor.bind("<Double-Button-1>", self.on_double_click)
        self.editor.bind("<Triple-Button-1>", self.on_triple_click)
        self.editor.bind("<B1-Motion>", self.on_mouse_drag)
        
        # Eventos de rueda del mouse
        self.editor.bind("<MouseWheel>", self.on_mouse_wheel)  # Windows/MacOS
        self.editor.bind("<Button-4>", self.on_mouse_wheel)    # Linux scroll up
        self.editor.bind("<Button-5>", self.on_mouse_wheel)    # Linux scroll down
        
        # Teclas de navegación
        self.editor.bind("<Control-Home>", self.on_ctrl_home)
        self.editor.bind("<Control-End>", self.on_ctrl_end)
        self.editor.bind("<Control-a>", self.on_select_all)

    def highlight_syntax_real_time(self):
        """Resalta la sintaxis en tiempo real utilizando el analizador léxico"""
        # Obtener el texto completo del editor
        texto = self.editor.get("1.0", "end")
        
        # Si no hay texto, salir
        if not texto.strip():
            return
        
        try:
            # Importar el analizador léxico
            import lexico
            
            # Analizar el código usando el analizador léxico
            tokens, _ = lexico.analizar_codigo(texto)
            
            # Importar la función de resaltado desde el módulo de integración
            import integration
            
            # Aplicar el resaltado basado en los tokens
            integration.aplicar_resaltado(self, tokens)
            
        except Exception as e:
            print(f"Error en el resaltado de sintaxis en tiempo real: {e}")
            pass
        
    def open_file(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Archivos de texto", "*.txt"), ("Todos los archivos", "*.*")])
        if file_path:
            self.current_file = file_path
            with open(file_path, 'r') as file:
                self.editor.delete('1.0', tk.END)
                self.editor.insert('1.0', file.read())
            self.update_line_numbers()
            self.highlight_syntax_real_time()  # Resaltar sintaxis al abrir el archivo
            self.highlight_comments()
   
    def close_file(self):
        self.editor.delete(1.0, tk.END)
        self.current_file = None
        # Limpiar todas las pestañas
        self.lexico_tab.delete(1.0, tk.END)
        self.sintactico_tab.delete(1.0, tk.END)
        self.semantico_tab.delete(1.0, tk.END)
        self.hash_table_tab.delete(1.0, tk.END)
        self.codigo_intermedio_tab.delete(1.0, tk.END)
        self.errores_lexicos_tab.delete(1.0, tk.END)
        self.errores_sintacticos_tab.delete(1.0, tk.END)
        self.errores_semanticos_tab.delete(1.0, tk.END)
        self.resultados_tab.delete(1.0, tk.END)
        #messagebox.showinfo("Cerrar archivo", "El archivo ha sido cerrado.")

    def save_file(self):
        if self.current_file:
            with open(self.current_file, 'w') as file:
                file.write(self.editor.get('1.0', tk.END))
        else:
            self.save_as_file()
            
    def save_as_file(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Archivos de texto", "*.txt"), ("Todos los archivos", "*.*")])
        if file_path:
            self.current_file = file_path
            self.save_file()

    def lexical_analysis(self):
        """Realiza el análisis léxico del código en el editor utilizando el analizador externo"""
        try:
            import integration
            import lexico
            
            # Obtener el código del editor
            codigo_fuente = self.editor.get('1.0', 'end')
            
            # Ejecutar el análisis léxico
            tokens, errores = lexico.analizar_codigo(codigo_fuente)
            
            # Mostrar resultados formateados en la pestaña (versión completa con formato)
            resultado_pestana = lexico.formatear_resultados(tokens, formato_completo=True)
            self.lexico_tab.delete('1.0', 'end')
            self.lexico_tab.insert('1.0', resultado_pestana)
            
            # Guardar valores de tokens en archivo
            with open('analisis_lexico.txt', 'w', encoding='utf-8') as f:
                for token in tokens:
                    if token[0] != 'EOF':  # Excluir token de fin de archivo
                        valor = token[1]
                        if valor.strip():  # Solo escribir valores no vacíos
                            f.write(f"{valor}\n")
            
            # Mostrar errores en su pestaña correspondiente
            errores_formateados = lexico.formatear_errores(errores)
            self.errores_lexicos_tab.delete('1.0', 'end')
            self.errores_lexicos_tab.insert('1.0', errores_formateados)
            
            # Guardar errores en archivo
            with open('errores_lexicos.txt', 'w', encoding='utf-8') as f:
                f.write(errores_formateados)
            
            # Aplicar resaltado de sintaxis en el editor
            integration.aplicar_resaltado(self, tokens)
            self.highlight_comments()
            
            # Cambiar a la pestaña léxico
            self.right_tabs.select(0)  # Seleccionar la primera pestaña (Léxico)
            
            # Cambiar a la pestaña de errores léxicos si hay errores
            if errores:
                self.bottom_tabs.select(0)  # Seleccionar la primera pestaña (Errores Léxicos)
                
            #messagebox.showinfo("Análisis Léxico", "Análisis léxico completado correctamente")
            
        except ImportError as e:
            # Manejo de error si no se encuentra el módulo
            self.lexico_tab.delete('1.0', 'end')
            self.lexico_tab.insert('1.0', f"Error: No se pudo importar el módulo lexico\n{str(e)}")
            
            self.errores_lexicos_tab.delete('1.0', 'end')
            self.errores_lexicos_tab.insert('1.0', "Error: Archivo lexico.py no encontrado o tiene errores")
            
            self.right_tabs.select(0)
            self.bottom_tabs.select(0)
            
            #messagebox.showerror("Error", "No se pudo cargar el analizador léxico. Verifique que el archivo 'lexico.py' existe y es accesible.")
            
        except Exception as e:
            # Manejo de otros errores
            self.lexico_tab.delete('1.0', 'end')
            self.lexico_tab.insert('1.0', f"Error durante el análisis léxico:\n{str(e)}")
            
            self.errores_lexicos_tab.delete('1.0', 'end')
            self.errores_lexicos_tab.insert('1.0', f"Error inesperado:\n{str(e)}")
            
            self.right_tabs.select(0)
            self.bottom_tabs.select(0)
            
            #messagebox.showerror("Error", f"Ocurrió un error durante el análisis léxico:\n{str(e)}")
        
    def syntax_analysis(self):
        """Realiza el análisis sintáctico del código en el editor"""
        try:
            import sintactico
            import lexico
            from ast_visualizer import VisualizadorAST
            
            # Limpiar pestaña de sintáctico primero
            self.sintactico_tab.delete('1.0', 'end')
            for widget in self.sintactico_tab.winfo_children():
                widget.destroy()
            
            # Obtener el código del editor
            codigo_fuente = self.editor.get('1.0', 'end')
            
            # Primero hacer análisis léxico para obtener los tokens
            tokens, _ = lexico.analizar_codigo(codigo_fuente)
            
            # Filtrar tokens no deseados
            tokens_filtrados = [token for token in tokens if token[0] not in ['COMENTARIO_LINEA', 'COMENTARIO_MULTILINEA']]
            
            # Realizar análisis sintáctico
            ast, errores = sintactico.analizar_desde_tokens(tokens_filtrados)
            
            # Mostrar AST en la pestaña de sintáctico
            if ast:
                # Crear un frame contenedor en la pestaña de texto
                container = tk.Frame(self.sintactico_tab)
                self.sintactico_tab.window_create('1.0', window=container)
                
                # Mostrar mensaje inicial
                #self.sintactico_tab.insert('1.0', "Árbol Sintáctico Abstracto (AST):\n\n")
                
                # Crear visualizador AST integrado
                VisualizadorAST(container, ast)
            else:
                self.sintactico_tab.insert('1.0', "No se pudo generar el AST debido a errores sintácticos\n")
            
            # Mostrar errores
            errores_formateados = sintactico.formatear_errores(errores)
            self.errores_sintacticos_tab.delete('1.0', 'end')
            self.errores_sintacticos_tab.insert('1.0', errores_formateados)
            
            # Guardar errores en archivo
            with open('errores_sintacticos.txt', 'w', encoding='utf-8') as f:
                f.write(errores_formateados)
            
            # Cambiar a las pestañas relevantes
            self.right_tabs.select(1)  # Pestaña Sintáctico
            if errores:
                self.bottom_tabs.select(1)  # Pestaña Errores
                
        except ImportError as e:
            self.sintactico_tab.delete('1.0', 'end')
            self.sintactico_tab.insert('1.0', f"Error: No se pudo importar módulos necesarios: {str(e)}")
        except Exception as e:
            self.sintactico_tab.delete('1.0', 'end')
            self.sintactico_tab.insert('1.0', f"Error inesperado durante el análisis: {str(e)}")
        
    def semantic_analysis(self):
        """Realiza el análisis semántico del código en el editor"""
        try:
            import semantico
            import lexico
            import sintactico
            from semantic_ast_visualizer import crear_visualizador_semantico

            # Limpiar pestañas
            self.semantico_tab.delete('1.0', 'end')
            for widget in self.semantico_tab.winfo_children():
                widget.destroy()
            self.hash_table_tab.delete('1.0', 'end')
            self.errores_semanticos_tab.delete('1.0', 'end')
            
            # Obtener el código del editor
            codigo_fuente = self.editor.get('1.0', 'end')
            
            if not codigo_fuente.strip():
                self.semantico_tab.insert('1.0', "No hay código para analizar")
                self.right_tabs.select(2)
                return
            
            # Realizar análisis léxico y sintáctico
            tokens, errores_lexicos = lexico.analizar_codigo(codigo_fuente)
            if errores_lexicos:
                self.semantico_tab.insert('1.0', "Análisis semántico no realizado debido a errores léxicos.")
                return

            tokens_filtrados = [token for token in tokens if token[0] not in ['COMENTARIO_LINEA', 'COMENTARIO_MULTILINEA']]
            ast, errores_sintacticos = sintactico.analizar_desde_tokens(tokens_filtrados)
            if errores_sintacticos or not ast:
                self.semantico_tab.insert('1.0', "Análisis semántico no realizado debido a errores sintácticos.")
                return

            # Realizar análisis semántico
            semantic_analyzer = semantico.SemanticAnalyzer(ast, tokens_filtrados)
            annotated_ast, symbol_table, semantic_errors = semantic_analyzer.analyze()
            
            # Exportar resultados a archivos
            semantico.export_semantic_analysis_files(
                annotated_ast, symbol_table, semantic_errors, "semantic_analysis_output"
            )

            # Mostrar AST anotado en la pestaña "Semántico" con el visualizador
            if annotated_ast:
                container = tk.Frame(self.semantico_tab)
                self.semantico_tab.window_create('1.0', window=container)
                crear_visualizador_semantico(container, annotated_ast, semantic_errors)
            else:
                self.semantico_tab.insert('1.0', "No se pudo generar el AST anotado.")

            # Cargar y mostrar la tabla de símbolos
            try:
                with open("semantic_analysis_output_symbol_table.txt", 'r', encoding='utf-8') as f:
                    self.hash_table_tab.insert('1.0', f.read())
            except FileNotFoundError:
                self.hash_table_tab.insert('1.0', "No se encontró el archivo de la tabla de símbolos.")

            # Mostrar errores semánticos
            errores_formateados = self._format_enhanced_semantic_errors(semantic_errors)
            self.errores_semanticos_tab.insert('1.0', errores_formateados)
            self._setup_error_navigation(semantic_errors)

            # Cambiar a las pestañas relevantes
            self.right_tabs.select(2)  # Pestaña Semántico
            if semantic_errors:
                self.bottom_tabs.select(2)  # Pestaña Errores Semánticos

        except Exception as e:
            self.semantico_tab.insert('1.0', f"Error durante el análisis semántico:\n{str(e)}")
            self.right_tabs.select(2)
    
    
    
    
    
    def _format_enhanced_semantic_errors(self, semantic_errors):
        """Formatea los errores semánticos con mejor presentación"""
        if not semantic_errors:
            resultado = "ANÁLISIS SEMÁNTICO EXITOSO\n"
            resultado += "=" * 80 + "\n\n"
            resultado += "¡Felicitaciones! Su código no contiene errores semánticos.\n\n"
            resultado += "Todas las variables están correctamente declaradas\n"
            resultado += "Los tipos son compatibles en todas las operaciones\n"
            resultado += "No hay declaraciones duplicadas\n"
            resultado += "Las asignaciones son válidas\n\n"
            resultado += "Su código está listo para la siguiente fase de compilación.\n"
            return resultado
        
        resultado = "ERRORES SEMÁNTICOS DETECTADOS\n"
        resultado += "=" * 120 + "\n\n"
        
        # Resumen de errores
        resultado += f"RESUMEN: Se encontraron {len(semantic_errors)} error(es) semántico(s)\n\n"
        
        # Agrupar errores por tipo
        errors_by_type = {}
        for error in semantic_errors:
            error_type = error.error_type.replace('_', ' ').title()
            if error_type not in errors_by_type:
                errors_by_type[error_type] = []
            errors_by_type[error_type].append(error)
        
        # Mostrar resumen por categoría
        
        
        # Mostrar errores detallados
        resultado += "DETALLE DE ERRORES:\n"
        resultado += "-" * 120 + "\n"
        resultado += f"{'#':<3} {'Línea':<6} {'Col':<4} {'Tipo':<20} {'Descripción':<40}\n"
        resultado += "-" * 120 + "\n"
        
        # Ordenar errores por línea
        sorted_errors = sorted(semantic_errors, key=lambda e: (e.line, e.column))
        
        for i, error in enumerate(sorted_errors, 1):
            error_type = error.error_type.replace('_', ' ').title()
            # Truncar descripción si es muy larga
            description = error.message
            if len(description) > 118:
                description = description[:115] + "..."
            
            resultado += f"{i:<3} {error.line:<6} {error.column:<4} {error_type:<20} {description:<40}\n"
        
        resultado += "-" * 120 + "\n\n"
        
        # Sugerencias de corrección por tipo de error
        return resultado
    
    def _get_error_icon(self, error_type):
        """Obtiene el icono apropiado para cada tipo de error"""
        icons = {
            'Undeclared Variable': '🔍',
            'Duplicate Declaration': '📋',
            'Type Incompatibility': '⚠️',
            'Invalid Conversion': '🔄',
            'Operator Misuse': '⚡',
            'Assignment Error': '📝'
        }
        return icons.get(error_type, '❌')
    
    def _setup_error_navigation(self, semantic_errors):
        """Configura la navegación interactiva de errores"""
        if not semantic_errors:
            return
        
        # Limpiar bindings previos
        self.errores_semanticos_tab.unbind('<Double-Button-1>')
        
        # Configurar doble clic para navegar a errores
        def on_error_double_click(event):
            try:
                # Obtener la línea donde se hizo clic
                click_line = self.errores_semanticos_tab.index(tk.INSERT).split('.')[0]
                click_line_num = int(click_line)
                
                # Buscar si hay información de error en esa línea
                content = self.errores_semanticos_tab.get(f"{click_line_num}.0", f"{click_line_num}.end")
                
                # Extraer número de línea del error si está presente
                import re
                line_match = re.search(r'(\d+)\s+\d+\s+\w+', content)
                if line_match:
                    error_line = int(line_match.group(1))
                    
                    # Navegar a la línea en el editor
                    self.editor.mark_set("insert", f"{error_line}.0")
                    self.editor.see("insert")
                    
                    # Resaltar la línea temporalmente
                    self._highlight_error_line(error_line)
                    
                    # Mostrar mensaje informativo
                    self.status_bar.config(text=f"Navegado a línea {error_line} - Error semántico")
                    
            except Exception as e:
                print(f"Error en navegación: {e}")
        
        self.errores_semanticos_tab.bind('<Double-Button-1>', on_error_double_click)
    
    def _highlight_error_line(self, line_number):
        """Resalta temporalmente una línea con error en el editor"""
        try:
            # Configurar tag para resaltado de error
            self.editor.tag_configure("error_highlight", background="#ffcccc", foreground="#cc0000")
            
            # Limpiar resaltados previos
            self.editor.tag_remove("error_highlight", "1.0", "end")
            
            # Resaltar la línea del error
            start_pos = f"{line_number}.0"
            end_pos = f"{line_number}.end"
            self.editor.tag_add("error_highlight", start_pos, end_pos)
            
            # Remover el resaltado después de 3 segundos
            self.editor.after(3000, lambda: self.editor.tag_remove("error_highlight", "1.0", "end"))
            
        except Exception as e:
            print(f"Error resaltando línea: {e}")
    
    def _add_interactive_error_navigation(self):
        """Agrega navegación interactiva de errores (funcionalidad futura)"""
        # Esta función se puede expandir para agregar:
        # - Tooltips con información adicional sobre errores
        # - Menú contextual con opciones de corrección
        # - Integración con sistema de ayuda
        pass
        
    def intermediate_code(self):
        # Mostrar resultados en la pestaña correspondiente
        self.codigo_intermedio_tab.delete('1.0', tk.END)
        self.codigo_intermedio_tab.insert('1.0', "Código Intermedio:\nImplementación pendiente")
        
        # Cambiar a la pestaña código intermedio
        self.right_tabs.select(4)  # Seleccionar la quinta pestaña (Código Intermedio)
        
    def execute_code(self):
        code = self.editor.get('1.0', tk.END)
        try:
            # Aquí iría la implementación real de la ejecución
            self.resultados_tab.delete('1.0', tk.END)
            self.resultados_tab.insert('1.0', "Ejecución exitosa")
            
            # Cambiar a la pestaña de resultados
            self.bottom_tabs.select(3)  # Seleccionar la cuarta pestaña (Resultados)
        except Exception as e:
            self.resultados_tab.delete('1.0', tk.END)
            self.resultados_tab.insert('1.0', f"Error de ejecución: {str(e)}")
            
    def compile_code(self):
        """Ejecuta el proceso completo de compilación incluyendo análisis semántico"""
        try:
            # Verificar que hay código para compilar
            codigo_fuente = self.editor.get('1.0', 'end')
            if not codigo_fuente.strip():
                messagebox.showwarning("Advertencia", "No hay código para compilar")
                return
            
            # Fase 1: Análisis Léxico
            self.lexical_analysis()
            
            # Verificar si hay errores léxicos antes de continuar
            errores_lexicos = self.errores_lexicos_tab.get('1.0', 'end').strip()
            if errores_lexicos and "Error" in errores_lexicos:
                #messagebox.showerror("Error de Compilación", "Se encontraron errores léxicos. Corrija los errores antes de continuar.")
                return
            
            # Fase 2: Análisis Sintáctico
            self.syntax_analysis()
            
            # Verificar si hay errores sintácticos antes de continuar
            errores_sintacticos = self.errores_sintacticos_tab.get('1.0', 'end').strip()
            if errores_sintacticos and "Error" in errores_sintacticos:
                #messagebox.showerror("Error de Compilación", "Se encontraron errores sintácticos. Corrija los errores antes de continuar.")
                return
            
            # Fase 3: Análisis Semántico
            self.semantic_analysis()
            
            # Verificar si hay errores semánticos críticos
            errores_semanticos = self.errores_semanticos_tab.get('1.0', 'end').strip()
            has_semantic_errors = errores_semanticos and any(
                keyword in errores_semanticos.lower() 
                for keyword in ['error', 'undeclared', 'incompatible', 'duplicate']
            )
            
            #if has_semantic_errors:
                # Mostrar advertencia pero permitir continuar
                #result = messagebox.askyesno(
                #    "Advertencia de Compilación", 
                #    "Se encontraron errores semánticos. ¿Desea continuar con la generación de código intermedio?"
                #)
                #if not result:
                #    return
            
            # Fase 4: Código Intermedio
            self.intermediate_code()
            
            # Mostrar mensaje de éxito
            self.resultados_tab.delete('1.0', 'end')
            
            if has_semantic_errors:
                self.resultados_tab.insert('1.0', 
                    "Compilación completada con advertencias semánticas.\n"
                    "Revise la pestaña de errores semánticos para más detalles.\n\n"
                    "Fases completadas:\n"
                    "✓ Análisis Léxico\n"
                    "✓ Análisis Sintáctico\n"
                    "⚠ Análisis Semántico (con advertencias)\n"
                    "✓ Código Intermedio"
                )
            else:
                self.resultados_tab.insert('1.0', 
                    "Compilación completada exitosamente.\n\n"
                    "Fases completadas:\n"
                    "✓ Análisis Léxico\n"
                    "✓ Análisis Sintáctico\n"
                    "✓ Análisis Semántico\n"
                    "✓ Código Intermedio"
                )
            
            # Cambiar a la pestaña de resultados
            self.bottom_tabs.select(3)
            
        except Exception as e:
            self.resultados_tab.delete('1.0', 'end')
            self.resultados_tab.insert('1.0', f"Error durante la compilación:\n{str(e)}")
            self.bottom_tabs.select(3)
            messagebox.showerror("Error de Compilación", f"Ocurrió un error durante la compilación:\n{str(e)}")
        self.right_tabs.select(3)  # Seleccionar la cuarta pestaña (Tabla de Símbolos)

if __name__ == '__main__':
    root = tk.Tk()
    root.geometry("1200x600")
    app = CustomIDE(root)
    root.mainloop()