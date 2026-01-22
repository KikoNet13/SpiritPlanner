import sys

sys.stdout.reconfigure(encoding="utf-8")

import random
import argparse
from data_loader import leer_espiritus

ESPIRITUS_FILE = "data/espiritus.tsv"


def generar_jornadas(espiritus):
    """
    Genera jornadas de un round-robin clásico (método del círculo) sin usar itertools.
    Mantiene el primer espíritu fijo y rota el resto en cada jornada para cubrir todas las parejas.
    """
    total = len(espiritus)
    if total < 2:
        raise ValueError("Debe haber al menos 2 espíritus para generar jornadas")
    if total % 2 != 0:
        raise ValueError("El número de espíritus debe ser par para formar parejas completas por jornada")

    # Trabajamos sobre una copia para no modificar la lista original
    orden = list(espiritus)
    jornadas = []

    # En un round-robin de N participantes se generan N-1 jornadas
    for _ in range(total - 1):
        parejas = []
        # Emparejar extremos: i con -(i+1)
        for i in range(total // 2):
            e1 = orden[i]
            e2 = orden[total - 1 - i]
            parejas.append((e1, e2))
        jornadas.append(parejas)

        # Rotación del método del círculo (el primer elemento permanece fijo)
        fijo = orden[0]
        resto = orden[1:]
        resto = [resto[-1]] + resto[:-1]
        orden = [fijo] + resto

    return jornadas


def randomizar_jornadas(jornadas, seed=None):
    """
    Aplica randomización superficial sin romper la estructura round-robin:
    - Puede fijarse seed para reproducibilidad.
    - Baraja el orden de espíritus dentro de cada pareja.
    - Baraja el orden de las parejas dentro de cada jornada.
    - Baraja el orden de las jornadas.
    Trabaja sobre copias para no mutar la entrada.
    """
    rng = random.Random(seed)
    jornadas_copia = []

    for parejas in jornadas:
        parejas_copia = []
        for e1, e2 in parejas:
            pareja = [e1, e2]
            rng.shuffle(pareja)
            parejas_copia.append(tuple(pareja))
        rng.shuffle(parejas_copia)
        jornadas_copia.append(parejas_copia)

    rng.shuffle(jornadas_copia)
    return jornadas_copia


def main():
    parser = argparse.ArgumentParser(
        description="Genera jornadas round-robin de espíritus y permite randomización reproducible."
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Semilla opcional para randomización reproducible. Déjalo vacío para orden aleatorio distinto cada vez.",
    )
    args = parser.parse_args()

    espiritus = leer_espiritus(ESPIRITUS_FILE)
    jornadas = generar_jornadas(espiritus)
    jornadas = randomizar_jornadas(jornadas, seed=args.seed)

    print("Jornadas de espíritus (round-robin):\n")
    for idx, parejas in enumerate(jornadas, start=1):
        print(f"Jornada {idx}:")
        for e1, e2 in parejas:
            print(
                f"- {e1['name']} ({e1['difficulty']})  +  "
                f"{e2['name']} ({e2['difficulty']})"
            )
        print()

    print(f"Total jornadas: {len(jornadas)}")


if __name__ == "__main__":
    main()
