import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

class HeatmapGenerator:
    def __init__(self, parent_window):
        self.parent = parent_window
        
        # Posições relativas dos pontos (em metros) - 4x4 grid
        self.point_positions = {}
        grid_size = 4
        spacing = 1.0  # 1 metro entre pontos
        
        for row in range(grid_size):
            for col in range(grid_size):
                point_num = row * grid_size + col + 1
                point_name = f"Ponto {point_num}"
                # Centralizar o grid em torno de (0,0)
                x_pos = (col - (grid_size-1)/2) * spacing
                y_pos = ((grid_size-1)/2 - row) * spacing  # Inverter Y para que row 0 seja no topo
                self.point_positions[point_name] = (x_pos, y_pos)

        # Posições base dos locais
        self.location_positions = {
            "Banheiro": (0, 0),
            "Sala": (6, 0),
            "Quarto": (0, 6),
            "Cozinha": (6, 6),
            "Corredor": (3, 3)
        }

    def generate_heatmap(self, measurements, ssid, load_example_callback):
        if not ssid:
            messagebox.showerror("Erro", "Selecione uma rede Wi-Fi")
            return
            
        # Verificar se há dados suficientes
        complete_locations = [local for local, points in measurements.items() if len(points) == 16]
        
        if len(complete_locations) < 1:
            messagebox.showwarning("Aviso", "É necessário pelo menos 1 local com todos os 16 pontos medidos")
            return

        # Criar janela do mapa
        heatmap_window = tk.Toplevel(self.parent)
        heatmap_window.title(f"Mapa de Calor Wi-Fi - {ssid}")
        heatmap_window.geometry("800x800")

        # Processar dados para o mapa
        x_coords, y_coords, dbm_values, location_labels = self._process_data(measurements, complete_locations)

        if len(x_coords) < 5:
            messagebox.showwarning("Aviso", "Dados insuficientes para gerar o mapa")
            return

        # Criar e configurar o gráfico
        fig, ax = self._create_plot(x_coords, y_coords, dbm_values, location_labels, ssid)
        
        # Integrar com Tkinter
        canvas = FigureCanvasTkAgg(fig, heatmap_window)
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Adicionar estatísticas e botões
        self._add_statistics_and_buttons(heatmap_window, dbm_values, ssid, complete_locations, fig, load_example_callback)

    def _process_data(self, measurements, complete_locations):
        x_coords = []
        y_coords = []
        dbm_values = []
        location_labels = []

        # Coletar todos os pontos
        for local in complete_locations:
            base_x, base_y = self.location_positions.get(local, (0, 0))
            
            for point, measurement in measurements[local].items():
                if measurement['dbm'] != 'N/A':
                    point_x, point_y = self.point_positions[point]
                    x_coords.append(base_x + point_x)
                    y_coords.append(base_y + point_y)
                    dbm_values.append(float(measurement['dbm']))
                    location_labels.append(f"{local}\n{point}")
                    
        return x_coords, y_coords, dbm_values, location_labels

    def _create_plot(self, x_coords, y_coords, dbm_values, location_labels, ssid):
        # Criar figura matplotlib
        fig, ax = plt.subplots(figsize=(14, 10))

        # Criar grid para interpolação
        x_min, x_max = min(x_coords) - 3, max(x_coords) + 3
        y_min, y_max = min(y_coords) - 3, max(y_coords) + 3

        xi = np.linspace(x_min, x_max, 100)
        yi = np.linspace(y_min, y_max, 100)
        Xi, Yi = np.meshgrid(xi, yi)

        # Interpolação
        Zi = self._interpolate_data(xi, yi, Xi, Yi, x_coords, y_coords, dbm_values)

        # Criar mapa de calor com escala correta
        contour = ax.contourf(Xi, Yi, Zi, levels=20, cmap='RdYlGn', alpha=0.8)

        # Contornos das zonas
        contour_lines = ax.contour(Xi, Yi, Zi, levels=[-60, -49, -30], colors=['black'], linewidths=2, linestyles='--')
        ax.clabel(contour_lines, inline=True, fontsize=10, fmt='%d dBm')

        # Pontos medidos com escala correta
        scatter = ax.scatter(x_coords, y_coords, c=dbm_values, cmap='RdYlGn', 
                           s=150, edgecolors='black', linewidth=2, zorder=10)

        # Adicionar rótulos
        self._add_labels(ax, x_coords, y_coords, dbm_values, location_labels)

        # Configurar gráfico
        self._configure_plot(ax, ssid)

        # Barra de cores
        cbar = plt.colorbar(contour, ax=ax, shrink=0.8)
        cbar.set_label('RSSI (dBm)', fontsize=12)

        return fig, ax

    def _interpolate_data(self, xi, yi, Xi, Yi, x_coords, y_coords, dbm_values):
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
        return Zi

    def _add_labels(self, ax, x_coords, y_coords, dbm_values, location_labels):
        for x, y, dbm, label in zip(x_coords, y_coords, dbm_values, location_labels):
            # Extrair nome do local e ponto do label
            parts = label.split('\n')
            local_name = parts[0]
            point_name = parts[1] if len(parts) > 1 else ""
            
            # Criar rótulo mais limpo
            clean_label = f"{local_name}\n{point_name}\n{dbm:.0f} dBm"
            
            ax.annotate(clean_label, (x, y), xytext=(8, 8), textcoords='offset points',
                       bbox=dict(boxstyle='round,pad=0.4', facecolor='white', alpha=0.9, edgecolor='black'),
                       fontsize=9, fontweight='bold', ha='left')

    def _configure_plot(self, ax, ssid):
        ax.set_xlabel('Posição X (metros)', fontsize=12)
        ax.set_ylabel('Posição Y (metros)', fontsize=12)
        ax.set_title(f'Mapa de Calor Wi-Fi - {ssid}\n' + 
                    'Verde: ≥ -30 dBm (Excelente) | Amarelo: -30 a -49 dBm (Bom) | Vermelho: ≤ -50 dBm (Ruim)', 
                    fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.set_aspect('equal')

    def _add_statistics_and_buttons(self, window, dbm_values, ssid, complete_locations, fig, load_example_callback):
        # Estatísticas
        stats_frame = ttk.Frame(window)
        stats_frame.pack(fill='x', padx=10, pady=5)

        min_dbm = min(dbm_values)
        max_dbm = max(dbm_values)
        avg_dbm = sum(dbm_values) / len(dbm_values)

        stats_text = f"Rede: {ssid} | Mín: {min_dbm:.1f} dBm | Máx: {max_dbm:.1f} dBm | Média: {avg_dbm:.1f} dBm | Pontos: {len(dbm_values)} | Locais: {len(complete_locations)}"
        ttk.Label(stats_frame, text=stats_text, font=('Arial', 10)).pack()

        # Botões
        button_frame = ttk.Frame(stats_frame)
        button_frame.pack(pady=5)

        def save_heatmap():
            filename = filedialog.asksaveasfilename(
                defaultextension=".png",
                filetypes=[("PNG files", "*.png"), ("PDF files", "*.pdf")]
            )
            if filename:
                fig.savefig(filename, dpi=300, bbox_inches='tight')
                messagebox.showinfo("Sucesso", f"Mapa salvo: {filename}")

        ttk.Button(button_frame, text="Salvar Mapa", command=save_heatmap).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Carregar Dados Exemplo", command=load_example_callback).pack(side='left', padx=5)