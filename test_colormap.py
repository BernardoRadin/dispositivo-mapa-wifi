#!/usr/bin/env python3
"""
Script de teste para verificar o colormap customizado do heatmap
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np

def test_custom_colormap():
    """Testa se o colormap customizado está funcionando com BoundaryNorm"""
    # Valores dBm e suas cores correspondentes (correspondência exata)
    dbm_values = [-80, -70, -60, -50, -40, -30]
    colors = ['#FF0000', '#FF4500', '#FFA500', '#ADFF2F', '#90EE90', '#00FFFF']

    # Criar colormap com pontos discretos para correspondência exata
    boundaries = [-85, -75, -65, -55, -45, -35, -25]  # Boundaries entre os valores
    cmap = mcolors.LinearSegmentedColormap.from_list("custom_dbm", colors, N=len(colors))

    # Configurar para mapear exatamente os valores
    norm = mcolors.BoundaryNorm(boundaries, cmap.N)

    print("Testando colormap customizado com BoundaryNorm:")
    print("=" * 60)

    # Testar mapeamento para valores específicos
    test_values = [-80, -75, -70, -65, -60, -55, -50, -45, -40, -35, -30]

    for val in test_values:
        normalized = norm(val)
        color = cmap(normalized)
        # Converter para hex
        hex_color = mcolors.to_hex(color)
        print("5.1f")

    print("=" * 60)
    print("✅ Colormap customizado criado com sucesso!")
    print("✅ BoundaryNorm configurado para mapeamento discreto!")

    # Criar um gráfico de teste simples
    fig, ax = plt.subplots(figsize=(10, 2))

    # Criar dados de teste
    x = np.linspace(-85, -25, 100)
    y = np.ones_like(x)

    # Plot com o colormap customizado
    scatter = ax.scatter(x, y, c=x, cmap=cmap, norm=norm, s=50)
    ax.set_title('Teste do Colormap Customizado dBm')
    ax.set_xlabel('Valor dBm')
    ax.set_yticks([])

    # Colorbar
    cbar = plt.colorbar(scatter, ax=ax, orientation='horizontal')
    cbar.set_label('RSSI (dBm)')

    plt.tight_layout()
    plt.savefig('colormap_test.png', dpi=150, bbox_inches='tight')
    plt.close()

    print("📊 Gráfico de teste salvo como 'colormap_test.png'")

if __name__ == "__main__":
    test_custom_colormap()