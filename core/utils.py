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
    if pct <= 33:
        return "red"
    elif pct <= 66:
        return "orange"
    else:
        return "green"

def dbm_to_color(dbm):
    if dbm == "N/A" or dbm is None:
        return "gray"

    try:
        dbm_val = float(dbm)

        # Tabela baseada no README
        if dbm_val >= -30:
            return "#00FFFF"  # Ciano - Excelente
        elif dbm_val >= -40:
            return "#90EE90"  # Verde claro - Muito Bom
        elif dbm_val >= -50:
            return "#ADFF2F"  # Amarelo esverdeado - Bom
        elif dbm_val >= -60:
            return "#FFA500"  # Laranja - Regular
        elif dbm_val >= -70:
            return "#FF4500"  # Laranja avermelhado - Ruim
        else:
            return "#FF0000"  # Vermelho - Muito Ruim
    except:
        return "gray"

def dbm_to_status(dbm):
    if dbm == "N/A" or dbm is None:
        return "Sem sinal"

    try:
        dbm_val = float(dbm)

        if dbm_val >= -30:
            return "Excelente"
        elif dbm_val >= -40:
            return "Muito Bom"
        elif dbm_val >= -50:
            return "Bom"
        elif dbm_val >= -60:
            return "Regular"
        elif dbm_val >= -70:
            return "Ruim"
        else:
            return "Muito Ruim"
    except:
        return "Sem sinal"

def interpolate_color(color1, color2, factor):
    def hex_to_rgb(hex_color):
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    def rgb_to_hex(rgb):
        return '#{:02x}{:02x}{:02x}'.format(*rgb)

    rgb1 = hex_to_rgb(color1)
    rgb2 = hex_to_rgb(color2)

    interpolated_rgb = tuple(
        int(rgb1[i] + (rgb2[i] - rgb1[i]) * factor)
        for i in range(3)
    )

    return rgb_to_hex(interpolated_rgb)