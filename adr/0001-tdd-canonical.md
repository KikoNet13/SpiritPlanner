# ADR 0001 - TDD canonico y README landing

Status: Accepted

## Contexto

Hay varias fuentes de documentacion y reglas en el repo, con riesgo de desalineacion.
Se necesita una fuente de verdad unica y estable.

## Decision

- `TDD.md` es la fuente canonica del modelo, reglas y flujos.
- `adr/` contiene decisiones tecnicas.
- `README.md`, `STATUS.md` y `DOCUMENTATION.md` son no canonicos y solo de apoyo.

## Consecuencias

- Los cambios de reglas o modelo deben actualizar `TDD.md` y/o ADRs.
- Los PRs deben enlazar a TDD/ADR cuando apliquen.
- README queda como landing breve, sin duplicar reglas.

## Referencias

- `TDD.md`
- `README.md`
- `STATUS.md`
- `DOCUMENTATION.md`
