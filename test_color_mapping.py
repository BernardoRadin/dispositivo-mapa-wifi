#!/usr/bin/env python3
"""
Script de teste para verificar o mapeamento exato de cores dBm
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.utils import dbm_to_color

def test_dbm_color_mapping():
    """Testa o mapeamento exato de cores para valores dBm"""
    test_cases = [
        (-80, '#FF0000'),  # Vermelho
        (-70, '#FF4500'),  # Laranja avermelhado
        (-60, '#FFA500'),  # Laranja
        (-50, '#ADFF2F'),  # Amarelo esverdeado
        (-40, '#90EE90'),  # Verde claro
        (-30, '#00FFFF'),  # Verde azulado/Ciano
    ]

    print("Testando mapeamento exato de cores dBm:")
    print("=" * 50)

    all_passed = True
    for dbm_value, expected_color in test_cases:
        actual_color = dbm_to_color(dbm_value)
        status = "✓ PASS" if actual_color == expected_color else "✗ FAIL"
        print("2d")
        if actual_color != expected_color:
            all_passed = False

    print("=" * 50)
    if all_passed:
        print("🎉 Todos os testes passaram! Mapeamento exato funcionando.")
    else:
        print("❌ Alguns testes falharam. Verificar implementação.")

    return all_passed

if __name__ == "__main__":
    test_dbm_color_mapping()