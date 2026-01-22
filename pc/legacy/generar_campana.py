import sys
import csv
import random

from data_loader import leer_espiritus, leer_tableros

sys.stdout.reconfigure(encoding="utf-8")

ESPIRITUS_FILE = "data/espiritus.tsv"
TABLEROS_FILE = "data/tableros.tsv"
OUTPUT_FILE = "campana.tsv"


def generar_jornadas_round_robin(espiritus):
    """
    Genera jornadas deterministas con el método del círculo (round-robin clásico).
    Cada jornada cubre todos los espíritus una vez y, en total, todas las parejas aparecen exactamente una vez.
    """
    total = len(espiritus)
    if total < 2:
        raise ValueError("Debe haber al menos 2 espíritus para generar jornadas")
    if total % 2 != 0:
        raise ValueError("El número de espíritus debe ser par para formar parejas completas por jornada")

    orden = list(espiritus)
    jornadas = []

    for _ in range(total - 1):
        parejas = []
        for i in range(total // 2):
            e1 = orden[i]
            e2 = orden[total - 1 - i]
            parejas.append((e1, e2))
        jornadas.append(parejas)

        fijo = orden[0]
        resto = orden[1:]
        resto = [resto[-1]] + resto[:-1]
        orden = [fijo] + resto

    return jornadas


def asignar_tableros_a_jornada(tableros, num_partidas):
    """
    Asigna tableros de forma estructurada y balanceada dentro de una jornada.
    - Cada partida recibe dos tableros distintos.
    - Cada tablero aparece el mismo número de veces o lo más equilibrado posible dentro de la jornada.
    """
    if len(tableros) < 2:
        raise ValueError("Debe haber al menos 2 tableros para asignar por partida")

    slots = num_partidas * 2  # dos tableros por partida
    base = slots // len(tableros)
    resto = slots % len(tableros)

    secuencia = []
    for idx, tablero in enumerate(tableros):
        repeticiones = base + (1 if idx < resto else 0)
        secuencia.extend([tablero] * repeticiones)

    primera_mitad = secuencia[:num_partidas]
    segunda_mitad = secuencia[num_partidas:]

    if len(segunda_mitad) != num_partidas:
        raise ValueError("No hay suficientes tableros para completar todas las partidas de la jornada")

    # En la construcción anterior no deberían coincidir, pero protegemos por si la distribución futura cambia.
    for i in range(num_partidas):
        if primera_mitad[i] == segunda_mitad[i]:
            swap_idx = (i + 1) % len(segunda_mitad)
            segunda_mitad[i], segunda_mitad[swap_idx] = segunda_mitad[swap_idx], segunda_mitad[i]

    parejas_tableros = []
    for i in range(num_partidas):
        parejas_tableros.append((primera_mitad[i], segunda_mitad[i]))

    return parejas_tableros


def generar_tableros_para_jornadas(jornadas, tableros):
    """Genera la estructura de tableros para cada jornada de forma determinista."""
    asignaciones = []
    for parejas in jornadas:
        asignaciones.append(asignar_tableros_a_jornada(tableros, len(parejas)))
    return asignaciones


def randomizar_superficial(jornadas, tableros_por_jornada):
    """
    Aplica randomización superficial sin alterar la estructura:
    - Baraja espíritus dentro de cada pareja.
    - Baraja el orden de parejas dentro de cada jornada.
    - Baraja el orden de las jornadas.
    - Baraja tableros dentro de cada partida y qué pareja recibe cada combinación.
    """
    rng = random.Random()
    jornadas_mezcladas = []

    for parejas, tableros in zip(jornadas, tableros_por_jornada):
        parejas_mezcladas = []
        for e1, e2 in parejas:
            duo = [e1, e2]
            rng.shuffle(duo)
            parejas_mezcladas.append(tuple(duo))

        tableros_mezclados = []
        for t1, t2 in tableros:
            duo_tableros = [t1, t2]
            rng.shuffle(duo_tableros)
            tableros_mezclados.append(tuple(duo_tableros))

        rng.shuffle(parejas_mezcladas)
        rng.shuffle(tableros_mezclados)

        jornada_completa = []
        for pareja, combo_tableros in zip(parejas_mezcladas, tableros_mezclados):
            jornada_completa.append((pareja, combo_tableros))

        jornadas_mezcladas.append(jornada_completa)

    rng.shuffle(jornadas_mezcladas)
    return jornadas_mezcladas


def exportar_tsv(jornadas, path):
    encabezados = [
        "Jornada",
        "Partida",
        "Espíritu 1",
        "Dificultad 1",
        "Tablero 1",
        "Espíritu 2",
        "Dificultad 2",
        "Tablero 2",
    ]

    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(encabezados)

        for jornada_idx, partidas in enumerate(jornadas, start=1):
            for partida_idx, (espiritus, tableros) in enumerate(partidas, start=1):
                e1, e2 = espiritus
                t1, t2 = tableros
                writer.writerow(
                    [
                        jornada_idx,
                        partida_idx,
                        e1["name"],
                        e1["difficulty"],
                        t1,
                        e2["name"],
                        e2["difficulty"],
                        t2,
                    ]
                )


def main():
    espiritus = leer_espiritus(ESPIRITUS_FILE)
    tableros = leer_tableros(TABLEROS_FILE)

    jornadas = generar_jornadas_round_robin(espiritus)
    tableros_por_jornada = generar_tableros_para_jornadas(jornadas, tableros)

    jornadas_finales = randomizar_superficial(jornadas, tableros_por_jornada)

    exportar_tsv(jornadas_finales, OUTPUT_FILE)

    print(f"Campaña generada en {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
