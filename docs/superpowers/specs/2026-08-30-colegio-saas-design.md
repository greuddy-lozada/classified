# Classified — Diseño v1 (colegio privado, Venezuela)

Fecha: 2026-08-30  
Estado: aprobado en conversación de diseño

## Problema

El repo es un andamiaje (FastAPI + Mongo + Quasar) sin dominio académico. El producto es un SIS para colegios venezolanos: inscripciones, asistencia, notas y un cobro mínimo, vendido a muchos planteles.

v1 cubre **colegio privado** (inicial + primaria + media). Universidad y centros de cursos no se implementan; el núcleo (organización, período, evaluación enchufable) se deja listo para esos perfiles después.

## Decisiones cerradas

- Un producto, muchos colegios. Cada plantel aislado.
- Una sola base PostgreSQL. Toda fila de negocio lleva `organizacion_id`.
- Stack: Quasar (Vue 3) + FastAPI + PostgreSQL 16. Sale MongoDB.
- Portales: plantel, representante, estudiante. Un SPA; el rol decide la pantalla.
- Cobro: estado de matrícula y mensualidad. Sin pasarela ni facturación fiscal.
- El colegio no se auto-registra. La plataforma da de alta el plantel y el primer admin.

## Fuera de v1

Universidad, cursos, planteles públicos, pasarela de pago, IGTF/divisas, Kubernetes, GraphQL, microservicios, justificación de faltas por el representante, app nativa (Quasar Capacitor puede venir después), esquema o base por colegio.

---

## 1. Tenancy

Una organización = un colegio (nombre, RIF, activo).

Sede y turno no son tenant. Viven dentro del colegio. v1 puede tener un solo campus implícito; sedes se agregan después sin cambiar el aislamiento.

**Usuario de plataforma** (`es_plataforma`): crea organizaciones y el primer admin. No lee fichas, notas ni cobros.

**Membresía:** `usuario + organizacion + rol`. Un usuario puede tener varias membresías (dos colegios, o docente y representante en el mismo). La sesión activa lleva un solo `organizacion_id` y un solo `rol`. Si hay más de una, el usuario elige plantel (y rol si aplica) después del login.

Toda query de negocio filtra por `organizacion_id` del token. Sin ese filtro es un bug de fuga.

Roles:

| Rol | Quién |
|---|---|
| `plataforma` | Staff de Classified |
| `direccion` | Configura el plantel, cierra lapsos |
| `secretaria` | Fichas, cupos, inscripción, recaudos, marca pagos |
| `docente` | Lista y notas de sus secciones/materias |
| `representante` | Pupilos |
| `estudiante` | Su expediente |

JWT: `sub` (usuario), `org_id` (nullable si solo plataforma), `rol`, `es_plataforma`. Access corto + refresh.

## 2. Personas

Tres conceptos distintos:

1. **Usuario** — login global (email único, clave). No es el expediente.
2. **Persona** — ficha **de un colegio**. El colegio A no hereda la ficha del B.
3. **Rol** — qué es esa persona en ese colegio (vía membresía + tablas de vínculo).

La ficha se identifica con `(organizacion_id, tipo_doc, numero_doc)`.

Documentos:

| `tipo_doc` | Uso |
|---|---|
| `cedula_v` | Venezolano |
| `cedula_e` | Extranjero con cédula |
| `pasaporte` | Sin cédula venezolana |
| `partida` | Niño sin cédula (inicial / primaria baja) |
| `expediente` | Último recurso; lo asigna secretaría |

Sin cédula no se bloquea la inscripción: se usa partida y se actualiza cuando salga la cédula.

Papeles sobre la ficha:

- **Alumno** — ficha + datos escolares mínimos. Usuario opcional (inicial/primaria no lo tienen; media sí).
- **Representante** — ficha + usuario. N alumnos, con `parentesco` (madre, padre, abuelo, tutor). Uno es `es_principal` (firma y ve cobros).
- **Trabajador** — ficha + usuario (dirección, secretaría, docente).

Ejemplos:

- Niño de inicial: ficha, sin usuario. Entra el representante.
- Alumno de media: ficha y usuario.
- Mamá con dos hijos: un usuario, dos fichas de alumno ligadas a ella.
- Docente en dos colegios: un usuario, dos fichas, dos membresías.

Reglas:

- El alumno no ve a sus hermanos ni cobros.
- El representante solo ve sus pupilos.
- Secretaría ve todas las fichas del plantel.
- El docente no ve el padrón completo (solo su sección, cuando exista oferta académica).
- Plataforma no lee fichas.

Recaudos (partida, fotos, cédula escaneada) son archivos de la ficha, no la ficha. v1: archivo + estado entregado/faltante. Almacenamiento: disco local o S3-compatible; no en Postgres.

## 3. Año escolar

El colegio trabaja por **año escolar** (ej. 2026-2027), no por semestre.

Cada año tiene **3 lapsos**. Notas y boletín se cierran por lapso.

Jerarquía dentro del año:

- **Nivel** — `inicial` | `primaria` | `media`
- **Grado** — 3er nivel, 4° grado, 3er año, etc.
- **Sección** — el grupo: `4° A`, con **turno** `manana` | `tarde`

El alumno se inscribe a **una sección de un año**. El docente se asigna a secciones (y en media, a materias).

Inicial, primaria y media comparten el mismo año y los mismos lapsos. Cambian materias y esquema de evaluación.

## 4. Inscripción

El alumno queda inscrito cuando tiene sección en un año escolar. Antes es solo ficha.

Flujo:

1. Solicitud de cupo (nuevo) o reinscripción (ya era del plantel).
2. Secretaría asigna sección si hay cupo.
3. Recaudos: entregado / faltante.
4. Matrícula: pendiente / pagada / morosa.

