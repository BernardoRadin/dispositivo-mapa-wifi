import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from collections import defaultdict
from PIL import Image, ImageTk
import os

from core.wifi_scanner import WifiScanner
from core.utils import signal_dbm_to_percent, dbm_to_color
from gui.heatmap import HeatmapGenerator

class WifiMapApp:  
    def __init__(self, root):
        self.root = root
        self.root.title("WiFi Scanner - Mapa de Calor Profissional")
        self.root.geometry("1200x900")
        self.root.configure(bg='#f0f0f0')
        self.setup_styles()
        
        self.scanner = WifiScanner()
        self.heatmap_generator = HeatmapGenerator(root)
        
        self.measurements = defaultdict(dict)
        self.ssid_selecionado = None
        
        self.floorplan_image = None
        self.floorplan_photo = None
        self.floorplan_path = None
        self.image_points = {}
        self.canvas_points = {}
        
        self.point_labels = {}
        self.canvas = None
        self.create_widgets()

    def setup_styles(self):
        style = ttk.Style()
        
        try:
            style.theme_use('clam')
        except:
            pass
        
        self.colors = {
            'primary': '#007acc',
            'secondary': '#f8f9fa',
            'success': '#28a745',
            'warning': '#ffc107',
            'danger': '#dc3545',
            'info': '#17a2b8',
            'light': '#f8f9fa',
            'dark': '#343a40',
            'white': '#ffffff',
            'gray': '#6c757d'
        }
        
        style.configure('TButton', 
                       font=('Segoe UI', 11, 'bold'),
                       padding=(15, 8),
                       relief='flat',
                       borderwidth=0)
        
        style.configure('Primary.TButton',
                       background=self.colors['primary'],
                       foreground=self.colors['white'],
                       borderwidth=0,
                       focuscolor=self.colors['primary'],
                       lightcolor=self.colors['primary'],
                       darkcolor=self.colors['primary'])
        
        style.configure('Success.TButton',
                       background=self.colors['success'],
                       foreground=self.colors['white'],
                       borderwidth=0,
                       focuscolor=self.colors['success'],
                       lightcolor=self.colors['success'],
                       darkcolor=self.colors['success'])
        
        style.configure('Danger.TButton',
                       background=self.colors['danger'],
                       foreground=self.colors['white'],
                       borderwidth=0,
                       focuscolor=self.colors['danger'],
                       lightcolor=self.colors['danger'],
                       darkcolor=self.colors['danger'])
        
        style.map('Primary.TButton',
                 background=[('active', '#0056b3'), ('pressed', '#004085')])
        style.map('Success.TButton', 
                 background=[('active', '#218838'), ('pressed', '#1e7e34')])
        style.map('Danger.TButton',
                 background=[('active', '#c82333'), ('pressed', '#bd2130')])
        
        style.configure('TLabel', 
                       font=('Segoe UI', 10),
                       background=self.colors['light'])
        
        style.configure('Header.TLabel',
                       font=('Segoe UI', 14, 'bold'),
                       foreground=self.colors['dark'])
        
        style.configure('TFrame',
                       background=self.colors['white'])
        
        style.configure('Card.TLabelframe',
                       background=self.colors['white'],
                       relief='solid',
                       borderwidth=1)
        
        style.configure('Card.TLabelframe.Label',
                       font=('Segoe UI', 11, 'bold'),
                       foreground=self.colors['primary'],
                       background=self.colors['white'])
        
        style.configure('TCombobox',
                       font=('Segoe UI', 10),
                       padding=5)
        
        style.configure('Treeview',
                       font=('Segoe UI', 9),
                       rowheight=25,
                       background=self.colors['white'])
        
        style.configure('Treeview.Heading',
                       font=('Segoe UI', 10, 'bold'),
                       background=self.colors['primary'],
                       foreground=self.colors['white'])

    def create_widgets(self):
        main_container = ttk.Frame(self.root, style='Card.TLabelframe')
        main_container.pack(fill='both', expand=True, padx=15, pady=10)
        
        title_label = ttk.Label(main_container, 
                               text="WiFi Scanner - Mapa de Calor com Planta Baixa",
                               style='Header.TLabel')
        title_label.pack(pady=(0, 15))
        
        self._create_top_frame(main_container)
        
        self.status_label = ttk.Label(main_container, 
                                     text="Selecione uma rede Wi-Fi para começar", 
                                     font=('Segoe UI', 11),
                                     foreground=self.colors['info'],
                                     background=self.colors['light'])
        self.status_label.pack(pady=10, fill='x', padx=10)

        content_frame = ttk.Frame(main_container, style='TFrame')
        content_frame.pack(fill='both', expand=True, pady=10)
        
        self._create_left_panel(content_frame)
        
        self._create_right_panel(content_frame)
        
        self.atualizar_redes()
        self.disable_controls()

    def _create_left_panel(self, parent):
        left_panel = ttk.Frame(parent, style='TFrame')
        left_panel.pack(side='left', fill='y', padx=(0, 10))
        
        self._create_image_controls(left_panel)
        
        self._create_points_list(left_panel)

    def _create_right_panel(self, parent):
        right_panel = ttk.LabelFrame(parent, text="Planta Baixa", 
                                    style='Card.TLabelframe', padding=10)
        right_panel.pack(side='right', fill='both', expand=True)
        
        self.canvas = tk.Canvas(right_panel, bg='white', relief='sunken', borderwidth=2)
        self.canvas.pack(fill='both', expand=True)
        
        self.canvas.bind('<Button-1>', self.on_canvas_click)
        
        self.canvas.create_text(300, 200, text="Clique em 'Carregar Imagem' para começar",
                               font=('Segoe UI', 12), fill='gray')

    def _create_image_controls(self, parent):
        image_frame = ttk.LabelFrame(parent, text="Gerenciar Planta Baixa", 
                                    style='Card.TLabelframe', padding=10)
        image_frame.pack(fill='x', pady=(0, 10))
        
        self.btn_load_image = ttk.Button(image_frame, text="Carregar Imagem", 
                                        command=self.load_floorplan_image, style='Primary.TButton')
        self.btn_load_image.pack(fill='x')

    def _create_points_list(self, parent):
        list_frame = ttk.LabelFrame(parent, text="Pontos Medidos", 
                                   style='Card.TLabelframe', padding=10)
        list_frame.pack(fill='both', expand=True)
        
        self.tree = ttk.Treeview(list_frame, columns=("ponto", "coordenadas", "dbm", "status"), 
                                show='headings', height=15, style='Treeview')
        self.tree.heading("ponto", text="Ponto")
        self.tree.heading("coordenadas", text="Coordenadas")
        self.tree.heading("dbm", text="dBm")
        self.tree.heading("status", text="Status")
        
        self.tree.column("ponto", width=80, anchor='center')
        self.tree.column("coordenadas", width=100, anchor='center')
        self.tree.column("dbm", width=60, anchor='center')
        self.tree.column("status", width=80, anchor='center')

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

    def load_floorplan_image(self):
        filetypes = [
            ('Imagens', '*.png *.jpg *.jpeg *.gif *.bmp'),
            ('PNG', '*.png'),
            ('JPEG', '*.jpg *.jpeg'),
            ('Todos os arquivos', '*.*')
        ]
        
        filename = filedialog.askopenfilename(
            title="Selecionar imagem da planta baixa",
            filetypes=filetypes
        )
        
        if filename:
            try:
                self.floorplan_image = Image.open(filename)
                self.floorplan_path = filename
                
                canvas_width = 600
                canvas_height = 400
                
                img_width, img_height = self.floorplan_image.size
                ratio = min(canvas_width / img_width, canvas_height / img_height)
                
                if ratio < 1:
                    new_width = int(img_width * ratio)
                    new_height = int(img_height * ratio)
                    self.floorplan_image = self.floorplan_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                self.floorplan_photo = ImageTk.PhotoImage(self.floorplan_image)
                
                self.canvas.delete("all")
                self.canvas.create_image(0, 0, anchor='nw', image=self.floorplan_photo)
                
                self.status_label.config(text=f"Imagem carregada: {os.path.basename(filename)}", 
                                       foreground=self.colors['success'])
                
                if self.ssid_selecionado:
                    self.enable_controls()
                
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao carregar imagem: {str(e)}")

    def clear_floorplan_image(self):
        if messagebox.askyesno("Confirmar", "Deseja remover a imagem atual e todos os pontos?"):
            self.floorplan_image = None
            self.floorplan_photo = None
            self.floorplan_path = None
            self.image_points.clear()
            self.canvas_points.clear()
            
            self.canvas.delete("all")
            self.canvas.create_text(300, 200, text="Clique em 'Carregar Imagem' para começar",
                                   font=('Segoe UI', 12), fill='gray')
            
            self.update_points_tree()
            
            self.status_label.config(text="Imagem removida", 
                                   foreground=self.colors['warning'])

    def clear_all_points(self):
        if messagebox.askyesno("Confirmar", "Deseja remover todos os pontos marcados?"):
            for outline_id, circle_id, text_id in self.canvas_points.values():
                self.canvas.delete(outline_id)
                self.canvas.delete(circle_id)
                self.canvas.delete(text_id)
            
            self.image_points.clear()
            self.canvas_points.clear()
            self.measurements.clear()
            
            self.update_points_tree()
            
            self.status_label.config(text="Todos os pontos foram removidos", 
                                   foreground=self.colors['warning'])

    def on_canvas_click(self, event):
        if not self.floorplan_image or not self.ssid_selecionado:
            return
        
        x, y = event.x, event.y
        
        if self.floorplan_photo:
            img_width = self.floorplan_photo.width()
            img_height = self.floorplan_photo.height()
            
            if 0 <= x <= img_width and 0 <= y <= img_height:
                self.add_measurement_point(x, y)

    def add_measurement_point(self, x, y):
        point_num = len(self.image_points) + 1
        point_name = f"Ponto {point_num}"
        
        self.image_points[point_name] = (x, y)
        
        outline_id = self.canvas.create_oval(x-8, y-8, x+8, y+8, fill='red', outline='white', width=2)
        circle_id = self.canvas.create_oval(x-5, y-5, x+5, y+5, fill='red', outline='white', width=1)
        text_id = self.canvas.create_text(x, y-15, text=str(point_num), 
                                        font=('Arial', 10, 'bold'), fill='white')
        
        self.canvas_points[point_name] = (outline_id, circle_id, text_id)
        
        self.measure_point_at_position(point_name, x, y)
        
        self.update_points_tree()
        
        self.status_label.config(text=f"Ponto {point_num} adicionado em ({x}, {y}) - Medição iniciada", 
                               foreground=self.colors['primary'])

    def measure_point_at_position(self, point_name, x, y):
        self.canvas.config(cursor='wait')
        
        def scan_thread():
            sig = self.scanner.scan_once(self.ssid_selecionado)
            self.root.after(0, lambda: self.update_measurement_result_position(point_name, x, y, sig))

        thread = threading.Thread(target=scan_thread, daemon=True)
        thread.start()

    def update_measurement_result_position(self, point_name, x, y, sig):
        timestamp = time.strftime("%H:%M:%S")
        
        if sig is None:
            dbm_str = "N/A"
            pct = 0
        else:
            dbm_str = sig
            pct = signal_dbm_to_percent(sig)

        measurement = {
            'dbm': dbm_str,
            'percent': pct,
            'timestamp': timestamp,
            'coordinates': (x, y)
        }
        self.measurements[point_name] = measurement

        self.update_point_visual(point_name, measurement)
        
        self.canvas.config(cursor='')
        
        self.update_points_tree()
        
        total_points = len([p for p in self.measurements.values() if p['dbm'] != 'N/A'])
        self.status_label.config(text=f"{point_name}: {dbm_str} dBm - Total de pontos medidos: {total_points}", 
                               foreground=self.colors['success'])

    def update_point_visual(self, point_name, measurement):
        if point_name not in self.canvas_points:
            return
            
        dbm = measurement['dbm']
        outline_id, circle_id, text_id = self.canvas_points[point_name]
        
        if dbm != "N/A":
            color = dbm_to_color(dbm)
            
            if color == "green":
                fill_color = '#28a745'
            elif color == "orange":
                fill_color = '#ffc107'
            else:
                fill_color = '#dc3545'
            
            self.canvas.itemconfig(circle_id, fill=fill_color)
            
            coords = self.image_points[point_name]
            self.canvas.coords(text_id, coords[0], coords[1]-15)
            self.canvas.itemconfig(text_id, text=f"{dbm}")

    def update_points_tree(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        for point_name, measurement in self.measurements.items():
            coords = measurement.get('coordinates', (0, 0))
            dbm = measurement.get('dbm', 'N/A')
            
            if dbm != 'N/A':
                color = dbm_to_color(dbm)
                if color == "green":
                    status = "Excelente"
                elif color == "orange":
                    status = "Bom"
                else:
                    status = "Ruim"
            else:
                status = "Sem sinal"

            self.tree.insert('', 'end', values=(
                point_name, 
                f"({coords[0]}, {coords[1]})", 
                dbm, 
                status
            ))

    def _create_top_frame(self, parent):
        top_frame = ttk.Frame(parent, style='Card.TLabelframe')
        top_frame.pack(fill='x', pady=(0, 10))
        
        wifi_frame = ttk.LabelFrame(top_frame, text="Seleção de Rede Wi-Fi", 
                                   style='Card.TLabelframe', padding=15)
        wifi_frame.pack(fill='x')
        
        self._create_wifi_controls(wifi_frame)
        
        controls_frame = ttk.LabelFrame(top_frame, text="Controles de Medição", 
                                       style='Card.TLabelframe', padding=15)
        controls_frame.pack(fill='x', pady=(10, 0))
        
        self._create_controls(controls_frame)

    def _create_controls(self, parent):
        local_frame = ttk.Frame(parent, style='TFrame')
        local_frame.pack(fill='x', pady=(0, 10))
        self.local_name_var = tk.StringVar()
        self.local_entry = ttk.Entry(local_frame, textvariable=self.local_name_var,
                                   font=('Segoe UI', 10), width=20)
        self.local_entry.pack(pady=(5, 0))
        self.local_entry.insert(0, "Digite o nome do local")
        self.local_entry.config(foreground='gray')

        self.local_entry.bind('<FocusIn>', self._on_entry_focus_in)
        self.local_entry.bind('<FocusOut>', self._on_entry_focus_out)

        self._create_buttons(parent)

    def _on_entry_focus_in(self, event):
        if self.local_entry.get() == "Digite o nome do local":
            self.local_entry.delete(0, tk.END)
            self.local_entry.config(foreground='black')

    def _on_entry_focus_out(self, event):
        if not self.local_entry.get():
            self.local_entry.insert(0, "Digite o nome do local")
            self.local_entry.config(foreground='gray')

    def _create_buttons(self, parent):
        button_frame = ttk.Frame(parent, style='TFrame')
        button_frame.pack(pady=(20, 10), fill='x')
        
        button_container = ttk.Frame(button_frame, style='TFrame')
        button_container.pack(anchor='center', padx=20)
        
        self.btn_clear_all = ttk.Button(button_container, text="Limpar Tudo",
                                       command=self.clear_all, style='Danger.TButton')
        self.btn_clear_all.pack(side='left', padx=(0, 30))

        self.btn_heatmap = ttk.Button(button_container, text="Gerar Mapa",
                                     command=self.show_heatmap, style='Primary.TButton')
        self.btn_heatmap.pack(side='left', padx=(0, 15))

        self.btn_save = ttk.Button(button_container, text="Salvar",
                                  command=self.save_heatmap_and_data, state='disabled',
                                  style='Success.TButton')
        self.btn_save.pack(side='left')
    def _create_wifi_controls(self, parent):
        ttk.Label(parent, text="Rede Wi-Fi:", font=('Segoe UI', 10, 'bold')).grid(row=0, column=0, sticky='w', padx=(0, 8), pady=5)
        self.combo_wifi = ttk.Combobox(parent, state='readonly', width=20, font=('Segoe UI', 10))
        self.combo_wifi.grid(row=0, column=1, sticky='w', padx=(0, 10), pady=5)
        self.combo_wifi.bind("<<ComboboxSelected>>", self.on_wifi_changed)
        
        btn_atualizar = ttk.Button(parent, text="Atualizar", 
                                  command=self.atualizar_redes, style='Primary.TButton')
        btn_atualizar.grid(row=0, column=2, pady=5)

    def _create_progress_frame(self, parent):
        self.progress_frame = ttk.LabelFrame(parent, text="Pontos de Medição",
                                           style='Card.TLabelframe', padding=15)
        self.progress_frame.pack(fill='x', pady=10)
        self.create_point_grid()

    def _create_list_frame(self, parent):
        list_frame = ttk.LabelFrame(parent, text="Pontos Medidos",
                                   style='Card.TLabelframe', padding=15)
        list_frame.pack(fill='both', expand=True, pady=10)

        self.tree = ttk.Treeview(list_frame, columns=("ponto", "dbm", "coordenadas"),
                                show='headings', height=10, style='Treeview')
        self.tree.heading("ponto", text="Ponto")
        self.tree.heading("dbm", text="dBm")
        self.tree.heading("coordenadas", text="Coordenadas")

        self.tree.column("ponto", width=120, anchor='w')
        self.tree.column("dbm", width=80, anchor='center')
        self.tree.column("coordenadas", width=120, anchor='center')

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

    def disable_controls(self):
        self.btn_load_image.config(state='disabled')
        self.btn_clear_all.config(state='disabled')
        self.btn_heatmap.config(state='disabled')
        
    def enable_controls(self):
        self.btn_load_image.config(state='normal')
        self.btn_clear_all.config(state='normal')
        self.btn_heatmap.config(state='normal')

    def atualizar_redes(self):
        lista_ssids = self.scanner.scan_networks()
        
        self.combo_wifi['values'] = ["Selecione uma rede..."] + lista_ssids
        self.combo_wifi.current(0)
        self.ssid_selecionado = None

    def on_wifi_changed(self, event):
        selected = self.combo_wifi.get()
        if selected == "Selecione uma rede...":
            self.ssid_selecionado = None
            self.disable_controls()
            self.status_label.config(text="Selecione uma rede Wi-Fi para começar as medições", 
                                   foreground=self.colors['info'])
        else:
            self.measurements.clear()
            self.update_point_grid_buttons()
            self.update_tree()
            
            self.ssid_selecionado = selected
            self.enable_controls()
            self.status_label.config(text=f"Rede selecionada: {self.ssid_selecionado} - Digite o nome do local e clique nos pontos para medir",
                                   foreground=self.colors['success'])
            print(f"Rede selecionada: {self.ssid_selecionado}")

    def on_local_changed(self, event):
        pass

    def create_point_grid(self):
        for widget in self.point_labels.values():
            widget.destroy()
        self.point_labels.clear()

        grid_size = 4
        
        for row in range(grid_size):
            for col in range(grid_size):
                point_num = row * grid_size + col + 1
                point_name = f"Ponto {point_num}"
                
                point_button = ttk.Button(self.progress_frame, 
                                        text=f"{point_num}\nNão medido",
                                        command=lambda p=point_name: self.measure_point_auto(p),
                                        style='TButton')
                point_button.grid(row=row, column=col, padx=3, pady=3, sticky='nsew')
                
                self.point_labels[point_name] = point_button

        for i in range(grid_size):
            self.progress_frame.grid_columnconfigure(i, weight=1)
            self.progress_frame.grid_rowconfigure(i, weight=1)

    def update_point_button(self, button, point_name, measurement):
        dbm = measurement['dbm']
        
        if dbm != "N/A":
            percent = measurement['percent']
            color = dbm_to_color(dbm)
            
            if color == "green":
                style_name = 'Success.TButton'
                status_icon = "✅"
                bg_color = '#d4edda'
            elif color == "orange":
                style_name = 'Warning.TButton' 
                status_icon = "⚠️"
                bg_color = '#fff3cd'
            else:
                style_name = 'Danger.TButton'
                status_icon = "❌"
                bg_color = '#f8d7da'
            
            button.config(text=f"{status_icon} {point_name}\n{dbm} dBm\n({percent}%)", 
                         style=style_name,
                         state='disabled')
        else:
            button.config(text=f"❓ {point_name}\nSem sinal", 
                         style='TButton',
                         state='normal')

    def measure_point_auto(self, point_name):
        if not self.ssid_selecionado:
            messagebox.showerror("Erro", "Selecione uma rede Wi-Fi primeiro")
            return

        local_name = self.local_name_var.get().strip()
        if not local_name:
            messagebox.showerror("Erro", "Digite um nome para o local")
            self.local_entry.focus()
            return

        local = local_name
        ponto = point_name

        button = self.point_labels[point_name]
        button.config(state='disabled', text=f"Medindo...\n{ponto}")
        self.status_label.config(text=f"Medindo {ponto} em {local}... Aguarde alguns segundos",
                               foreground=self.colors['warning'])
        self.root.update()

        def scan_thread():
            sig = self.scanner.scan_once(self.ssid_selecionado)
            self.root.after(0, lambda: self.update_measurement_result_auto(local, ponto, sig, button))

        thread = threading.Thread(target=scan_thread, daemon=True)
        thread.start()

    def update_measurement_result_auto(self, local, ponto, sig, button):
        timestamp = time.strftime("%H:%M:%S")
        
        if sig is None:
            dbm_str = "N/A"
            pct = 0
        else:
            dbm_str = sig
            pct = signal_dbm_to_percent(sig)

        measurement = {
            'dbm': dbm_str,
            'percent': pct,
            'timestamp': timestamp
        }
        self.measurements[local][ponto] = measurement

        self.update_point_button(button, ponto, measurement)
        
        self.update_tree()

        points_measured = len(self.measurements[local])
        if points_measured == 16:
            self.status_label.config(text=f"{local}: Todos os 16 pontos medidos! Pronto para gerar mapa de calor", 
                                   foreground=self.colors['success'])
        else:
            self.status_label.config(text=f"{local}: {points_measured}/16 pontos medidos - Continue clicando nos pontos restantes", 
                                   foreground=self.colors['primary'])

    def update_point_grid_buttons(self):
        local_name = self.local_name_var.get().strip()
        if not local_name:
            return

        local_data = self.measurements.get(local_name, {})

        for point_name, button in self.point_labels.items():
            if point_name in local_data:
                measurement = local_data[point_name]
                self.update_point_button(button, point_name, measurement)
            else:
                point_num = point_name.split()[-1]
        
        for point_name, button in self.point_labels.items():
            if point_name in local_data:
                measurement = local_data[point_name]
                self.update_point_button(button, point_name, measurement)
            else:
                point_num = point_name.split()[-1]
                button.config(text=f"{point_num}\nNão medido", 
                             style='TButton',
                             state='normal')

    def update_tree(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        local_name = self.local_name_var.get().strip() or "Local"
        if local_name in self.measurements:
            for point_name, measurement in self.measurements[local_name].items():
                if measurement.get('dbm', 'N/A') != 'N/A':
                    coords = measurement.get('coordinates', (0, 0))
                    coord_str = f"({coords[0]:.0f}, {coords[1]:.0f})"
                    self.tree.insert('', 'end', values=(point_name, f"{measurement['dbm']}", coord_str))

    def clear_all(self):
        if messagebox.askyesno("Limpar Tudo", "Tem certeza que deseja limpar TODOS os dados?\n\nIsso irá remover:\n• Todos os pontos marcados\n• A imagem carregada\n• Todas as medições\n\nEsta ação não pode ser desfeita."):
            self.floorplan_image = None
            self.floorplan_photo = None
            self.floorplan_path = None
            
            for outline_id, circle_id, text_id in self.canvas_points.values():
                self.canvas.delete(outline_id)
                self.canvas.delete(circle_id)
                self.canvas.delete(text_id)
            
            self.image_points.clear()
            self.canvas_points.clear()
            self.measurements.clear()
            
            self.canvas.delete("all")
            self.canvas.create_text(300, 200, text="Clique em 'Carregar Imagem' para começar",
                                  font=('Segoe UI', 12), fill=self.colors['info'])
            
            self.update_points_tree()
            
            if self.ssid_selecionado:
                self.status_label.config(text=f"Tudo foi limpo - Pronto para novas medições com {self.ssid_selecionado}", 
                                       foreground=self.colors['warning'])
            else:
                self.status_label.config(text="Tudo foi limpo - Selecione uma rede Wi-Fi para começar", 
                                       foreground=self.colors['warning'])

    def show_heatmap(self):
        self.heatmap_generator.generate_heatmap(self.measurements, self.ssid_selecionado, 
                                              self.floorplan_path)
        self.btn_save.config(state='normal')

    def save_heatmap_and_data(self):
        try:
            if not self.measurements:
                messagebox.showwarning("Aviso", "Não há dados para salvar. Gere um mapa primeiro.")
                return
            
            file_path = filedialog.asksaveasfilename(
                defaultextension=".png",
                filetypes=[
                    ("PNG files", "*.png"),
                    ("All files", "*.*")
                ],
                title="Salvar Mapa de Calor"
            )
            
            if not file_path:
                return
            
            png_path = file_path
            self.heatmap_generator.save_heatmap_image(png_path)
            
            json_path = file_path.replace('.png', '.json')
            self.save_measurements_json(json_path)
            
            self.status_label.config(
                text=f"Arquivos salvos com sucesso!\nPNG: {os.path.basename(png_path)}\nJSON: {os.path.basename(json_path)}",
                foreground=self.colors['success']
            )
            
        except Exception as e:
            messagebox.showerror("Erro ao Salvar", f"Ocorreu um erro ao salvar os arquivos:\n{str(e)}")
            self.status_label.config(text="Erro ao salvar arquivos", foreground=self.colors['error'])

    def save_measurements_json(self, file_path):
        import json
        
        data_to_save = {
            "ssid": self.ssid_selecionado,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "measurements": self.measurements,
            "floorplan": self.floorplan_path if self.floorplan_path else None
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data_to_save, f, indent=2, ensure_ascii=False)