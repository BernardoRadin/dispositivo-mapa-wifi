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
        
        # Configurar estilos modernos
        self.setup_styles()
        
        # Componentes principais
        self.scanner = WifiScanner()
        self.heatmap_generator = HeatmapGenerator(root)
        
        # Dados da aplicação
        self.measurements = defaultdict(dict)
        self.current_local = None
        self.ssid_selecionado = None
        
        # Sistema de imagem de planta baixa
        self.floorplan_image = None
        self.floorplan_photo = None
        self.floorplan_path = None
        self.image_points = {}  # {point_name: (x, y)}
        self.canvas_points = {}  # {point_name: canvas_item_id}
        
        # Interface
        self.point_labels = {}
        self.canvas = None
        self.create_widgets()

    def setup_styles(self):
        """Configura estilos modernos para a interface"""
        style = ttk.Style()
        
        # Configurar tema
        try:
            style.theme_use('clam')  # Tema mais moderno
        except:
            pass
        
        # Cores do tema
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
        
        # Estilo para botões
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
        
        # Hover effects melhorados
        style.map('Primary.TButton',
                 background=[('active', '#0056b3'), ('pressed', '#004085')])
        style.map('Success.TButton', 
                 background=[('active', '#218838'), ('pressed', '#1e7e34')])
        style.map('Danger.TButton',
                 background=[('active', '#c82333'), ('pressed', '#bd2130')])
        
        # Estilo para labels
        style.configure('TLabel', 
                       font=('Segoe UI', 10),
                       background=self.colors['light'])
        
        style.configure('Header.TLabel',
                       font=('Segoe UI', 14, 'bold'),
                       foreground=self.colors['dark'])
        
        # Estilo para frames normais
        style.configure('TFrame',
                       background=self.colors['white'])
        
        # Estilo para frames
        style.configure('Card.TLabelframe',
                       background=self.colors['white'],
                       relief='solid',
                       borderwidth=1)
        
        style.configure('Card.TLabelframe.Label',
                       font=('Segoe UI', 11, 'bold'),
                       foreground=self.colors['primary'],
                       background=self.colors['white'])
        
        # Estilo para combobox
        style.configure('TCombobox',
                       font=('Segoe UI', 10),
                       padding=5)
        
        # Estilo para treeview
        style.configure('Treeview',
                       font=('Segoe UI', 9),
                       rowheight=25,
                       background=self.colors['white'])
        
        style.configure('Treeview.Heading',
                       font=('Segoe UI', 10, 'bold'),
                       background=self.colors['primary'],
                       foreground=self.colors['white'])

    def create_widgets(self):
        # Container principal com padding e fundo
        main_container = ttk.Frame(self.root, style='Card.TLabelframe')
        main_container.pack(fill='both', expand=True, padx=15, pady=10)
        
        # Título principal
        title_label = ttk.Label(main_container, 
                               text="📡 WiFi Scanner - Mapa de Calor com Planta Baixa",
                               style='Header.TLabel')
        title_label.pack(pady=(0, 15))
        
        # Frame superior para controles
        self._create_top_frame(main_container)
        
        # Status com melhor visual
        self.status_label = ttk.Label(main_container, 
                                     text="Selecione uma rede Wi-Fi para começar", 
                                     font=('Segoe UI', 11),
                                     foreground=self.colors['info'],
                                     background=self.colors['light'])
        self.status_label.pack(pady=10, fill='x', padx=10)

        # Container principal dividido em duas partes
        content_frame = ttk.Frame(main_container, style='TFrame')
        content_frame.pack(fill='both', expand=True, pady=10)
        
        # Painel esquerdo - Controles e lista
        self._create_left_panel(content_frame)
        
        # Painel direito - Canvas da imagem
        self._create_right_panel(content_frame)
        
        # Inicialização
        self.atualizar_redes()
        self.disable_controls()

    def _create_left_panel(self, parent):
        """Cria o painel esquerdo com controles e lista"""
        left_panel = ttk.Frame(parent, style='TFrame')
        left_panel.pack(side='left', fill='y', padx=(0, 10))
        
        # Controles de imagem
        self._create_image_controls(left_panel)
        
        # Lista de pontos medidos
        self._create_points_list(left_panel)

    def _create_right_panel(self, parent):
        """Cria o painel direito com o canvas da imagem"""
        right_panel = ttk.LabelFrame(parent, text="🖼️ Planta Baixa", 
                                    style='Card.TLabelframe', padding=10)
        right_panel.pack(side='right', fill='both', expand=True)
        
        # Canvas para exibir a imagem
        self.canvas = tk.Canvas(right_panel, bg='white', relief='sunken', borderwidth=2)
        self.canvas.pack(fill='both', expand=True)
        
        # Bind do clique no canvas
        self.canvas.bind('<Button-1>', self.on_canvas_click)
        
        # Mensagem inicial no canvas
        self.canvas.create_text(300, 200, text="Clique em 'Carregar Imagem' para começar",
                               font=('Segoe UI', 12), fill='gray')

    def _create_image_controls(self, parent):
        """Cria controles para gerenciar a imagem"""
        image_frame = ttk.LabelFrame(parent, text="📁 Gerenciar Planta Baixa", 
                                    style='Card.TLabelframe', padding=10)
        image_frame.pack(fill='x', pady=(0, 10))
        
        # Botão para carregar imagem
        self.btn_load_image = ttk.Button(image_frame, text="📤 Carregar Imagem", 
                                        command=self.load_floorplan_image, style='Primary.TButton')
        self.btn_load_image.pack(fill='x')

    def _create_points_list(self, parent):
        """Cria a lista de pontos medidos"""
        list_frame = ttk.LabelFrame(parent, text="📋 Pontos Medidos", 
                                   style='Card.TLabelframe', padding=10)
        list_frame.pack(fill='both', expand=True)
        
        # Treeview para mostrar pontos
        self.tree = ttk.Treeview(list_frame, columns=("ponto", "coordenadas", "dbm", "status"), 
                                show='headings', height=15, style='Treeview')
        self.tree.heading("ponto", text="📍 Ponto")
        self.tree.heading("coordenadas", text="📐 Coordenadas")
        self.tree.heading("dbm", text="📊 dBm")
        self.tree.heading("status", text="📈 Status")
        
        self.tree.column("ponto", width=80, anchor='center')
        self.tree.column("coordenadas", width=100, anchor='center')
        self.tree.column("dbm", width=60, anchor='center')
        self.tree.column("status", width=80, anchor='center')

        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

    def load_floorplan_image(self):
        """Carrega uma imagem de planta baixa"""
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
                # Carregar imagem com PIL
                self.floorplan_image = Image.open(filename)
                self.floorplan_path = filename
                
                # Redimensionar se necessário para caber no canvas
                canvas_width = 600
                canvas_height = 400
                
                img_width, img_height = self.floorplan_image.size
                ratio = min(canvas_width / img_width, canvas_height / img_height)
                
                if ratio < 1:
                    new_width = int(img_width * ratio)
                    new_height = int(img_height * ratio)
                    self.floorplan_image = self.floorplan_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # Converter para PhotoImage
                self.floorplan_photo = ImageTk.PhotoImage(self.floorplan_image)
                
                # Exibir no canvas
                self.canvas.delete("all")
                self.canvas.create_image(0, 0, anchor='nw', image=self.floorplan_photo)
                
                # Atualizar status
                self.status_label.config(text=f"✅ Imagem carregada: {os.path.basename(filename)}", 
                                       foreground=self.colors['success'])
                
                # Habilitar controles se WiFi estiver selecionado
                if self.ssid_selecionado:
                    self.enable_controls()
                
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao carregar imagem: {str(e)}")

    def clear_floorplan_image(self):
        """Limpa a imagem atual"""
        if messagebox.askyesno("Confirmar", "Deseja remover a imagem atual e todos os pontos?"):
            self.floorplan_image = None
            self.floorplan_photo = None
            self.floorplan_path = None
            self.image_points.clear()
            self.canvas_points.clear()
            
            # Limpar canvas
            self.canvas.delete("all")
            self.canvas.create_text(300, 200, text="Clique em 'Carregar Imagem' para começar",
                                   font=('Segoe UI', 12), fill='gray')
            
            # Limpar lista de pontos
            self.update_points_tree()
            
            # Atualizar status
            self.status_label.config(text="🖼️ Imagem removida", 
                                   foreground=self.colors['warning'])

    def clear_all_points(self):
        """Limpa todos os pontos da imagem"""
        if messagebox.askyesno("Confirmar", "Deseja remover todos os pontos marcados?"):
            # Remover pontos do canvas
            for outline_id, circle_id, text_id in self.canvas_points.values():
                self.canvas.delete(outline_id)
                self.canvas.delete(circle_id)
                self.canvas.delete(text_id)
            
            # Limpar dados
            self.image_points.clear()
            self.canvas_points.clear()
            self.measurements.clear()
            
            # Atualizar interface
            self.update_points_tree()
            
            # Atualizar status
            self.status_label.config(text="🔄 Todos os pontos foram removidos", 
                                   foreground=self.colors['warning'])

    def on_canvas_click(self, event):
        """Manipula clique no canvas para adicionar pontos"""
        if not self.floorplan_image or not self.ssid_selecionado:
            return
        
        # Obter coordenadas do clique
        x, y = event.x, event.y
        
        # Verificar se clicou dentro da imagem
        if self.floorplan_photo:
            img_width = self.floorplan_photo.width()
            img_height = self.floorplan_photo.height()
            
            if 0 <= x <= img_width and 0 <= y <= img_height:
                self.add_measurement_point(x, y)

    def add_measurement_point(self, x, y):
        """Adiciona um ponto de medição na posição clicada"""
        # Gerar nome do ponto
        point_num = len(self.image_points) + 1
        point_name = f"Ponto {point_num}"
        
        # Armazenar coordenadas
        self.image_points[point_name] = (x, y)
        
        # Desenhar ponto no canvas
        # Círculo externo (contorno)
        outline_id = self.canvas.create_oval(x-8, y-8, x+8, y+8, fill='red', outline='white', width=2)
        # Círculo interno
        circle_id = self.canvas.create_oval(x-5, y-5, x+5, y+5, fill='red', outline='white', width=1)
        # Texto com número
        text_id = self.canvas.create_text(x, y-15, text=str(point_num), 
                                        font=('Arial', 10, 'bold'), fill='white')
        
        # Armazenar IDs dos elementos do canvas
        self.canvas_points[point_name] = (outline_id, circle_id, text_id)
        
        # Iniciar medição automaticamente
        self.measure_point_at_position(point_name, x, y)
        
        # Atualizar lista
        self.update_points_tree()
        
        # Atualizar status
        self.status_label.config(text=f"📍 Ponto {point_num} adicionado em ({x}, {y}) - Medição iniciada", 
                               foreground=self.colors['primary'])

    def measure_point_at_position(self, point_name, x, y):
        """Realiza medição WiFi em uma posição específica"""
        # Desabilitar canvas durante medição
        self.canvas.config(cursor='wait')
        
        # Fazer medição em thread separada
        def scan_thread():
            sig = self.scanner.scan_once(self.ssid_selecionado)
            self.root.after(0, lambda: self.update_measurement_result_position(point_name, x, y, sig))

        thread = threading.Thread(target=scan_thread, daemon=True)
        thread.start()

    def update_measurement_result_position(self, point_name, x, y, sig):
        """Atualiza resultado da medição para um ponto específico"""
        timestamp = time.strftime("%H:%M:%S")
        
        if sig is None:
            dbm_str = "N/A"
            pct = 0
        else:
            dbm_str = sig
            pct = signal_dbm_to_percent(sig)

        # Salvar medição
        measurement = {
            'dbm': dbm_str,
            'percent': pct,
            'timestamp': timestamp,
            'coordinates': (x, y)
        }
        self.measurements[point_name] = measurement

        # Atualizar visual do ponto no canvas baseado na qualidade
        self.update_point_visual(point_name, measurement)
        
        # Reabilitar canvas
        self.canvas.config(cursor='')
        
        # Atualizar lista
        self.update_points_tree()
        
        # Verificar se temos pontos suficientes para gerar mapa
        total_points = len([p for p in self.measurements.values() if p['dbm'] != 'N/A'])
        self.status_label.config(text=f"✅ {point_name}: {dbm_str} dBm - Total de pontos medidos: {total_points}", 
                               foreground=self.colors['success'])

    def update_point_visual(self, point_name, measurement):
        """Atualiza a aparência visual do ponto baseado na medição"""
        if point_name not in self.canvas_points:
            return
            
        dbm = measurement['dbm']
        outline_id, circle_id, text_id = self.canvas_points[point_name]
        
        if dbm != "N/A":
            color = dbm_to_color(dbm)
            
            # Cores baseadas na qualidade do sinal
            if color == "green":
                fill_color = '#28a745'  # Verde
            elif color == "orange":
                fill_color = '#ffc107'  # Amarelo
            else:
                fill_color = '#dc3545'  # Vermelho
            
            # Atualizar cor do círculo
            self.canvas.itemconfig(circle_id, fill=fill_color)
            
            # Adicionar texto com valor dBm
            coords = self.image_points[point_name]
            self.canvas.coords(text_id, coords[0], coords[1]-15)
            self.canvas.itemconfig(text_id, text=f"{dbm}")

    def update_points_tree(self):
        """Atualiza a lista de pontos na treeview"""
        # Limpar árvore
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Adicionar pontos
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
        
        # Frame para seleção de WiFi
        wifi_frame = ttk.LabelFrame(top_frame, text="📶 Seleção de Rede Wi-Fi", 
                                   style='Card.TLabelframe', padding=15)
        wifi_frame.pack(fill='x')
        
        self._create_wifi_controls(wifi_frame)
        
        # Frame para controles de localização e botões
        controls_frame = ttk.LabelFrame(top_frame, text="🎯 Controles de Medição", 
                                       style='Card.TLabelframe', padding=15)
        controls_frame.pack(fill='x', pady=(10, 0))
        
        self._create_controls(controls_frame)

    def _create_controls(self, parent):
        # Instruções para o usuário
        ttk.Label(parent, text="📍 Clique na imagem para posicionar pontos de medição", 
                 font=('Segoe UI', 9), foreground=self.colors['info']).pack(pady=5)
        
        # Botões de ação
        self._create_buttons(parent)

    def _create_buttons(self, parent):
        button_frame = ttk.Frame(parent, style='TFrame')
        button_frame.pack(pady=(20, 10), fill='x')
        
        # Container para centralizar os botões com padding adequado
        button_container = ttk.Frame(button_frame, style='TFrame')
        button_container.pack(anchor='center', padx=20)
        
        # Botões principais com espaçamento adequado
        self.btn_clear_all = ttk.Button(button_container, text="🗑️ Limpar Tudo", 
                                       command=self.clear_all, style='Danger.TButton')
        self.btn_clear_all.pack(side='left', padx=(0, 50))
        
        self.btn_heatmap = ttk.Button(button_container, text="🗺️ Gerar Mapa", 
                                     command=self.show_heatmap, style='Primary.TButton')
        self.btn_heatmap.pack(side='left')
    def _create_wifi_controls(self, parent):
        ttk.Label(parent, text="📶 Rede Wi-Fi:", font=('Segoe UI', 10, 'bold')).grid(row=0, column=0, sticky='w', padx=(0, 8), pady=5)
        self.combo_wifi = ttk.Combobox(parent, state='readonly', width=20, font=('Segoe UI', 10))
        self.combo_wifi.grid(row=0, column=1, sticky='w', padx=(0, 10), pady=5)
        self.combo_wifi.bind("<<ComboboxSelected>>", self.on_wifi_changed)
        
        btn_atualizar = ttk.Button(parent, text="🔄 Atualizar", 
                                  command=self.atualizar_redes, style='Primary.TButton')
        btn_atualizar.grid(row=0, column=2, pady=5)

    def _create_progress_frame(self, parent):
        self.progress_frame = ttk.LabelFrame(parent, text="📊 Progresso do Local Atual", 
                                           style='Card.TLabelframe', padding=15)
        self.progress_frame.pack(fill='x', pady=10)
        self.create_point_grid()

    def _create_list_frame(self, parent):
        list_frame = ttk.LabelFrame(parent, text="📋 Todos os Locais Medidos", 
                                   style='Card.TLabelframe', padding=15)
        list_frame.pack(fill='both', expand=True, pady=10)

        # Treeview para mostrar todos os locais
        self.tree = ttk.Treeview(list_frame, columns=("local", "pontos", "media"), 
                                show='headings', height=10, style='Treeview')
        self.tree.heading("local", text="🏠 Local")
        self.tree.heading("pontos", text="📍 Pontos Medidos")
        self.tree.heading("media", text="📊 Média (dBm)")
        
        self.tree.column("local", width=140, anchor='w')
        self.tree.column("pontos", width=140, anchor='center')
        self.tree.column("media", width=140, anchor='center')

        # Scrollbar
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
        
        # Atualiza valores no combobox sem selecionar nada
        self.combo_wifi['values'] = ["Selecione uma rede..."] + lista_ssids
        self.combo_wifi.current(0)  # seleciona o placeholder
        self.ssid_selecionado = None

    def on_wifi_changed(self, event):
        selected = self.combo_wifi.get()
        if selected == "Selecione uma rede...":
            self.ssid_selecionado = None
            self.disable_controls()
            self.status_label.config(text="💡 Selecione uma rede Wi-Fi para começar as medições", 
                                   foreground=self.colors['info'])
        else:
            # Se já havia uma rede selecionada e há medições, limpar tudo
            self.measurements.clear()
            self.update_point_grid_buttons()
            self.update_tree()
            
            self.ssid_selecionado = selected
            self.enable_controls()
            self.status_label.config(text=f"✅ Rede selecionada: {self.ssid_selecionado} - Selecione um local e ponto para começar", 
                                   foreground=self.colors['success'])
            print(f"Rede selecionada: {self.ssid_selecionado}")

    def on_local_changed(self, event):
        selected = self.combo_local.get()
        if selected:
            self.current_local = selected
            self.status_label.config(text=f"🏠 Local selecionado: {self.current_local} - Clique nos pontos do grid para medir", 
                                   foreground=self.colors['success'])
            print(f"Local selecionado: {self.current_local}")
        else:
            self.current_local = None
            self.status_label.config(text="💡 Selecione um local para começar as medições", 
                                   foreground=self.colors['info'])

    def create_point_grid(self):
        # Limpar labels anteriores
        for widget in self.point_labels.values():
            widget.destroy()
        self.point_labels.clear()

        # Criar grid 4x4 de pontos clicáveis
        grid_size = 4
        
        for row in range(grid_size):
            for col in range(grid_size):
                point_num = row * grid_size + col + 1
                point_name = f"Ponto {point_num}"
                
                # Criar botão para cada ponto
                point_button = ttk.Button(self.progress_frame, 
                                        text=f"📍 {point_num}\nNão medido",
                                        command=lambda p=point_name: self.measure_point_auto(p),
                                        style='TButton')
                point_button.grid(row=row, column=col, padx=3, pady=3, sticky='nsew')
                
                self.point_labels[point_name] = point_button

        # Configurar grid para expandir igualmente
        for i in range(grid_size):
            self.progress_frame.grid_columnconfigure(i, weight=1)
            self.progress_frame.grid_rowconfigure(i, weight=1)

    def update_point_button(self, button, point_name, measurement):
        """Atualiza a aparência de um botão de ponto baseado na medição"""
        dbm = measurement['dbm']
        
        if dbm != "N/A":
            percent = measurement['percent']
            color = dbm_to_color(dbm)
            
            # Cores e ícones baseados na qualidade do sinal
            if color == "green":
                style_name = 'Success.TButton'
                status_icon = "✅"
                bg_color = '#d4edda'  # Verde claro
            elif color == "orange":
                style_name = 'Warning.TButton' 
                status_icon = "⚠️"
                bg_color = '#fff3cd'  # Amarelo claro
            else:
                style_name = 'Danger.TButton'
                status_icon = "❌"
                bg_color = '#f8d7da'  # Vermelho claro
            
            button.config(text=f"{status_icon} {point_name}\n{dbm} dBm\n({percent}%)", 
                         style=style_name,
                         state='disabled')  # Desabilitar botão após medição
        else:
            button.config(text=f"❓ {point_name}\nSem sinal", 
                         style='TButton',
                         state='normal')  # Manter habilitado para tentar novamente

    def measure_point_auto(self, point_name):
        if not self.ssid_selecionado:
            messagebox.showerror("Erro", "Selecione uma rede Wi-Fi primeiro")
            return
            
        if not self.current_local:
            messagebox.showerror("Erro", "Selecione um local primeiro")
            return

        local = self.current_local
        ponto = point_name

        # Desabilitar botão durante medição
        button = self.point_labels[point_name]
        button.config(state='disabled', text=f"📡 Medindo...\n{ponto}")
        self.status_label.config(text=f"📡 Medindo {ponto} em {local}... Aguarde alguns segundos", 
                               foreground=self.colors['warning'])
        self.root.update()

        # Fazer medição em thread separada
        def scan_thread():
            sig = self.scanner.scan_once(self.ssid_selecionado)
            self.root.after(0, lambda: self.update_measurement_result_auto(local, ponto, sig, button))

        thread = threading.Thread(target=scan_thread, daemon=True)
        thread.start()

    def insert_manual(self):
        if not self.ssid_selecionado:
            messagebox.showerror("Erro", "Selecione uma rede Wi-Fi")
            return
            
        if not self.current_local:
            messagebox.showerror("Erro", "Selecione um local primeiro")
            return

        local = self.current_local
        
        # Criar lista de pontos disponíveis (1-16)
        available_points = [f"Ponto {i}" for i in range(1, 17)]
        
        # Criar janela para inserir valor manual
        manual_window = tk.Toplevel(self.root)
        manual_window.title("Inserir Valor Manual")
        manual_window.geometry("400x250")
        manual_window.transient(self.root)
        manual_window.grab_set()

        # Centralizar a janela
        manual_window.geometry("+%d+%d" % (self.root.winfo_rootx() + 50, self.root.winfo_rooty() + 50))

        frame = ttk.Frame(manual_window, padding=20)
        frame.pack(fill='both', expand=True)

        ttk.Label(frame, text=f"Rede: {self.ssid_selecionado}", font=('Arial', 10)).pack(pady=2)
        ttk.Label(frame, text=f"Local: {local}", font=('Arial', 12, 'bold')).pack(pady=2)
        
        # Seleção de ponto
        point_frame = ttk.Frame(frame, style='TFrame')
        point_frame.pack(pady=(15, 5))
        
        ttk.Label(point_frame, text="Ponto:", font=('Arial', 10)).grid(row=0, column=0, padx=(0, 10))
        point_var = tk.StringVar()
        point_combo = ttk.Combobox(point_frame, textvariable=point_var, values=available_points, 
                                  state='readonly', width=15)
        point_combo.grid(row=0, column=1)
        point_combo.current(0)  # Selecionar primeiro ponto por padrão

        ttk.Label(frame, text="Valor RSSI (dBm):", font=('Arial', 10)).pack(pady=(15, 5))
        
        dbm_var = tk.StringVar(value="-50")
        entry_dbm = ttk.Entry(frame, textvariable=dbm_var, font=('Arial', 12), width=15, justify='center')
        entry_dbm.pack(pady=5)
        entry_dbm.focus()
        entry_dbm.select_range(0, tk.END)

        # Frame para botões
        btn_frame = ttk.Frame(frame, style='TFrame')
        btn_frame.pack(pady=20)

        def save_manual():
            try:
                ponto = point_var.get()
                if not ponto:
                    messagebox.showerror("Erro", "Selecione um ponto")
                    return
                    
                dbm_value = int(dbm_var.get())
                if dbm_value < -100 or dbm_value > 0:
                    messagebox.showerror("Erro", "Valor deve estar entre -100 e 0 dBm")
                    return

                # Salvar medição
                timestamp = time.strftime("%H:%M:%S")
                pct = signal_dbm_to_percent(dbm_value)
                
                measurement = {
                    'dbm': dbm_value,
                    'percent': pct,
                    'timestamp': timestamp
                }
                self.measurements[local][ponto] = measurement

                # Atualizar botão com resultado
                if ponto in self.point_labels:
                    self.update_point_button(self.point_labels[ponto], ponto, measurement)
                
                # Atualizar interface
                self.update_tree()

                # Verificar se completou os 16 pontos
                points_measured = len(self.measurements[local])
                self.status_label.config(text=f"📍 {local}: {points_measured}/16 pontos medidos (Manual: {dbm_value} dBm)")

                manual_window.destroy()

            except ValueError:
                messagebox.showerror("Erro", "Digite um número inteiro válido")

        def cancel_manual():
            manual_window.destroy()

        ttk.Button(btn_frame, text="Salvar", command=save_manual).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Cancelar", command=cancel_manual).pack(side='left', padx=5)

        # Bind Enter key
        entry_dbm.bind('<Return>', lambda e: save_manual())
        manual_window.bind('<Escape>', lambda e: cancel_manual())

    def update_measurement_result_auto(self, local, ponto, sig, button):
        timestamp = time.strftime("%H:%M:%S")
        
        if sig is None:
            dbm_str = "N/A"
            pct = 0
        else:
            dbm_str = sig
            pct = signal_dbm_to_percent(sig)

        # Salvar medição
        measurement = {
            'dbm': dbm_str,
            'percent': pct,
            'timestamp': timestamp
        }
        self.measurements[local][ponto] = measurement

        # Atualizar botão com resultado
        self.update_point_button(button, ponto, measurement)
        
        # Atualizar interface
        self.update_tree()

        # Verificar se completou os 16 pontos
        points_measured = len(self.measurements[local])
        if points_measured == 16:
            self.status_label.config(text=f"🎉 {local}: Todos os 16 pontos medidos! Pronto para gerar mapa de calor", 
                                   foreground=self.colors['success'])
        else:
            self.status_label.config(text=f"📍 {local}: {points_measured}/16 pontos medidos - Continue clicando nos pontos restantes", 
                                   foreground=self.colors['primary'])

    def update_point_grid_buttons(self):
        """Atualiza todos os botões do grid para o local atual"""
        if not self.current_local:
            return

        local_data = self.measurements.get(self.current_local, {})
        
        for point_name, button in self.point_labels.items():
            if point_name in local_data:
                measurement = local_data[point_name]
                self.update_point_button(button, point_name, measurement)
            else:
                # Reset para estado não medido
                point_num = point_name.split()[-1]  # Extrair número do ponto
                button.config(text=f"📍 {point_num}\nNão medido", 
                             style='TButton',
                             state='normal')

    def update_tree(self):
        # Limpar árvore
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Adicionar locais
        for local, points in self.measurements.items():
            points_count = len(points)
            valid_measurements = [p['dbm'] for p in points.values() if p['dbm'] != 'N/A']
            
            if valid_measurements:
                avg_dbm = sum(valid_measurements) / len(valid_measurements)
                avg_str = f"{avg_dbm:.1f}"
            else:
                avg_str = "N/A"

            self.tree.insert('', 'end', values=(local, f"{points_count}/16", avg_str))

    def clear_all(self):
        if messagebox.askyesno("🗑️ Limpar Tudo", "Tem certeza que deseja limpar TODOS os dados?\n\nIsso irá remover:\n• Todos os pontos marcados\n• A imagem carregada\n• Todas as medições\n\nEsta ação não pode ser desfeita."):
            # Limpar imagem
            self.floorplan_image = None
            self.floorplan_photo = None
            self.floorplan_path = None
            
            # Limpar pontos do canvas
            for outline_id, circle_id, text_id in self.canvas_points.values():
                self.canvas.delete(outline_id)
                self.canvas.delete(circle_id)
                self.canvas.delete(text_id)
            
            # Limpar dados
            self.image_points.clear()
            self.canvas_points.clear()
            self.measurements.clear()
            
            # Limpar canvas completamente
            self.canvas.delete("all")
            self.canvas.create_text(300, 200, text="Clique em 'Carregar Imagem' para começar",
                                  font=('Segoe UI', 12), fill=self.colors['info'])
            
            # Atualizar interface
            self.update_points_tree()
            
            # Resetar seleção de local
            self.current_local = None
            
            if self.ssid_selecionado:
                self.status_label.config(text=f"🗑️ Tudo foi limpo - Pronto para novas medições com {self.ssid_selecionado}", 
                                       foreground=self.colors['warning'])
            else:
                self.status_label.config(text="🗑️ Tudo foi limpo - Selecione uma rede Wi-Fi para começar", 
                                       foreground=self.colors['warning'])

    def show_heatmap(self):
        self.heatmap_generator.generate_heatmap(self.measurements, self.ssid_selecionado, 
                                              self.floorplan_path, self.load_example_data)

    def load_example_data(self):
        if not self.ssid_selecionado:
            messagebox.showerror("Erro", "Selecione uma rede Wi-Fi primeiro")
            return
            
        if messagebox.askyesno("Carregar Dados", "Isso irá substituir todas as medições atuais. Continuar?"):
            self.measurements.clear()
            
            # Dados de exemplo para 4x4 grid (16 pontos)
            example_data = {
                "Sala": {
                    "Ponto 1": {'dbm': -45, 'percent': 90, 'timestamp': '10:00:00'},
                    "Ponto 2": {'dbm': -48, 'percent': 86, 'timestamp': '10:01:00'},
                    "Ponto 3": {'dbm': -42, 'percent': 96, 'timestamp': '10:02:00'},
                    "Ponto 4": {'dbm': -50, 'percent': 80, 'timestamp': '10:03:00'},
                    "Ponto 5": {'dbm': -47, 'percent': 88, 'timestamp': '10:04:00'},
                    "Ponto 6": {'dbm': -46, 'percent': 89, 'timestamp': '10:05:00'},
                    "Ponto 7": {'dbm': -49, 'percent': 84, 'timestamp': '10:06:00'},
                    "Ponto 8": {'dbm': -44, 'percent': 92, 'timestamp': '10:07:00'},
                    "Ponto 9": {'dbm': -51, 'percent': 78, 'timestamp': '10:08:00'},
                    "Ponto 10": {'dbm': -48, 'percent': 86, 'timestamp': '10:09:00'},
                    "Ponto 11": {'dbm': -45, 'percent': 90, 'timestamp': '10:10:00'},
                    "Ponto 12": {'dbm': -47, 'percent': 88, 'timestamp': '10:11:00'},
                    "Ponto 13": {'dbm': -49, 'percent': 84, 'timestamp': '10:12:00'},
                    "Ponto 14": {'dbm': -46, 'percent': 89, 'timestamp': '10:13:00'},
                    "Ponto 15": {'dbm': -48, 'percent': 86, 'timestamp': '10:14:00'},
                    "Ponto 16": {'dbm': -50, 'percent': 80, 'timestamp': '10:15:00'}
                }
            }
            
            self.measurements.update(example_data)
            self.update_point_grid_buttons()
            self.update_tree()
            self.status_label.config(text=f"📊 Dados de exemplo carregados com sucesso para {self.ssid_selecionado} - Pronto para gerar mapa!", 
                                   foreground=self.colors['success'])