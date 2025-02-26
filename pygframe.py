import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkinter.scrolledtext import ScrolledText
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
        
        # Configurar estilo de botones
        self.style.configure('Toolbar.TButton',
            background='#2d2d2d',
            foreground='#5d5d3d',
            #foreground='#a17c04',
            #foreground='#d4af37',
            padding=5
        )
        
        # Crear botones
        ttk.Button(toolbar, text="Abrir", command=self.open_file, style='Toolbar.TButton').pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Guardar", command=self.save_file, style='Toolbar.TButton').pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Compilar", command=self.compile_code, style='Toolbar.TButton').pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="A. Léxico", command=self.lexical_analysis, style='Toolbar.TButton').pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="A. Sintáctico", command=self.syntax_analysis, style='Toolbar.TButton').pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="A. Semántico", command=self.semantic_analysis, style='Toolbar.TButton').pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="C. Intermedio", command=self.intermediate_code, style='Toolbar.TButton').pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Ejecutar", command=self.execute_code, style='Toolbar.TButton').pack(side=tk.LEFT, padx=2)
        
    def create_main_interface(self):
        # Panel principal
        main_panel = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
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
        
        # Panel derecho (resultados)
        right_frame = ttk.Frame(main_panel)
        main_panel.add(right_frame, weight=1)
        
        self.output = ScrolledText(right_frame, height=20, wrap=tk.WORD,
                                 background='#1e1e1e', foreground='#d4af37')
        self.output.pack(fill=tk.BOTH, expand=True)
        
        # Panel inferior
        bottom_frame = ttk.Frame(self.root)
        bottom_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Área de errores y tabla de símbolos
        self.error_output = ScrolledText(bottom_frame, height=10, wrap=tk.WORD,
                                       background='#1e1e1e', foreground='#ff6b6b')
        self.error_output.pack(fill=tk.BOTH, expand=True)
        
        # Barra de estado para posición del cursor
        self.status_bar = ttk.Label(self.root, text="Línea: 1, Columna: 1",
                                  background='#2d2d2d', foreground='#d4af37')
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
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
        self.status_bar.config(text=f"Línea: {line}, Columna: {int(column) + 1}")
        
    def open_file(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Archivos de texto", "*.txt"), ("Todos los archivos", "*.*")])
        if file_path:
            self.current_file = file_path
            with open(file_path, 'r') as file:
                self.editor.delete('1.0', tk.END)
                self.editor.insert('1.0', file.read())
            self.update_line_numbers()
            
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
            
        self.output.delete('1.0', tk.END)
        self.output.insert('1.0', "Análisis Léxico:\n" + "\n".join(tokens))
        
    def syntax_analysis(self):
        self.output.delete('1.0', tk.END)
        self.output.insert('1.0', "Análisis Sintáctico:\nImplementación pendiente")
        
    def semantic_analysis(self):
        self.output.delete('1.0', tk.END)
        self.output.insert('1.0', "Análisis Semántico:\nImplementación pendiente")
        
    def intermediate_code(self):
        self.output.delete('1.0', tk.END)
        self.output.insert('1.0', "Código Intermedio:\nImplementación pendiente")
        
    def execute_code(self):
        code = self.editor.get('1.0', tk.END)
        try:
            # Aquí iría la implementación real de la ejecución
            self.error_output.delete('1.0', tk.END)
            self.error_output.insert('1.0', "Ejecución exitosa")
        except Exception as e:
            self.error_output.delete('1.0', tk.END)
            self.error_output.insert('1.0', f"Error de ejecución: {str(e)}")
            
    def compile_code(self):
        self.lexical_analysis()
        self.syntax_analysis()
        self.semantic_analysis()
        self.intermediate_code()

if __name__ == '__main__':
    root = tk.Tk()
    root.geometry("1200x800")
    app = CustomIDE(root)
    root.mainloop()