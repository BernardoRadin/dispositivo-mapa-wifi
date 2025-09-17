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
        self.root.title("WiFi Scanner - 5 Pontos por Local")
        self.root.geometry("800x600")
        
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

    def create_widgets(self):
        # Container principal para organizar os frames
        main_container = ttk.Frame(self.root)
        main_container.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Frame superior para controles
        self._create_top_frame(main_container)
        
        # Status
        self.status_label = ttk.Label(main_container, text="Selecione uma rede Wi-Fi para começar", 
                                     font=('Arial', 10))
        self.status_label.pack(pady=5)

        # Frame de progresso do local atual
        self._create_progress_frame(main_container)

        # Frame para lista de todos os locais
        self._create_list_frame(main_container)
        
        # Inicialização
        self.atualizar_redes()
        self.disable_controls()

    def _create_top_frame(self, parent):
        top_frame = ttk.Frame(parent)
        top_frame.pack(fill='x', pady=(0, 5))
        
        # Frame para controles de local e ponto (lado esquerdo)
        controls_frame = ttk.LabelFrame(top_frame, text="Local e Ponto", padding=10)
        controls_frame.pack(side='left', fill='x', expand=True, anchor='n')
        
        self._create_controls(controls_frame)
        
        # Frame para seleção de WiFi (lado direito)
        wifi_frame = ttk.LabelFrame(top_frame, text="Seleção de Rede Wi-Fi", padding=10)
        wifi_frame.pack(side='right', padx=(10, 0), anchor='n')
        
        self._create_wifi_controls(wifi_frame)

    def _create_controls(self, parent):
        # Primeira linha - Local e Ponto
        ttk.Label(parent, text="Local:").grid(row=0, column=0, sticky='w', padx=(0, 5))
        self.combo_local = ttk.Combobox(parent, state='readonly', width=15,
                                        values=["Banheiro", "Sala", "Corredor", "Quarto", "Cozinha"])
        self.combo_local.bind('<<ComboboxSelected>>', self.on_local_changed)
        self.combo_local.grid(row=0, column=1, sticky='w', padx=(0, 20))
        
        ttk.Label(parent, text="Ponto:").grid(row=0, column=2, sticky='w', padx=(0, 5))
        self.combo_ponto = ttk.Combobox(parent, state='readonly', width=20,
                                        values=["Ponto 1 (Centro)", "Ponto 2 (Superior Direito)", 
                                                "Ponto 3 (Superior Esquerdo)", "Ponto 4 (Inferior Direito)", 
                                                "Ponto 5 (Inferior Esquerdo)"])
        self.combo_ponto.grid(row=0, column=3, sticky='w')
        
        # Segunda linha - Botões de ação
        self._create_buttons(parent)

    def _create_buttons(self, parent):
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=1, column=0, columnspan=4, pady=(10, 0), sticky='w')
        
        self.btn_measure = ttk.Button(button_frame, text="Medir Ponto", command=self.measure_point)
        self.btn_measure.pack(side='left', padx=(0, 5))
        
        self.btn_manual = ttk.Button(button_frame, text="Inserir Manual", command=self.insert_manual)
        self.btn_manual.pack(side='left', padx=(0, 5))
        
        self.btn_clear_all = ttk.Button(button_frame, text="Limpar Tudo", command=self.clear_all)
        self.btn_clear_all.pack(side='left', padx=(0, 5))
        
        self.btn_heatmap = ttk.Button(button_frame, text="Gerar Mapa de Calor", command=self.show_heatmap)
        self.btn_heatmap.pack(side='left')

    def _create_wifi_controls(self, parent):
        ttk.Label(parent, text="Rede:").grid(row=0, column=0, sticky='w', padx=(0, 5))
        self.combo_wifi = ttk.Combobox(parent, state='readonly', width=20)
        self.combo_wifi.grid(row=0, column=1, sticky='w', padx=(0, 10))
        self.combo_wifi.bind("<<ComboboxSelected>>", self.on_wifi_changed)
        
        btn_atualizar = ttk.Button(parent, text="🔄 Atualizar", command=self.atualizar_redes)
        btn_atualizar.grid(row=0, column=2)

    def _create_progress_frame(self, parent):
        self.progress_frame = ttk.LabelFrame(parent, text="Progresso do Local Atual", padding=10)
        self.progress_frame.pack(fill='x', pady=5)
        self.create_point_grid()

    def _create_list_frame(self, parent):
        list_frame = ttk.LabelFrame(parent, text="Todos os Locais Medidos", padding=10)
        list_frame.pack(fill='both', expand=True, pady=5)

        # Treeview para mostrar todos os locais
        self.tree = ttk.Treeview(list_frame, columns=("local", "pontos", "media"), show='headings', height=8)
        self.tree.heading("local", text="Local")
        self.tree.heading("pontos", text="Pontos Medidos")
        self.tree.heading("media", text="Média (dBm)")
        
        self.tree.column("local", width=120, anchor='w')
        self.tree.column("pontos", width=120, anchor='center')
        self.tree.column("media", width=120, anchor='center')

        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

    def disable_controls(self):
        self.combo_local.config(state='disabled')
        self.combo_ponto.config(state='disabled')
        self.btn_measure.config(state='disabled')
        self.btn_manual.config(state='disabled')
        self.btn_clear_all.config(state='disabled')
        self.btn_heatmap.config(state='disabled')
        
    def enable_controls(self):
        self.combo_local.config(state='readonly')
        self.combo_ponto.config(state='readonly')
        self.btn_measure.config(state='normal')
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
            self.status_label.config(text="Selecione uma rede Wi-Fi para começar")
        else:
            # Se já havia uma rede selecionada e há medições, limpar tudo
            if self.ssid_selecionado is not None and self.measurements:
                self.measurements.clear()
                self.update_point_grid()
                self.update_tree()
            
            self.ssid_selecionado = selected
            self.enable_controls()
            self.status_label.config(text=f"Rede selecionada: {self.ssid_selecionado} - Selecione um local e ponto")
            print(f"Rede selecionada: {self.ssid_selecionado}")

    def create_point_grid(self):
        # Limpar labels anteriores
        for label in self.point_labels.values():
            label.destroy()
        self.point_labels.clear()

        # Layout em cruz: 
        #   NO    NE
        #     Centro
        #   SO    SE
        positions = [
            ("Ponto 1 (Centro)", 1, 1),
            ("Ponto 2 (Superior Direito)", 0, 2),
            ("Ponto 3 (Superior Esquerdo)", 0, 0),
            ("Ponto 4 (Inferior Direito)", 2, 2),
            ("Ponto 5 (Inferior Esquerdo)", 2, 0)
        ]

        for point_name, row, col in positions:
            label = ttk.Label(self.progress_frame, text=f"{point_name}\nNão medido", 
                             relief='sunken', width=15, anchor='center',
                             background='lightgray')
            label.grid(row=row, column=col, padx=5, pady=5, sticky='nsew')
            self.point_labels[point_name] = label

        # Configurar grid para expandir
        for i in range(3):
            self.progress_frame.grid_columnconfigure(i, weight=1)
            self.progress_frame.grid_rowconfigure(i, weight=1)

    def on_local_changed(self, event=None):
        self.current_local = self.combo_local.get()
        self.update_point_grid()
        if self.ssid_selecionado:
            self.status_label.config(text=f"Rede: {self.ssid_selecionado} - Local: {self.current_local}")

    def update_point_grid(self):
        if not self.current_local:
            return

        local_data = self.measurements.get(self.current_local, {})
        
        for point_name, label in self.point_labels.items():
            if point_name in local_data:
                measurement = local_data[point_name]
                dbm = measurement['dbm']
                if dbm != "N/A":
                    percent = signal_dbm_to_percent(dbm)
                    color = dbm_to_color(dbm)
                    bg_color = {'red': '#ffcccc', 'orange': '#ffedcc', 'green': '#ccffcc'}[color]
                    label.config(text=f"{point_name}\n{dbm} dBm ({percent}%)", 
                               background=bg_color)
                else:
                    label.config(text=f"{point_name}\nSem sinal", background='#ffcccc')
            else:
                label.config(text=f"{point_name}\nNão medido", background='lightgray')

    def measure_point(self):
        if not self.ssid_selecionado:
            messagebox.showerror("Erro", "Selecione uma rede Wi-Fi")
            return
            
        if not self.combo_local.get():
            messagebox.showerror("Erro", "Selecione um local")
            return
        
        if not self.combo_ponto.get():
            messagebox.showerror("Erro", "Selecione um ponto")
            return

        local = self.combo_local.get()
        ponto = self.combo_ponto.get()

        # Fazer medição
        self.btn_measure.config(state='disabled')
        self.status_label.config(text="Medindo sinal Wi-Fi...")
        self.root.update()

        # Fazer scan em thread separada
        def scan_thread():
            sig = self.scanner.scan_once(self.ssid_selecionado)
            self.root.after(0, lambda: self.update_measurement_result(local, ponto, sig))

        thread = threading.Thread(target=scan_thread, daemon=True)
        thread.start()

    def insert_manual(self):
        if not self.ssid_selecionado:
            messagebox.showerror("Erro", "Selecione uma rede Wi-Fi")
            return
            
        if not self.combo_local.get():
            messagebox.showerror("Erro", "Selecione um local")
            return
        
        if not self.combo_ponto.get():
            messagebox.showerror("Erro", "Selecione um ponto")
            return

        local = self.combo_local.get()
        ponto = self.combo_ponto.get()

        # Criar janela para inserir valor manual
        manual_window = tk.Toplevel(self.root)
        manual_window.title("Inserir Valor Manual")
        manual_window.geometry("350x200")
        manual_window.transient(self.root)
        manual_window.grab_set()

        # Centralizar a janela
        manual_window.geometry("+%d+%d" % (self.root.winfo_rootx() + 50, self.root.winfo_rooty() + 50))

        frame = ttk.Frame(manual_window, padding=20)
        frame.pack(fill='both', expand=True)

        ttk.Label(frame, text=f"Rede: {self.ssid_selecionado}", font=('Arial', 10)).pack(pady=2)
        ttk.Label(frame, text=f"Local: {local}", font=('Arial', 12, 'bold')).pack(pady=2)
        ttk.Label(frame, text=f"Ponto: {ponto}", font=('Arial', 12, 'bold')).pack(pady=2)

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

                # Atualizar interface
                self.current_local = local
                self.update_point_grid()
                self.update_tree()

                # Verificar se completou os 5 pontos
                points_measured = len(self.measurements[local])
                self.status_label.config(text=f"Rede: {self.ssid_selecionado} - {local}: {points_measured}/5 pontos (Manual: {dbm_value} dBm)")

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

    def update_measurement_result(self, local, ponto, sig):
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

        # Atualizar interface
        self.current_local = local
        self.update_point_grid()
        self.update_tree()

        # Verificar se completou os 5 pontos
        points_measured = len(self.measurements[local])
        self.status_label.config(text=f"Rede: {self.ssid_selecionado} - {local}: {points_measured}/5 pontos medidos")

        self.btn_measure.config(state='normal')

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

            self.tree.insert('', 'end', values=(local, f"{points_count}/5", avg_str))

    def clear_all(self):
        if messagebox.askyesno("Confirmar", "Limpar todas as medições de todos os locais?"):
            self.measurements.clear()
            self.update_point_grid()
            self.update_tree()
            if self.ssid_selecionado:
                self.status_label.config(text=f"Rede: {self.ssid_selecionado} - Todas as medições foram removidas")

    def show_heatmap(self):
        self.heatmap_generator.generate_heatmap(self.measurements, self.ssid_selecionado, self.load_example_data)

    def load_example_data(self):
        if not self.ssid_selecionado:
            messagebox.showerror("Erro", "Selecione uma rede Wi-Fi primeiro")
            return
            
        if messagebox.askyesno("Carregar Dados", "Isso irá substituir todas as medições atuais. Continuar?"):
            self.measurements.clear()
            
            # Dados de exemplo
            example_data = {
                "Sala": {
                    "Ponto 1 (Centro)": {'dbm': -45, 'percent': 90, 'timestamp': '10:00:00'},
                    "Ponto 2 (Superior Direito)": {'dbm': -48, 'percent': 86, 'timestamp': '10:01:00'},
                    "Ponto 3 (Superior Esquerdo)": {'dbm': -42, 'percent': 96, 'timestamp': '10:02:00'},
                    "Ponto 4 (Inferior Direito)": {'dbm': -50, 'percent': 80, 'timestamp': '10:03:00'},
                    "Ponto 5 (Inferior Esquerdo)": {'dbm': -47, 'percent': 88, 'timestamp': '10:04:00'}
                },
                "Quarto": {
                    "Ponto 1 (Centro)": {'dbm': -55, 'percent': 70, 'timestamp': '10:05:00'},
                    "Ponto 2 (Superior Direito)": {'dbm': -58, 'percent': 64, 'timestamp': '10:06:00'},
                    "Ponto 3 (Superior Esquerdo)": {'dbm': -52, 'percent': 76, 'timestamp': '10:07:00'},
                    "Ponto 4 (Inferior Direito)": {'dbm': -60, 'percent': 60, 'timestamp': '10:08:00'},
                    "Ponto 5 (Inferior Esquerdo)": {'dbm': -56, 'percent': 68, 'timestamp': '10:09:00'}
                },
                "Cozinha": {
                    "Ponto 1 (Centro)": {'dbm': -65, 'percent': 40, 'timestamp': '10:10:00'},
                    "Ponto 2 (Superior Direito)": {'dbm': -68, 'percent': 34, 'timestamp': '10:11:00'},
                    "Ponto 3 (Superior Esquerdo)": {'dbm': -62, 'percent': 46, 'timestamp': '10:12:00'},
                    "Ponto 4 (Inferior Direito)": {'dbm': -70, 'percent': 30, 'timestamp': '10:13:00'},
                    "Ponto 5 (Inferior Esquerdo)": {'dbm': -67, 'percent': 36, 'timestamp': '10:14:00'}
                }
            }
            
            self.measurements.update(example_data)
            self.update_point_grid()
            self.update_tree()
            self.status_label.config(text=f"Rede: {self.ssid_selecionado} - Dados de exemplo carregados")