#!/usr/bin/env python3
"""
Script de teste para visualizar o colormap com gradientes suaves
"""
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np

def test_gradient_colormap():
    """Testa o colormap com gradientes suaves"""
    # Valores dBm e suas cores correspondentes
    colors = ['#FF0000', '#FF4500', '#FFA500', '#ADFF2F', '#90EE90', '#00FFFF']

    # Criar colormap com gradientes suaves (256 pontos)
    cmap = mcolors.LinearSegmentedColormap.from_list("custom_dbm_gradient", colors, N=256)

    # Configurar boundaries
    boundaries = [-85, -75, -65, -55, -45, -35, -25]
    norm = mcolors.BoundaryNorm(boundaries, cmap.N)

    print("🎨 Testando colormap com gradientes suaves:")
    print("=" * 50)

    # Criar dados de teste simulando um heatmap
    np.random.seed(42)
    x = np.random.uniform(-10, 10, 20)
    y = np.random.uniform(-10, 10, 20)
    dbm_values = np.random.choice([-80, -70, -60, -50, -40, -30], 20)

    # Criar grid para interpolação
    xi = np.linspace(-15, 15, 100)
    yi = np.linspace(-15, 15, 100)
    Xi, Yi = np.meshgrid(xi, yi)

    # Interpolação simples
    Zi = np.zeros_like(Xi)
    for i in range(len(xi)):
        for j in range(len(yi)):
            distances = np.sqrt((x - xi[i])**2 + (y - yi[j])**2)
            if len(distances) > 0:
                weights = 1 / (distances + 1.0)
                Zi[j, i] = np.sum(weights * dbm_values) / np.sum(weights)

    # Criar figura
    fig, ax = plt.subplots(figsize=(12, 8))

    # Plot do heatmap com gradientes
    contour = ax.contourf(Xi, Yi, Zi, levels=50, cmap=cmap, norm=norm, alpha=0.8)

    # Pontos medidos (sem bordas pretas)
    scatter = ax.scatter(x, y, c=dbm_values, cmap=cmap, norm=norm,
                        s=120, edgecolors='white', linewidth=1, zorder=10)

    # Configurações limpas
    ax.set_xlabel('Posição X (pixels)', fontsize=12)
    ax.set_ylabel('Posição Y (pixels)', fontsize=12)
    ax.set_title('Mapa de Calor Wi-Fi - Gradientes Suaves', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.set_aspect('equal')

    # Barra de cores limpa
    cbar = plt.colorbar(contour, ax=ax, shrink=0.8)
    cbar.set_label('RSSI (dBm)', fontsize=12)
    cbar.set_ticks([-80, -70, -60, -50, -40, -30])
    cbar.set_ticklabels(['-80', '-70', '-60', '-50', '-40', '-30'])

    plt.tight_layout()
    plt.savefig('gradient_heatmap_test.png', dpi=150, bbox_inches='tight')
    plt.close()

    print("✅ Colormap com gradientes criado com sucesso!")
    print("✅ Contornos removidos!")
    print("✅ Título simplificado!")
    print("📊 Gráfico salvo como 'gradient_heatmap_test.png'")

if __name__ == "__main__":
    test_gradient_colormap()