Estados: `preinscrito` → `inscrito` → `activo`. También `retirado`.

Reglas:

- Un alumno, una sección por año.
- Sin representante principal no se cierra la inscripción.
- Recaudos o matrícula pendientes no impiden el estado `inscrito`; secretaría lo ve pendiente. El colegio decide si entra a clases.
- El representante ve el estado. No asigna sección.

## 5. Evaluación

Año y lapsos son iguales en todo el plantel. Cambia lo que se carga:

- **Inicial** — sin 1–20. Por lapso: áreas (lenguaje, socioemocional, etc.) con juicio `logrado` | `en_proceso` | `iniciado` y comentario. El documento es un informe.
- **Media** — materias. Escala 1–20, mínimo 10. Notas por materia y lapso. Promedio de lapso y final. Si cierra bajo 10: reparación.
- **Primaria** — el colegio elige **por grado**: esquema de inicial (grados bajos) o de media (grados altos).

Reglas:

- El docente solo carga en sus materias/secciones.
- Al cerrar el lapso, las notas no se editan. Solo el rol `direccion` puede reabrir (coordinación usa ese rol en v1).
- Representante y estudiante ven el boletín. No lo editan.

## 6. Asistencia

- **Inicial y primaria** — lista por sección y día.
- **Media** — lista por materia, sección y día (la clase de ese profesor).

Estados: `presente` | `ausente` | `justificado` | `tardanza`.

El % se calcula en consecuencia (en media: por materia y lapso). v1 no bloquea notas por asistencia. El representante ve faltas; no las justifica (avisa al colegio; secretaría o docente marca `justificado`). Un alumno `retirado` no sale en la lista.

## 7. Cobro mínimo

Sin facturas ni pasarela. Estado por alumno y año:

- **Matrícula** — un cargo al año: `pendiente` | `pagada` | `morosa`
- **Mensualidad** — un cargo por mes que defina el colegio: mismos estados

Secretaría marca pagado (fecha + nota libre: “transferencia”, “efectivo”). El representante ve qué debe. Moroso no expulsa solo; lo ven secretaría y dirección.

## 8. Portales

Un frontend Quasar. Rutas por rol. Si hay varias membresías, selector de plantel.

**Plantel**

- Dirección: año, grados, secciones, cierre de lapsos.
- Secretaría: fichas, cupos, inscripción, recaudos, pagos.
- Docente: sus secciones — asistencia y notas.

**Representante** — pupilos: boletín, asistencia, recaudos, matrícula/mensualidad.

**Estudiante** — su boletín y su asistencia. No hermanos, no cobros.

**Plataforma** — alta de colegio y primer admin.

## 9. Arquitectura técnica

Monolito modular. Un repo, un FastAPI, un Quasar.

```
Quasar (Vue 3)  →  FastAPI  →  PostgreSQL 16
       │                │
  un SPA, rutas         SQLAlchemy 2 + Alembic
  por rol               JWT + filtro de tenant
```

Módulos de backend (carpetas, no servicios): `identidad`, `plantel`, `personas`, `periodo`, `inscripcion`, `asistencia`, `evaluacion`, `cobro`.

Deploy v1: Docker Compose en un VPS (o servidor local del plantel). Tres servicios: `frontend`, `backend`, `postgres`.

Archivos de recaudos: disco o S3-compatible (MinIO / R2). Jobs (cierre de lapso, PDFs): cron + tabla al inicio; Celery cuando duela. PDF de boletín/constancia: WeasyPrint o equivalente, no en la fase 1.

Auth: no inventar crypto. Hash de clave con passlib/bcrypt (o argon2). JWT con `python-jose` o PyJWT.

## 10. Modelo de datos (núcleo)

Tablas que el resto asume. Todas las de negocio excepto `usuario` llevan `organizacion_id` (usuario es global).

- `organizacion`
- `usuario` (email único, `password_hash`, `es_plataforma`, `activo`)
- `membresia` (`usuario_id`, `organizacion_id`, `rol`, `activo`). Única por `(usuario_id, organizacion_id, rol)`.
- `persona` (ficha; `usuario_id` opcional; documento único por org)
- `alumno` (`persona_id`)
- `vinculo_representante` (`representante_persona_id`, `alumno_id`, `parentesco`, `es_principal`)
- `trabajador` (`persona_id`, `usuario_id`) — staff/docente del plantel
- `anio_escolar`, `lapso`
- `nivel`, `grado`, `seccion` (con turno)
- `inscripcion` (alumno + sección + año + estado)
- `recaudo` (alumno + tipo + estado + archivo)
- `materia`, `asignacion_docente`
- `evaluacion` / `informe` (según esquema del grado)
- `asistencia`
- `cargo` (matrícula o mensualidad: concepto, período, estado, fecha de pago, nota)

Integridad: un alumno, una inscripción activa por año. Un `es_principal` por alumno.

## 11. Orden de construcción

Cada fase deja software usable.

1. **Núcleo** — Postgres, auth, organización, membresías, fichas, portales que entran y no se ven entre colegios.
2. **Año escolar** — período, lapsos, grados, secciones.
3. **Inscripción** — cupo, sección, recaudos, representante obligatorio.
4. **Evaluación** — esquemas por nivel, carga, cierre de lapso, boletín.
5. **Asistencia** — lista diaria / por materia.
6. **Cobro mínimo** — estados de matrícula y mensualidad.
7. **Documentos PDF** — boletín e informe.

## 12. Criterio de éxito de v1

Un colegio privado puede: dar de alta alumnos de inicial, primaria y media; inscribirlos a una sección; pasar asistencia; cargar notas o informes; cerrar un lapso; que el representante vea boletín, faltas y si debe la mensualidad; que otro colegio en la misma base no vea nada de ese expediente.
