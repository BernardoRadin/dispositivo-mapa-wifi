import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.colors as mcolors
import numpy as np

class HeatmapGenerator:
    def __init__(self, parent_window):
        self.parent = parent_window
        
        self.dbm_colors = [
            (-80, '#FF0000'),
            (-70, '#FF4500'),
            (-60, '#FFA500'),
            (-50, '#ADFF2F'),
            (-40, '#90EE90'),
            (-30, '#00FFFF')
        ]
        
        self.custom_cmap = self._create_custom_colormap()
        
        self.point_positions = {}
        grid_size = 4
        spacing = 1.0
        
        for row in range(grid_size):
            for col in range(grid_size):
                point_num = row * grid_size + col + 1
                point_name = f"Ponto {point_num}"
                x_pos = (col - (grid_size-1)/2) * spacing
                y_pos = ((grid_size-1)/2 - row) * spacing
                self.point_positions[point_name] = (x_pos, y_pos)
        
        self._current_fig = None

    def _create_custom_colormap(self):
        dbm_values = [-80, -70, -60, -50, -40, -30]
        colors = ['#FF0000', '#FF4500', '#FFA500', '#ADFF2F', '#90EE90', '#00FFFF']
        extended_colors = []
        extended_positions = []
        for i, color in enumerate(colors):
            extended_colors.append(color)
            extended_positions.append(i / (len(colors) - 1))
        cmap = mcolors.LinearSegmentedColormap.from_list("custom_dbm_gradient", extended_colors, N=256)
        boundaries = [-85, -75, -65, -55, -45, -35, -25]
        norm = mcolors.BoundaryNorm(boundaries, cmap.N)
        self.dbm_norm = norm
        return cmap

    def generate_heatmap(self, measurements, ssid, image_path=None, load_example_callback=None):
        if not ssid:
            messagebox.showerror("Erro", "Selecione uma rede Wi-Fi")
            return
            
        valid_measurements = {k: v for k, v in measurements.items() if v.get('dbm', 'N/A') != 'N/A'}
        
        if len(valid_measurements) < 3:
            messagebox.showwarning("Aviso", "É necessário pelo menos 3 pontos medidos para gerar o mapa")
            return

        heatmap_window = tk.Toplevel(self.parent)
        heatmap_window.title(f"Mapa de Calor Wi-Fi - {ssid}")
        heatmap_window.geometry("1000x800")

        x_coords, y_coords, dbm_values, point_labels = self._process_image_data(measurements)

        if len(x_coords) < 3:
            messagebox.showwarning("Aviso", "Dados insuficientes para gerar o mapa")
            return

        fig, ax = self._create_plot_with_image(x_coords, y_coords, dbm_values, point_labels, ssid, image_path)
        self._current_fig = fig
        
        canvas = FigureCanvasTkAgg(fig, heatmap_window)
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        self._add_statistics_and_buttons(heatmap_window, dbm_values, ssid, len(valid_measurements), fig, load_example_callback, measurements)

    def _process_data(self, measurements, complete_locations):
        x_coords = []
        y_coords = []
        dbm_values = []
        location_labels = []
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
        x_coords = []
        y_coords = []
        dbm_values = []
        point_labels = []

        all_coords = []
        for point_name, measurement in measurements.items():
            if measurement.get('dbm', 'N/A') != 'N/A':
                coords = measurement.get('coordinates', (0, 0))
                all_coords.append(coords)

        if all_coords:
            max_y = max(coord[1] for coord in all_coords)


            for point_name, measurement in measurements.items():
                if measurement.get('dbm', 'N/A') != 'N/A':
                    coords = measurement.get('coordinates', (0, 0))
                    x_coords.append(coords[0])
                    y_coords.append(max_y - coords[1])
                    dbm_values.append(float(measurement['dbm']))
                    point_labels.append(point_name)

        return x_coords, y_coords, dbm_values, point_labels

    def _create_plot_with_image(self, x_coords, y_coords, dbm_values, point_labels, ssid, image_path):
        fig, ax = plt.subplots(figsize=(14, 10))
        if image_path:
            try:
                from PIL import Image
                import matplotlib.image as mpimg
                img = Image.open(image_path)
                img_width, img_height = img.size
                x_min, x_max = min(x_coords), max(x_coords)
                y_min, y_max = min(y_coords), max(y_coords)
                margin_x = (x_max - x_min) * 0.1
                margin_y = (y_max - y_min) * 0.1
                ax.imshow(img, extent=[x_min-margin_x, x_max+margin_x, y_min-margin_y, y_max+margin_y], 
                         aspect='auto', alpha=0.3, origin='upper')
            except Exception as e:
                print(f"Aviso: Não foi possível carregar imagem de fundo: {e}")

        x_min, x_max = min(x_coords) - 10, max(x_coords) + 10
        y_min, y_max = min(y_coords) - 10, max(y_coords) + 10

        xi = np.linspace(x_min, x_max, 100)
        yi = np.linspace(y_min, y_max, 100)
        Xi, Yi = np.meshgrid(xi, yi)

        Zi = self._interpolate_data(xi, yi, Xi, Yi, x_coords, y_coords, dbm_values)

        contour = ax.contourf(Xi, Yi, Zi, levels=50, cmap=self.custom_cmap, norm=self.dbm_norm, alpha=0.8)

        scatter = ax.scatter(x_coords, y_coords, c=dbm_values, cmap=self.custom_cmap, norm=self.dbm_norm,
                           s=120, edgecolors='white', linewidth=1, zorder=10)

        self._add_labels(ax, x_coords, y_coords, dbm_values, point_labels)

        ax.set_xlabel('', fontsize=12)
        ax.set_ylabel('', fontsize=12)
        ax.set_title(f'Mapa de Calor Wi-Fi - {ssid}', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.set_aspect('equal')
        ax.set_xticks([])
        ax.set_yticks([])

        import matplotlib as mpl
        sm = mpl.cm.ScalarMappable(cmap=self.custom_cmap, norm=self.dbm_norm)
        sm.set_array([])
        cbar = plt.colorbar(sm, ax=ax, shrink=0.8, orientation='vertical')
        cbar.set_label('RSSI (dBm)', fontsize=12)
        all_dbm_values = [-30, -40, -50, -60, -70, -80]
        cbar.set_ticks(all_dbm_values)
        cbar.set_ticklabels([f'{val}' for val in all_dbm_values])
        cbar.mappable.set_clim(-85, -25)

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
            parts = label.split('\n')
            local_name = parts[0]
            point_name = parts[1] if len(parts) > 1 else ""
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

    def _add_statistics_and_buttons(self, window, dbm_values, ssid, total_points, fig, load_example_callback, measurements=None):
        stats_frame = ttk.Frame(window, style='TFrame')
        stats_frame.pack(fill='x', padx=10, pady=5)

        min_dbm = min(dbm_values)
        max_dbm = max(dbm_values)
        avg_dbm = sum(dbm_values) / len(dbm_values)

        stats_text = f"Rede: {ssid} | Mín: {min_dbm:.1f} dBm | Máx: {max_dbm:.1f} dBm | Média: {avg_dbm:.1f} dBm | Pontos: {len(dbm_values)} | Total: {total_points}"
        ttk.Label(stats_frame, text=stats_text, font=('Arial', 10)).pack()

        button_frame = ttk.Frame(stats_frame, style='TFrame')
        button_frame.pack(pady=5)

        def save_heatmap():
            filename = filedialog.asksaveasfilename(
                defaultextension=".png",
                filetypes=[
                    ("PNG files", "*.png"),
                    ("PDF files", "*.pdf"),
                    ("SVG files", "*.svg"),
                    ("JPEG files", "*.jpg")
                ]
            )
            if filename:
                try:
                    if filename.lower().endswith('.pdf'):
                        fig.savefig(filename, format='pdf', dpi=300, bbox_inches='tight')
                    elif filename.lower().endswith('.svg'):
                        fig.savefig(filename, format='svg', bbox_inches='tight')
                    elif filename.lower().endswith(('.jpg', '.jpeg')):
                        fig.savefig(filename, format='jpg', dpi=300, bbox_inches='tight', quality=95)
                    else:
                        fig.savefig(filename, format='png', dpi=300, bbox_inches='tight')
                    messagebox.showinfo("Sucesso", f"Mapa salvo: {filename}")
                except Exception as e:
                    messagebox.showerror("Erro", f"Erro ao salvar mapa: {str(e)}")

        def save_measurements_json():
            if measurements is None:
                messagebox.showerror("Erro", "Dados de medição não disponíveis")
                return
            filename = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json")]
            )
            if filename:
                try:
                    import json
                    from datetime import datetime
                    json_data = {
                        "metadata": {
                            "ssid": ssid,
                            "timestamp": datetime.now().isoformat(),
                            "total_points": len(measurements),
                            "statistics": {
                                "min_dbm": min(dbm_values) if dbm_values else 0,
                                "max_dbm": max(dbm_values) if dbm_values else 0,
                                "avg_dbm": sum(dbm_values) / len(dbm_values) if dbm_values else 0,
                                "points_count": len(dbm_values)
                            }
                        },
                        "measurements": {}
                    }
                    for point_name, measurement in measurements.items():
                        if measurement.get('dbm', 'N/A') != 'N/A':
                            json_data["measurements"][point_name] = {
                                "dbm": float(measurement['dbm']),
                                "coordinates": measurement.get('coordinates', (0, 0)),
                                "timestamp": measurement.get('timestamp', datetime.now().isoformat())
                            }
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(json_data, f, indent=2, ensure_ascii=False)
                    messagebox.showinfo("Sucesso", f"Dados salvos: {filename}")
                except Exception as e:
                    messagebox.showerror("Erro", f"Erro ao salvar arquivo: {str(e)}")

        def save_measurements_csv():
            if measurements is None:
                messagebox.showerror("Erro", "Dados de medição não disponíveis")
                return
            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv")]
            )
            if filename:
                try:
                    import csv
                    from datetime import datetime
                    with open(filename, 'w', newline='', encoding='utf-8') as f:
                        writer = csv.writer(f)
                        writer.writerow(['Ponto', 'dBm', 'Coordenada_X', 'Coordenada_Y', 'Timestamp'])
                        for point_name, measurement in measurements.items():
                            if measurement.get('dbm', 'N/A') != 'N/A':
                                coords = measurement.get('coordinates', (0, 0))
                                timestamp = measurement.get('timestamp', datetime.now().isoformat())
                                writer.writerow([
                                    point_name,
                                    measurement['dbm'],
                                    coords[0],
                                    coords[1],
                                    timestamp
                                ])
                    messagebox.showinfo("Sucesso", f"Dados CSV salvos: {filename}")
                except Exception as e:
                    messagebox.showerror("Erro", f"Erro ao salvar arquivo CSV: {str(e)}")

        ttk.Button(button_frame, text="Salvar Mapa", command=save_heatmap).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Salvar Dados (JSON)", command=save_measurements_json).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Salvar Dados (CSV)", command=save_measurements_csv).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Carregar Dados Exemplo", command=load_example_callback).pack(side='left', padx=5)

    def save_heatmap_image(self, file_path):
        try:
            if not hasattr(self, '_current_fig') or self._current_fig is None:
                raise ValueError("Nenhum mapa de calor foi gerado ainda")
            self._current_fig.savefig(file_path, format='png', dpi=300, bbox_inches='tight')
        except Exception as e:
            raise Exception(f"Erro ao salvar imagem do mapa: {str(e)}")
