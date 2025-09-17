import threading
import time
import pywifi
from pywifi import PyWiFi
import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from collections import defaultdict

SSID_TARGET = ".URI-C2"

def signal_dbm_to_percent(dbm):
    try:
        val = float(dbm)
    except Exception:
        return 0
    if val <= -100:
        return 0
    if val >= -50:
        return 100
    return max(0, min(100, int(round(2 * (val + 100)))))

def signal_to_color(pct):
    # Baseado em dBm, não em porcentagem
    # Esta função será atualizada para usar dBm diretamente
    if pct <= 33:
        return "red"
    elif pct <= 66:
        return "orange"
    else:
        return "green"

def dbm_to_color(dbm):
    """Converte dBm para cor baseado nas suas especificações corretas"""
    if dbm == "N/A" or dbm is None:
        return "red"
    
    try:
        dbm_val = float(dbm)
        if dbm_val >= -30:  # -30 ou melhor = Verde (excelente)
            return "green"
        elif dbm_val >= -49:  # -30 a -49 = Amarelo (bom)  
            return "orange"
        elif dbm_val >= -60:  # -50 a -60 = Vermelho (ruim)
            return "red"
        else:  # Pior que -60 = Vermelho escuro (muito ruim)
            return "red"
    except:
        return "red"

class WifiScanner:
    def __init__(self):
        self.wifi = PyWiFi()
        self.iface = self.wifi.interfaces()[0] if self.wifi.interfaces() else None

    def scan_once(self):
        if self.iface is None:
            return None
        try:
            self.iface.scan()
            time.sleep(1.0)
            raw = self.iface.scan_results()
        except Exception:
            return None

        best_signal = None
        for r in raw:
            if r.ssid == SSID_TARGET:
                sig = getattr(r, 'signal', None)
                if sig is not None and (best_signal is None or sig > best_signal):
                    best_signal = sig
        return best_signal

