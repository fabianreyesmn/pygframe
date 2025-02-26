import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkinter.scrolledtext import ScrolledText
from PIL import Image, ImageTk
import re

class CustomIDE:
    def __init__(self, root):
        self.root = root
        self.root.title("PyGFrame")
        
        # Configurar tema oscuro
        self.style = ttk.Style()
        self.style.configure(".", 
            background='#1e1e1e',
            foreground='#d4af37',  # Dorado
            fieldbackground='#1e1e1e'
        )
        
        self.root.configure(bg='#1e1e1e')
        self.current_file = None
        
        self.create_menu()
        self.create_toolbar()
        self.create_main_interface()
        
        # Configurar el seguimiento de posición del cursor
        self.editor.bind('<KeyRelease>', self.update_cursor_position)
        self.editor.bind('<Button-1>', self.update_cursor_position)
        
    def create_menu(self):
        menubar = tk.Menu(self.root, bg='#2d2d2d', fg='#d4af37')
        self.root.config(menu=menubar)
        
        # Menú Archivo
        file_menu = tk.Menu(menubar, tearoff=0, bg='#2d2d2d', fg='#d4af37')
        menubar.add_cascade(label="Archivo", menu=file_menu)
        file_menu.add_command(label="Abrir", command=self.open_file)
        file_menu.add_command(label="Cerrar archivo", command=self.close_file)
        file_menu.add_command(label="Guardar", command=self.save_file)
        file_menu.add_command(label="Guardar como", command=self.save_as_file)
        file_menu.add_separator()
        file_menu.add_command(label="Salir", command=self.root.quit)
        
        # Menú Análisis
        analysis_menu = tk.Menu(menubar, tearoff=0, bg='#2d2d2d', fg='#d4af37')
        menubar.add_cascade(label="Análisis", menu=analysis_menu)
        analysis_menu.add_command(label="Análisis Léxico", command=self.lexical_analysis)
        analysis_menu.add_command(label="Análisis Sintáctico", command=self.syntax_analysis)
        analysis_menu.add_command(label="Análisis Semántico", command=self.semantic_analysis)
        analysis_menu.add_command(label="Código Intermedio", command=self.intermediate_code)
        analysis_menu.add_command(label="Ejecutar", command=self.execute_code)
        
    def create_toolbar(self):
        toolbar = ttk.Frame(self.root, style='Toolbar.TFrame')
        toolbar.pack(fill=tk.X, padx=5, pady=5)
        
        # Cargar imágenes
        self.open_icon = tk.PhotoImage(file="images/open_icon.png")
        self.save_icon = tk.PhotoImage(file="images/save_icon.png")
        self.compile_icon = tk.PhotoImage(file="images/compile_icon.png")
        self.lexical_icon = tk.PhotoImage(file="images/lexical_icon.png")
        self.syntax_icon = tk.PhotoImage(file="images/syntax_icon.png")
        self.semantic_icon = tk.PhotoImage(file="images/semantic_icon.png")
        self.intermediate_icon = tk.PhotoImage(file="images/intermediate_icon.png")
        self.execute_icon = tk.PhotoImage(file="images/execute_icon.png")

        # Configurar estilo de botones
        self.style.configure('Toolbar.TButton',
            background='#2d2d2d',
            foreground='#5d5d3d',
            padding=5
        )
    
    # Crear botones
        ttk.Button(toolbar, image=self.open_icon, text="Abrir", command=self.open_file, style='Toolbar.TButton', compound=tk.LEFT).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, image=self.save_icon, text="Guardar", command=self.save_file, style='Toolbar.TButton', compound=tk.LEFT).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, image=self.compile_icon, text="Compilar", command=self.compile_code, style='Toolbar.TButton', compound=tk.LEFT).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, image=self.lexical_icon, text="A. Léxico", command=self.lexical_analysis, style='Toolbar.TButton', compound=tk.LEFT).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, image=self.syntax_icon, text="A. Sintáctico", command=self.syntax_analysis, style='Toolbar.TButton', compound=tk.LEFT).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, image=self.semantic_icon, text="A. Semántico", command=self.semantic_analysis, style='Toolbar.TButton', compound=tk.LEFT).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, image=self.intermediate_icon, text="C. Intermedio", command=self.intermediate_code, style='Toolbar.TButton', compound=tk.LEFT).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, image=self.execute_icon, text="Ejecutar", command=self.execute_code, style='Toolbar.TButton', compound=tk.LEFT).pack(side=tk.LEFT, padx=2)


    
    def create_main_interface(self):
        # Contenedor principal para organizar el diseño
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Crear barra de estado primero para que esté en la parte inferior
        status_frame = ttk.Frame(main_container, height=25)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.status_bar = ttk.Label(status_frame, text="Líneas: 1, Columnas: 1",
                                  background='#2d2d2d', foreground='#d4af37',
                                  padding=(5, 0))
        self.status_bar.pack(side=tk.LEFT, fill=tk.X)
        
        # Panel principal para el área de trabajo
        main_panel = ttk.PanedWindow(main_container, orient=tk.HORIZONTAL)
        main_panel.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        
        # Panel izquierdo (editor)
        left_frame = ttk.Frame(main_panel)
        main_panel.add(left_frame, weight=1)
        

        # Editor con números de línea
        self.line_numbers = tk.Text(left_frame, width=4, padx=3, takefocus=0, border=0,
                                  background='#2d2d2d', foreground='#d4af37',
                                  state='disabled')
        self.line_numbers.pack(side=tk.LEFT, fill=tk.Y)
        
        self.editor = ScrolledText(left_frame, wrap=tk.WORD, undo=True,
                                 background='#1e1e1e', foreground='#d4af37',
                                 insertbackground='#d4af37')
        self.editor.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        

        # Panel derecho (resultados con pestañas)
        right_frame = ttk.Frame(main_panel)
        main_panel.add(right_frame, weight=1)
        
        # Crear pestañas para la parte derecha
        self.right_tabs = ttk.Notebook(right_frame)
        self.right_tabs.pack(fill=tk.BOTH, expand=True)
        
        # Configurar estilo para pestañas
        self.style.configure('TNotebook.Tab', background='#2d2d2d', foreground='#5d5d3d', padding=[10, 2])
        self.style.map('TNotebook.Tab', 
                      background=[('selected', '#3d3d3d')],
                      foreground=[('selected', '#d4af37')])
        
        # Crear las pestañas para la parte derecha
        self.lexico_tab = ScrolledText(self.right_tabs, wrap=tk.WORD, background='#1e1e1e', foreground='#d4af37')
        self.sintactico_tab = ScrolledText(self.right_tabs, wrap=tk.WORD, background='#1e1e1e', foreground='#d4af37')
        self.semantico_tab = ScrolledText(self.right_tabs, wrap=tk.WORD, background='#1e1e1e', foreground='#d4af37')
        self.hash_table_tab = ScrolledText(self.right_tabs, wrap=tk.WORD, background='#1e1e1e', foreground='#d4af37')
        self.codigo_intermedio_tab = ScrolledText(self.right_tabs, wrap=tk.WORD, background='#1e1e1e', foreground='#d4af37')
        
        # Añadir pestañas al notebook
        self.right_tabs.add(self.lexico_tab, text="Léxico")
        self.right_tabs.add(self.sintactico_tab, text="Sintáctico")
        self.right_tabs.add(self.semantico_tab, text="Semántico")
        self.right_tabs.add(self.hash_table_tab, text="Hash Table")
        self.right_tabs.add(self.codigo_intermedio_tab, text="Código Intermedio")
        

        # Panel inferior con pestañas para errores
        bottom_frame = ttk.Frame(main_container)
        bottom_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Crear pestañas para la parte inferior
        self.bottom_tabs = ttk.Notebook(bottom_frame)
        self.bottom_tabs.pack(fill=tk.BOTH, expand=True)
        
        # Crear las pestañas para la parte inferior
        self.errores_lexicos_tab = ScrolledText(self.bottom_tabs, height=10, wrap=tk.WORD, background='#1e1e1e', foreground='#ff6b6b')
        self.errores_sintacticos_tab = ScrolledText(self.bottom_tabs, height=10, wrap=tk.WORD, background='#1e1e1e', foreground='#ff6b6b')
        self.errores_semanticos_tab = ScrolledText(self.bottom_tabs, height=10, wrap=tk.WORD, background='#1e1e1e', foreground='#ff6b6b')
        self.resultados_tab = ScrolledText(self.bottom_tabs, height=10, wrap=tk.WORD, background='#1e1e1e', foreground='#d4af37')
        
        # Añadir pestañas al notebook
        self.bottom_tabs.add(self.errores_lexicos_tab, text="Errores Léxicos")
        self.bottom_tabs.add(self.errores_sintacticos_tab, text="Errores Sintácticos")
        self.bottom_tabs.add(self.errores_semanticos_tab, text="Errores Semánticos")
        self.bottom_tabs.add(self.resultados_tab, text="Resultados")
        
        self.update_line_numbers()
        self.editor.bind('<Key>', self.update_line_numbers)
        self.editor.bind('<MouseWheel>', self.update_line_numbers)
        
    def update_line_numbers(self, event=None):
        lines = self.editor.get('1.0', tk.END).count('\n')
        line_numbers_text = '\n'.join(str(i) for i in range(1, lines + 1))
        self.line_numbers.config(state='normal')
        self.line_numbers.delete('1.0', tk.END)
        self.line_numbers.insert('1.0', line_numbers_text)
        self.line_numbers.config(state='disabled')
        
    def update_cursor_position(self, event=None):
        position = self.editor.index(tk.INSERT)
        line, column = position.split('.')
        self.status_bar.config(text=f"Líneas: {line}, Columnas: {int(column) + 1}")
        
    def open_file(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Archivos de texto", "*.txt"), ("Todos los archivos", "*.*")])
        if file_path:
            self.current_file = file_path
            with open(file_path, 'r') as file:
                self.editor.delete('1.0', tk.END)
                self.editor.insert('1.0', file.read())
            self.update_line_numbers()
            self.close_file_button["state"] = tk.NORMAL

   
    def close_file(self):
        self.editor.delete(1.0, tk.END)
        self.current_file = None
        self.output.delete(1.0, tk.END)
        self.error_output.delete(1.0, tk.END)
        messagebox.showinfo("Cerrar archivo", "El archivo ha sido cerrado.")

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
        code = self.editor.get('1.0', tk.END)
        # Ejemplo simple de análisis léxico
        tokens = []
        current_token = ""
        for char in code:
            if char.isspace():
                if current_token:
                    tokens.append(current_token)
                    current_token = ""
            else:
                current_token += char
        if current_token:
            tokens.append(current_token)
            
        # Mostrar resultados en la pestaña correspondiente
        self.lexico_tab.delete('1.0', tk.END)
        self.lexico_tab.insert('1.0', "Análisis Léxico:\n" + "\n".join(tokens))
        
        # Cambiar a la pestaña léxico
        self.right_tabs.select(0)  # Seleccionar la primera pestaña (Léxico)
        
        # Simular algunos errores léxicos
        self.errores_lexicos_tab.delete('1.0', tk.END)
        self.errores_lexicos_tab.insert('1.0', "No se encontraron errores léxicos")
        
        # Cambiar a la pestaña de errores léxicos
        self.bottom_tabs.select(0)  # Seleccionar la primera pestaña (Errores Léxicos)
        
    def syntax_analysis(self):
        # Mostrar resultados en la pestaña correspondiente
        self.sintactico_tab.delete('1.0', tk.END)
        self.sintactico_tab.insert('1.0', "Análisis Sintáctico:\nImplementación pendiente")
        
        # Cambiar a la pestaña sintáctico
        self.right_tabs.select(1)  # Seleccionar la segunda pestaña (Sintáctico)
        
        # Simular algunos errores sintácticos
        self.errores_sintacticos_tab.delete('1.0', tk.END)
        self.errores_sintacticos_tab.insert('1.0', "No se encontraron errores sintácticos")
        
        # Cambiar a la pestaña de errores sintácticos
        self.bottom_tabs.select(1)  # Seleccionar la segunda pestaña (Errores Sintácticos)
        
    def semantic_analysis(self):
        # Mostrar resultados en la pestaña correspondiente
        self.semantico_tab.delete('1.0', tk.END)
        self.semantico_tab.insert('1.0', "Análisis Semántico:\nImplementación pendiente")
        
        # Cambiar a la pestaña semántico
        self.right_tabs.select(2)  # Seleccionar la tercera pestaña (Semántico)
        
        # Simular algunos errores semánticos
        self.errores_semanticos_tab.delete('1.0', tk.END)
        self.errores_semanticos_tab.insert('1.0', "No se encontraron errores semánticos")
        
        # Cambiar a la pestaña de errores semánticos
        self.bottom_tabs.select(2)  # Seleccionar la tercera pestaña (Errores Semánticos)
        
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
        self.lexical_analysis()
        self.syntax_analysis()
        self.semantic_analysis()
        self.intermediate_code()
        
        # Ejemplo simple de tabla hash
        self.hash_table_tab.delete('1.0', tk.END)
        self.hash_table_tab.insert('1.0', "Tabla Hash:\n\nID\t|\tTipo\t|\tValor\n" + 
                                 "-" * 40 + "\n" +
                                 "var1\t|\tint\t|\t10\n" +
                                 "var2\t|\tstring\t|\t\"texto\"\n" +
                                 "func1\t|\tfunción\t|\tvoid")
        
        # Cambiar a la pestaña hash table
        self.right_tabs.select(3)  # Seleccionar la cuarta pestaña (Hash Table)

if __name__ == '__main__':
    root = tk.Tk()
    root.geometry("1200x800")
    app = CustomIDE(root)
    root.mainloop()