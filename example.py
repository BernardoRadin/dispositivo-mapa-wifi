#!/usr/bin/env python3
"""
Exemplo de uso do WiFi Scanner com Planta Baixa

Este script demonstra como usar o sistema de mapeamento WiFi
com imagens de plantas baixas de forma programática.
"""

import tkinter as tk
from gui.wifi_app import WifiMapApp

def main():
    """Função principal do exemplo"""
    print("🚀 Iniciando WiFi Scanner com Planta Baixa")
    print("📋 Instruções:")
    print("   1. Selecione uma rede WiFi")
    print("   2. Carregue uma imagem de planta baixa")
    print("   3. Clique na imagem para posicionar pontos")
    print("   4. Gere o mapa de calor")

    # Criar janela principal
    root = tk.Tk()
    root.title("WiFi Scanner - Exemplo com Planta Baixa")

    # Criar aplicação
    app = WifiMapApp(root)

    # Iniciar loop da interface
    root.mainloop()

if __name__ == "__main__":
    main()