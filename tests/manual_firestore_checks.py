import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))
sys.path.append(str(ROOT / "app"))

from app.services.firestore_service import FirestoreService

# ========= CONFIGURACIÓN =========

ERA_ID = "era_001"
PERIOD_ID = "p01"
INCURSION_IDS = [
    "i01",
    "i02",
    "i03",
    "i04",
]

ADVERSARIES = [
    "england",
    "sweden",
    "brandenburg_prussia",
    "scenario",
]

# ========= UTILIDADES =========


def check(desc, fn, should_fail=False):
    try:
        fn()
        if should_fail:
            print(f"❌ ERROR (debía fallar): {desc}")
        else:
            print(f"✅ OK: {desc}")
    except ValueError as e:
        if should_fail:
            print(f"✅ OK (falló como se esperaba): {desc}")
            print(f"   ↳ {e}")
        else:
            print(f"❌ ERROR inesperado: {desc}")
            print(f"   ↳ {e}")


# ========= TESTS =========

fs = FirestoreService()

print("\n--- REVELAR PERIODO ---")
check(
    "Revelar periodo",
    lambda: fs.reveal_period(ERA_ID, PERIOD_ID),
)

print("\n--- ASIGNAR ADVERSARIOS ---")
for inc_id, adv in zip(INCURSION_IDS, ADVERSARIES):
    check(
        f"Asignar adversario {adv} a {inc_id}",
        lambda inc_id=inc_id, adv=adv: fs.set_incursion_adversary(
            ERA_ID, PERIOD_ID, inc_id, adv
        ),
    )

print("\n--- FIJAR NIVEL ADVERSARIO ---")
check(
    "Fijar nivel para la primera incursión",
    lambda: fs.update_incursion_adversary_level(
        ERA_ID,
        PERIOD_ID,
        INCURSION_IDS[0],
        adversary_id=ADVERSARIES[0],
        adversary_level="Base",
        difficulty=3,
    ),
)

print("\n--- INICIAR INCURSION SIN ERROR ---")
check(
    "Iniciar primera incursión",
    lambda: fs.start_incursion(
        ERA_ID,
        PERIOD_ID,
        INCURSION_IDS[0],
    ),
)

print("\n--- INTENTOS ILEGALES ---")
check(
    "Iniciar segunda incursión con una activa",
    lambda: fs.start_incursion(
        ERA_ID,
        PERIOD_ID,
        INCURSION_IDS[1],
    ),
    should_fail=True,
)

check(
    "Modificar adversario con periodo iniciado",
    lambda: fs.set_incursion_adversary(
        ERA_ID,
        PERIOD_ID,
        INCURSION_IDS[1],
        "england",
    ),
    should_fail=True,
)

print("\n--- FINALIZAR INCURSION ---")
check(
    "Finalizar incursión",
    lambda: fs.finalize_incursion(
        ERA_ID,
        PERIOD_ID,
        INCURSION_IDS[0],
        result="win",
        player_count=2,
        invader_cards_remaining=2,
        invader_cards_out_of_deck=0,
        dahan_alive=6,
        blight_on_island=1,
    ),
)

print("\n--- REANUDAR INCURSION FINALIZADA ---")
check(
    "Reanudar incursión finalizada",
    lambda: fs.resume_incursion(
        ERA_ID,
        PERIOD_ID,
        INCURSION_IDS[0],
    ),
    should_fail=True,
)

print("\n--- FIN DE PRUEBAS ---")