class WifiMapApp:
    def __init__(self, root):
        self.root = root
        self.root.title("WiFi Scanner - 5 Pontos por Local")
        self.root.geometry("700x600")
        self.scanner = WifiScanner()
        self.create_widgets()

        # Estrutura de dados: {local: {ponto: {dbm, percent, timestamp}}}
        self.measurements = defaultdict(dict)
        self.current_local = None

    def create_widgets(self):
        # Frame superior com controles
        frame_top = ttk.LabelFrame(self.root, text="Seleção de Local e Ponto", padding=10)
        frame_top.pack(fill='x', padx=10, pady=5)

        # Seleção de local
        ttk.Label(frame_top, text="Local:").grid(row=0, column=0, sticky='w', padx=(0, 10))
        self.combo_local = ttk.Combobox(frame_top, state='readonly', width=15,
                                       values=["Banheiro", "Sala", "Corredor", "Quarto", "Cozinha"])
        self.combo_local.bind('<<ComboboxSelected>>', self.on_local_changed)
        self.combo_local.grid(row=0, column=1, sticky='w')

        # Seleção de ponto
        ttk.Label(frame_top, text="Ponto:").grid(row=0, column=2, sticky='w', padx=(20, 10))
        self.combo_ponto = ttk.Combobox(frame_top, state='readonly', width=15,
                                       values=["Ponto 1 (Centro)", "Ponto 2 (Superior Direito)", 
                                              "Ponto 3 (Superior Esquerdo)", "Ponto 4 (Inferior Direito)", 
                                              "Ponto 5 (Inferior Esquerdo)"])
        self.combo_ponto.grid(row=0, column=3, sticky='w')

        # Botões de controle
        button_frame = ttk.Frame(frame_top)
        button_frame.grid(row=1, column=0, columnspan=4, pady=(10, 0))

        self.btn_measure = ttk.Button(button_frame, text="Medir Ponto", command=self.measure_point)
        self.btn_measure.pack(side='left', padx=(0, 10))

        self.btn_manual = ttk.Button(button_frame, text="Inserir Manual", command=self.insert_manual)
        self.btn_manual.pack(side='left', padx=(0, 10))

        self.btn_clear_all = ttk.Button(button_frame, text="Limpar Tudo", command=self.clear_all)
        self.btn_clear_all.pack(side='left', padx=(0, 10))

        self.btn_heatmap = ttk.Button(button_frame, text="Gerar Mapa de Calor", command=self.show_heatmap)
        self.btn_heatmap.pack(side='left')

        # Segunda linha de botões
        button_frame2 = ttk.Frame(frame_top)
        button_frame2.grid(row=2, column=0, columnspan=4, pady=(5, 0))

        # Status
        self.status_label = ttk.Label(self.root, text="Selecione um local e ponto para começar", 
                                     font=('Arial', 10))
        self.status_label.pack(pady=5)

        # Frame de progresso do local atual
        self.progress_frame = ttk.LabelFrame(self.root, text="Progresso do Local Atual", padding=10)
        self.progress_frame.pack(fill='x', padx=10, pady=5)

        # Grid para mostrar os 5 pontos
        self.point_labels = {}
        self.create_point_grid()

        # Frame para lista de todos os locais
        list_frame = ttk.LabelFrame(self.root, text="Todos os Locais Medidos", padding=10)
        list_frame.pack(fill='both', expand=True, padx=10, pady=5)

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

    def create_point_grid(self):
        """Cria o grid visual dos 5 pontos"""
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
        """Chamado quando o local é alterado"""
        self.current_local = self.combo_local.get()
        self.update_point_grid()
        self.status_label.config(text=f"Local selecionado: {self.current_local}")

    def update_point_grid(self):
        """Atualiza o grid de pontos para o local atual"""
        if not self.current_local:
            return

        local_data = self.measurements.get(self.current_local, {})
        
        for point_name, label in self.point_labels.items():
            if point_name in local_data:
                measurement = local_data[point_name]
                dbm = measurement['dbm']
                if dbm != "N/A":
                    percent = signal_dbm_to_percent(dbm)
                    color = dbm_to_color(dbm)  # Usar função baseada em dBm
                    bg_color = {'red': '#ffcccc', 'orange': '#ffedcc', 'green': '#ccffcc'}[color]
                    label.config(text=f"{point_name}\n{dbm} dBm ({percent}%)", 
                               background=bg_color)
                else:
                    label.config(text=f"{point_name}\nSem sinal", background='#ffcccc')
            else:
                label.config(text=f"{point_name}\nNão medido", background='lightgray')

    def measure_point(self):
        """Mede o ponto selecionado"""
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
            sig = self.scanner.scan_once()
            self.root.after(0, lambda: self.update_measurement_result(local, ponto, sig))

        thread = threading.Thread(target=scan_thread, daemon=True)
        thread.start()

    def insert_manual(self):
        """Permite inserir valores dBm manualmente"""
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

        ttk.Label(frame, text=f"Local: {local}", font=('Arial', 12, 'bold')).pack(pady=5)
        ttk.Label(frame, text=f"Ponto: {ponto}", font=('Arial', 12, 'bold')).pack(pady=5)

        ttk.Label(frame, text="Valor RSSI (dBm):", font=('Arial', 10)).pack(pady=(20, 5))
        
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
                self.status_label.config(text=f"{local}: {points_measured}/5 pontos medidos (Manual: {dbm_value} dBm)")

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
        """Atualiza o resultado da medição"""
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
        self.status_label.config(text=f"{local}: {points_measured}/5 pontos medidos")

        self.btn_measure.config(state='normal')

    def update_tree(self):
        """Atualiza a árvore de locais"""
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
        """Limpa todas as medições"""
        if messagebox.askyesno("Confirmar", "Limpar todas as medições de todos os locais?"):
            self.measurements.clear()
            self.update_point_grid()
            self.update_tree()
            self.status_label.config(text="Todas as medições foram removidas")

    def show_heatmap(self):
        """Gera e exibe o mapa de calor"""
        # Verificar se há dados suficientes
        complete_locations = [local for local, points in self.measurements.items() if len(points) == 5]
        
        if len(complete_locations) < 1:
            messagebox.showwarning("Aviso", "É necessário pelo menos 1 local com todos os 5 pontos medidos")
            return

        # Criar janela do mapa
        heatmap_window = tk.Toplevel(self.root)
        heatmap_window.title("Mapa de Calor Wi-Fi - 5 Pontos")
        heatmap_window.geometry("800x800")

        # Processar dados para o mapa
        x_coords = []
        y_coords = []
        dbm_values = []
        location_labels = []

        # Posições relativas dos pontos (em metros)
        point_positions = {
            "Ponto 1 (Centro)": (0, 0),
            "Ponto 2 (Superior Direito)": (2, 2),
            "Ponto 3 (Superior Esquerdo)": (-2, 2),
            "Ponto 4 (Inferior Direito)": (2, -2),
            "Ponto 5 (Inferior Esquerdo)": (-2, -2)
        }

        # Posições base dos locais
        location_positions = {
            "Banheiro": (0, 0),
            "Sala": (6, 0),
            "Quarto": (0, 6),
            "Cozinha": (6, 6),
            "Corredor": (3, 3)
        }

        # Coletar todos os pontos
        for local in complete_locations:
            base_x, base_y = location_positions.get(local, (0, 0))
            
            for point, measurement in self.measurements[local].items():
                if measurement['dbm'] != 'N/A':
                    point_x, point_y = point_positions[point]
                    x_coords.append(base_x + point_x)
                    y_coords.append(base_y + point_y)
                    dbm_values.append(float(measurement['dbm']))
                    location_labels.append(f"{local}\n{point}")

        if len(x_coords) < 5:
            messagebox.showwarning("Aviso", "Dados insuficientes para gerar o mapa")
            return

        # Criar figura matplotlib
        fig, ax = plt.subplots(figsize=(14, 10))

        # Criar grid para interpolação
        x_min, x_max = min(x_coords) - 3, max(x_coords) + 3
        y_min, y_max = min(y_coords) - 3, max(y_coords) + 3

        xi = np.linspace(x_min, x_max, 100)
        yi = np.linspace(y_min, y_max, 100)
        Xi, Yi = np.meshgrid(xi, yi)

        # Interpolação
        Zi = np.zeros_like(Xi)
        for i in range(len(xi)):
            for j in range(len(yi)):
                distances = np.sqrt((np.array(x_coords) - xi[i])**2 + (np.array(y_coords) - yi[j])**2)
                if np.min(distances) < 0.1:
                    closest_idx = np.argmin(distances)
                    Zi[j, i] = dbm_values[closest_idx]
                else:
                    weights = 1 / (distances + 0.1)
                    Zi[j, i] = np.sum(weights * np.array(dbm_values)) / np.sum(weights)

        # Criar mapa de calor com escala correta
        # Inverter o colormap para que verde seja melhor sinal
        contour = ax.contourf(Xi, Yi, Zi, levels=20, cmap='RdYlGn', alpha=0.8)

        # Contornos das zonas
        contour_lines = ax.contour(Xi, Yi, Zi, levels=[-60, -49, -30], colors=['black'], linewidths=2, linestyles='--')
        ax.clabel(contour_lines, inline=True, fontsize=10, fmt='%d dBm')

        # Pontos medidos com escala correta
        scatter = ax.scatter(x_coords, y_coords, c=dbm_values, cmap='RdYlGn', 
                           s=150, edgecolors='black', linewidth=2, zorder=10)

        # Mostrar TODOS os rótulos dos pontos com nome completo
        for i, (x, y, dbm, label) in enumerate(zip(x_coords, y_coords, dbm_values, location_labels)):
            # Extrair nome do local e ponto do label
            parts = label.split('\n')
            local_name = parts[0]
            point_name = parts[1] if len(parts) > 1 else ""
            
            # Criar rótulo mais limpo
            clean_label = f"{local_name}\n{point_name}\n{dbm:.0f} dBm"
            
            ax.annotate(clean_label, (x, y), xytext=(8, 8), textcoords='offset points',
                       bbox=dict(boxstyle='round,pad=0.4', facecolor='white', alpha=0.9, edgecolor='black'),
                       fontsize=9, fontweight='bold', ha='left')

        # Configurar gráfico
        ax.set_xlabel('Posição X (metros)', fontsize=12)
        ax.set_ylabel('Posição Y (metros)', fontsize=12)
        ax.set_title('Mapa de Calor Wi-Fi - 5 Pontos por Local\n' + 
                    'Verde: ≥ -30 dBm (Excelente) | Amarelo: -30 a -49 dBm (Bom) | Vermelho: ≤ -50 dBm (Ruim)', 
                    fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.set_aspect('equal')

        # Barra de cores
        cbar = plt.colorbar(contour, ax=ax, shrink=0.8)
        cbar.set_label('RSSI (dBm)', fontsize=12)

        # Integrar com Tkinter
        canvas = FigureCanvasTkAgg(fig, heatmap_window)
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Estatísticas
        stats_frame = ttk.Frame(heatmap_window)
        stats_frame.pack(fill='x', padx=10, pady=5)

        min_dbm = min(dbm_values)
        max_dbm = max(dbm_values)
        avg_dbm = sum(dbm_values) / len(dbm_values)

        stats_text = f"Estatísticas: Mín: {min_dbm:.1f} dBm | Máx: {max_dbm:.1f} dBm | Média: {avg_dbm:.1f} dBm | Pontos: {len(dbm_values)} | Locais: {len(complete_locations)}"
        ttk.Label(stats_frame, text=stats_text, font=('Arial', 10)).pack()

        # Botão salvar
        def save_heatmap():
            from tkinter import filedialog
            filename = filedialog.asksaveasfilename(
                defaultextension=".png",
                filetypes=[("PNG files", "*.png"), ("PDF files", "*.pdf")]
            )
            if filename:
                fig.savefig(filename, dpi=300, bbox_inches='tight')
                messagebox.showinfo("Sucesso", f"Mapa salvo: {filename}")

        # Botão salvar e pré-carregar dados de exemplo
        button_frame = ttk.Frame(stats_frame)
        button_frame.pack(pady=5)

        ttk.Button(button_frame, text="Salvar Mapa", command=save_heatmap).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Carregar Dados Exemplo", command=self.load_example_data).pack(side='left', padx=5)

def main():
    try:
        import matplotlib
        matplotlib.use('TkAgg')
    except ImportError:
        print("Aviso: matplotlib não encontrado. Instale com: pip install matplotlib")
    
    root = tk.Tk()
    app = WifiMapApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()