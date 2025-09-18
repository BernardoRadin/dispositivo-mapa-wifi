import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.colors as mcolors
import numpy as np

class HeatmapGenerator:
    def __init__(self, parent_window):
        self.parent = parent_window
        
        # Definir colormap customizado baseado nos valores dBm
        self.dbm_colors = [
            (-80, '#FF0000'),  # Vermelho
            (-70, '#FF4500'),  # Laranja avermelhado
            (-60, '#FFA500'),  # Laranja
            (-50, '#ADFF2F'),  # Amarelo esverdeado
            (-40, '#90EE90'),  # Verde claro
            (-30, '#00FFFF')   # Verde azulado/Ciano
        ]
        
        # Criar colormap customizado
        self.custom_cmap = self._create_custom_colormap()
        
        # Posições relativas dos pontos (em metros) - 4x4 grid
        
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

    def _create_custom_colormap(self):
        """Cria colormap customizado com gradientes suaves entre as cores dBm"""
        # Valores dBm e suas cores correspondentes com gradientes
        dbm_values = [-80, -70, -60, -50, -40, -30]
        colors = ['#FF0000', '#FF4500', '#FFA500', '#ADFF2F', '#90EE90', '#00FFFF']

        # Criar colormap com mais pontos para gradientes suaves
        # Adicionar pontos intermediários para transições suaves
        extended_colors = []
        extended_positions = []

        for i, color in enumerate(colors):
            extended_colors.append(color)
            extended_positions.append(i / (len(colors) - 1))

        # Criar colormap com gradientes suaves
        cmap = mcolors.LinearSegmentedColormap.from_list("custom_dbm_gradient", extended_colors, N=256)

        # Configurar boundaries para mapeamento preciso mas com gradientes
        boundaries = [-85, -75, -65, -55, -45, -35, -25]
        norm = mcolors.BoundaryNorm(boundaries, cmap.N)
        self.dbm_norm = norm

        return cmap

    def generate_heatmap(self, measurements, ssid, image_path=None, load_example_callback=None):
        if not ssid:
            messagebox.showerror("Erro", "Selecione uma rede Wi-Fi")
            return
            
        # Verificar se há dados suficientes
        valid_measurements = {k: v for k, v in measurements.items() if v.get('dbm', 'N/A') != 'N/A'}
        
        if len(valid_measurements) < 3:
            messagebox.showwarning("Aviso", "É necessário pelo menos 3 pontos medidos para gerar o mapa")
            return

        # Criar janela do mapa
        heatmap_window = tk.Toplevel(self.parent)
        heatmap_window.title(f"Mapa de Calor Wi-Fi - {ssid}")
        heatmap_window.geometry("1000x800")

        # Processar dados para o mapa
        x_coords, y_coords, dbm_values, point_labels = self._process_image_data(measurements)

        if len(x_coords) < 3:
            messagebox.showwarning("Aviso", "Dados insuficientes para gerar o mapa")
            return

        # Criar e configurar o gráfico
        fig, ax = self._create_plot_with_image(x_coords, y_coords, dbm_values, point_labels, ssid, image_path)
        
        # Integrar com Tkinter
        canvas = FigureCanvasTkAgg(fig, heatmap_window)
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Adicionar estatísticas e botões
        self._add_statistics_and_buttons(heatmap_window, dbm_values, ssid, len(valid_measurements), fig, load_example_callback)

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

    def _process_image_data(self, measurements):
        """Processa dados de medição com coordenadas de imagem"""
        x_coords = []
        y_coords = []
        dbm_values = []
        point_labels = []

        # Coletar todos os pontos válidos
        for point_name, measurement in measurements.items():
            if measurement.get('dbm', 'N/A') != 'N/A':
                coords = measurement.get('coordinates', (0, 0))
                x_coords.append(coords[0])
                y_coords.append(coords[1])
                dbm_values.append(float(measurement['dbm']))
                point_labels.append(point_name)
                
        return x_coords, y_coords, dbm_values, point_labels

    def _create_plot_with_image(self, x_coords, y_coords, dbm_values, point_labels, ssid, image_path):
        """Cria gráfico com imagem de fundo"""
        # Criar figura matplotlib
        fig, ax = plt.subplots(figsize=(14, 10))

        # Se temos imagem, usar como fundo
        if image_path:
            try:
                from PIL import Image
                import matplotlib.image as mpimg
                
                # Carregar imagem
                img = Image.open(image_path)
                
                # Obter dimensões da imagem
                img_width, img_height = img.size
                
                # Calcular limites baseados nos pontos
                x_min, x_max = min(x_coords), max(x_coords)
                y_min, y_max = min(y_coords), max(y_coords)
                
                # Adicionar margem
                margin_x = (x_max - x_min) * 0.1
                margin_y = (y_max - y_min) * 0.1
                
                # Exibir imagem como fundo
                ax.imshow(img, extent=[x_min-margin_x, x_max+margin_x, y_min-margin_y, y_max+margin_y], 
                         aspect='auto', alpha=0.3, origin='upper')
            except Exception as e:
                print(f"Aviso: Não foi possível carregar imagem de fundo: {e}")

        # Criar grid para interpolação
        x_min, x_max = min(x_coords) - 10, max(x_coords) + 10
        y_min, y_max = min(y_coords) - 10, max(y_coords) + 10

        xi = np.linspace(x_min, x_max, 100)
        yi = np.linspace(y_min, y_max, 100)
        Xi, Yi = np.meshgrid(xi, yi)

        # Interpolação
        Zi = self._interpolate_data(xi, yi, Xi, Yi, x_coords, y_coords, dbm_values)

        # Criar mapa de calor
        contour = ax.contourf(Xi, Yi, Zi, levels=50, cmap=self.custom_cmap, norm=self.dbm_norm, alpha=0.8)

        # Pontos medidos (sem bordas pretas)
        scatter = ax.scatter(x_coords, y_coords, c=dbm_values, cmap=self.custom_cmap, norm=self.dbm_norm,
                           s=120, edgecolors='white', linewidth=1, zorder=10)

        # Adicionar rótulos
        self._add_labels(ax, x_coords, y_coords, dbm_values, point_labels)

        # Configurar gráfico (título simplificado)
        ax.set_xlabel('Posição X (pixels)', fontsize=12)
        ax.set_ylabel('Posição Y (pixels)', fontsize=12)
        ax.set_title(f'Mapa de Calor Wi-Fi - {ssid}', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.set_aspect('equal')

        # Barra de cores limpa
        cbar = plt.colorbar(contour, ax=ax, shrink=0.8)
        cbar.set_label('RSSI (dBm)', fontsize=12)
        cbar.set_ticks([-80, -70, -60, -50, -40, -30])
        cbar.set_ticklabels(['-80', '-70', '-60', '-50', '-40', '-30'])

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

    def _add_statistics_and_buttons(self, window, dbm_values, ssid, total_points, fig, load_example_callback):
        # Estatísticas
        stats_frame = ttk.Frame(window, style='TFrame')
        stats_frame.pack(fill='x', padx=10, pady=5)

        min_dbm = min(dbm_values)
        max_dbm = max(dbm_values)
        avg_dbm = sum(dbm_values) / len(dbm_values)

        stats_text = f"Rede: {ssid} | Mín: {min_dbm:.1f} dBm | Máx: {max_dbm:.1f} dBm | Média: {avg_dbm:.1f} dBm | Pontos: {len(dbm_values)} | Total: {total_points}"
        ttk.Label(stats_frame, text=stats_text, font=('Arial', 10)).pack()

        # Botões
        button_frame = ttk.Frame(stats_frame, style='TFrame')
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