pywifi>=1.1.12
matplotlib>=3.5.0
numpy>=1.21.0
tkinter

*Separação em pastas*
    projeto/
    ├── main.py                # Arquivo principal de execução
    ├── core/
    │   ├── __init__.py        # Inicialização do pacote core
    │   ├── wifi_scanner.py    # Classe WifiScanner
    │   └── utils.py           # Funções utilitárias
    ├── gui/
    │   ├── __init__.py        # Inicialização do pacote gui
    │   ├── wifi_app.py        # Interface principal (WifiMapApp)
    │   └── heatmap.py         # Gerador de mapas de calor
    └── requirements.txt       # Dependências do projeto