def leer_espiritus(path):
    espiritus = []

    with open(path, "r", encoding="utf-8-sig") as f:
        for line_num, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue

            parts = line.split("\t")
            if len(parts) != 2:
                raise ValueError(
                    f"Línea {line_num}: se esperaban 2 columnas (espíritu, dificultad)"
                )

            nombre = parts[0].strip()
            dificultad = parts[1].strip()

            if not nombre or not dificultad:
                raise ValueError(f"Línea {line_num}: nombre o dificultad vacío")

            espiritus.append({"name": nombre, "difficulty": dificultad})

    return espiritus


def leer_tableros(path):
    tableros = []

    with open(path, "r", encoding="utf-8-sig") as f:
        for line_num, line in enumerate(f, start=1):
            value = line.strip()
            if not value:
                continue
            tableros.append(value)

    if len(tableros) < 2:
        raise ValueError("Debe haber al menos 2 tableros")

    return tableros
