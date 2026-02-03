# ADR 0008 - Placeholder responsive del layout en incursión

Status: Accepted

## Contexto

- El placeholder fijo de 240×140 puede desbordar en ventanas estrechas.
- El resize no se refleja hasta forzar un refresh de la pantalla.
- Se necesita mantener el contrato visual general del detalle de incursión sin reordenar secciones.

## Decision

- El placeholder del layout pasa a ser responsive dentro de `setup_section`.
- El ancho se calcula según el ancho disponible (teniendo en cuenta paddings) y se limita a un máximo razonable.
- La altura se deriva del ancho manteniendo la proporción 240×140 (`height = width * 140/240`).
- El contenedor del marco aplica `clip_behavior` para recortar el contenido con `border_radius`.
- La imagen/preview del layout usa `fit=CONTAIN` y no define tamaños fijos.
- En `on_resize` se recalculan tamaños y se actualizan solo los controles necesarios.

Esta decisión supersede únicamente la regla de tamaño fijo del placeholder en ADR 0004. El resto del contrato de UI permanece vigente.

## Consecuencias

- El layout preview no genera overflow horizontal y se adapta al tamaño de ventana.
- Las esquinas redondeadas recortan el contenido incluso al redimensionar.
- Se mantiene el orden y estilo general del detalle de incursión.

## Referencias

- ADR 0004.
- `REPO_MAP.md`.
