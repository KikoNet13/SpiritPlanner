# ADR 0007: Puntuacion del reglamento

## Contexto

El proyecto debe alinear la puntuacion con el reglamento oficial de Spirit Island.
El reglamento es la fuente canonica externa para la formula de puntuacion.

## Decision

Variables (campos):

- `result`: "win" | "loss"
- `difficulty`: int
- `player_count`: int (en la app siempre 2; se guarda como 2)
- `dahan_alive`: int
- `blight_on_island`: int
- `invader_cards_remaining`: int (solo relevante en win)
- `invader_cards_out_of_deck`: int (solo relevante en loss)

Formulas:

- Win:
  - `score = 5*difficulty + 10 + 2*invader_cards_remaining + player_count*dahan_alive - player_count*blight_on_island`
- Loss:
  - `score = 2*difficulty + 1*invader_cards_out_of_deck + player_count*dahan_alive - player_count*blight_on_island`

Notas:

- La app se juega solo a 2 jugadores => `player_count=2` sin input en UI.
- Mapas tematicos (+3) no se usan en la app (fuera de alcance).
- No se migran scores historicos ya finalizados (score inmutable); el cambio aplica a nuevas finalizaciones.
