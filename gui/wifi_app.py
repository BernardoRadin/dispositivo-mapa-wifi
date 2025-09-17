import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox
from collections import defaultdict

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
        
        # Interface
        self.point_labels = {}
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
                       font=('Segoe UI', 10, 'bold'),
                       padding=8,
                       relief='flat',
                       background=self.colors['primary'])
        
        style.configure('Primary.TButton',
                       background=self.colors['primary'],
                       foreground=self.colors['white'])
        
        style.configure('Success.TButton',
                       background=self.colors['success'],
                       foreground=self.colors['white'])
        
        style.configure('Danger.TButton',
                       background=self.colors['danger'],
                       foreground=self.colors['white'])
        
        # Estilo para labels
        style.configure('TLabel', 
                       font=('Segoe UI', 10),
                       background=self.colors['light'])
        
        style.configure('Header.TLabel',
                       font=('Segoe UI', 14, 'bold'),
                       foreground=self.colors['dark'])
        
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
                               text="📡 WiFi Scanner - Mapa de Calor",
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

        # Frame de progresso do local atual
        self._create_progress_frame(main_container)

        # Frame para lista de todos os locais
        self._create_list_frame(main_container)
        
        # Inicialização
        self.atualizar_redes()
        self.disable_controls()

    def _create_top_frame(self, parent):
        top_frame = ttk.Frame(parent, style='Card.TLabelframe')
        top_frame.pack(fill='x', pady=(0, 10))
        
        # Frame para controles de local e ponto (lado esquerdo)
        controls_frame = ttk.LabelFrame(top_frame, text="📍 Local e Ponto", 
                                       style='Card.TLabelframe', padding=15)
        controls_frame.pack(side='left', fill='x', expand=True, padx=(0, 10))
        
        self._create_controls(controls_frame)
        
        # Frame para seleção de WiFi (lado direito)
        wifi_frame = ttk.LabelFrame(top_frame, text="📶 Seleção de Rede Wi-Fi", 
                                   style='Card.TLabelframe', padding=15)
        wifi_frame.pack(side='right', fill='x', expand=True)
        
        self._create_wifi_controls(wifi_frame)

    def _create_controls(self, parent):
        # Primeira linha - Local
        ttk.Label(parent, text="🏠 Local:", font=('Segoe UI', 10, 'bold')).grid(row=0, column=0, sticky='w', padx=(0, 8), pady=5)
        self.combo_local = ttk.Combobox(parent, state='readonly', width=18,
                                        values=["Banheiro", "Sala", "Corredor", "Quarto", "Cozinha"],
                                        font=('Segoe UI', 10))
        self.combo_local.bind('<<ComboboxSelected>>', self.on_local_changed)
        self.combo_local.grid(row=0, column=1, sticky='w', padx=(0, 20), pady=5)
        
        # Instruções para o usuário
        ttk.Label(parent, text="📍 Clique nos pontos do grid abaixo para medir automaticamente", 
                 font=('Segoe UI', 9), foreground=self.colors['info']).grid(row=0, column=2, columnspan=2, sticky='w', pady=5)
        
        # Segunda linha - Botões de ação
        self._create_buttons(parent)

    def _create_buttons(self, parent):
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=1, column=0, columnspan=4, pady=(15, 0), sticky='w')
        
        # Botões - removido o botão de medição manual
        self.btn_manual = ttk.Button(button_frame, text="✏️ Inserir Manual", 
                                    command=self.insert_manual, style='Success.TButton')
        self.btn_manual.pack(side='left', padx=(0, 8))
        
        self.btn_clear_all = ttk.Button(button_frame, text="🗑️ Limpar Tudo", 
                                       command=self.clear_all, style='Danger.TButton')
        self.btn_clear_all.pack(side='left', padx=(0, 8))
        
        self.btn_heatmap = ttk.Button(button_frame, text="🗺️ Gerar Mapa", 
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
        self.combo_local.config(state='disabled')
        self.btn_manual.config(state='disabled')
        self.btn_clear_all.config(state='disabled')
        self.btn_heatmap.config(state='disabled')
        
    def enable_controls(self):
        self.combo_local.config(state='readonly')
        self.btn_manual.config(state='normal')
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

    def on_local_changed(self, event=None):
        self.current_local = self.combo_local.get()
        self.update_point_grid_buttons()
        if self.ssid_selecionado:
            self.status_label.config(text=f"🏠 Local: {self.current_local} - Clique nos pontos do grid para medir automaticamente", 
                                   foreground=self.colors['primary'])

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
        point_frame = ttk.Frame(frame)
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
        btn_frame = ttk.Frame(frame)
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
        if messagebox.askyesno("🗑️ Limpar Tudo", "Tem certeza que deseja limpar TODAS as medições de todos os locais?\n\nEsta ação não pode ser desfeita."):
            self.measurements.clear()
            self.update_point_grid_buttons()
            self.update_tree()
            if self.ssid_selecionado:
                self.status_label.config(text=f"🗑️ Todas as medições foram removidas - Pronto para novas medições com {self.ssid_selecionado}", 
                                       foreground=self.colors['warning'])

    def show_heatmap(self):
        self.heatmap_generator.generate_heatmap(self.measurements, self.ssid_selecionado, self.load_example_data)

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