# Shared Context - chappie-notification / initial-setup

**Increment:** initial-setup  
**Lifecycle Status:** `validator-review`  
**Created:** 2026-06-14  
**Last Updated:** 2026-06-14  

---

## Current status

- **Estado del incremento:** `awaiting-human-plan-approval`
- **Fase actual:** Spec Validator otorgó veredicto `ready`. Todos los findings resueltos (7/7).
- **Bloqueadores:** Ninguno.
- **Alineación global:** Completa. system-landscape.md e integration-map.md sincronizados.
- **workspace_changes.md:** Revisado. No hay cambios globales pendientes que afecten este incremento directamente.
- **Siguiente paso:** Esperar aprobación humana del plan de implementación.

---

## Canonical artifacts

| Artefacto | Ruta | Estado |
|---|---|---|
| Master Spec local | `projects/chappie-notification/docs/specs/master_spec.md` | `planning` |
| Shared context | `projects/chappie-notification/docs/specs/.working/initial-setup-sdd-context.md` | `validator-review` |
| Master Spec global | `docs/specs/master_spec.md` | Active |
| System Landscape | `docs/architecture/system-landscape.md` | Active (corregido por Enterprise Architect — F-002) |
| Integration Map | `docs/architecture/integration-map.md` | Active (corregido por Enterprise Architect — F-003, F-007) |
| Workspace Changes | `docs/specs/workspace_changes.md` | Active |

---

## Artifact evidence

| Artefacto | Verificación | Resultado |
|---|---|---|
| Master Spec local | Revisada sección por sección. Arquitectura hexagonal correcta, 4 consumers bien definidos, contratos RabbitMQ/HTTP/CLI presentes. MemoryUpdate y NotificationRequest definidos en §3.1 (F-001 resuelto). ExecutionConsumer eliminado como producer injustificado de chappie.notifications (F-004 resuelto). NotificationConsumer documentado con modelo async D-Bus (F-005 resuelto). | `pass` |
| Master Spec global | Leída. Sección 3 lista chappie-notification correctamente. Sección 6 responsabilidades alineadas. Sección 4.2 colas RabbitMQ coinciden. | `pass` |
| System Landscape | Leído. Línea 52 corregida por Enterprise Architect: `Python 3 + aio-pika` (F-002 resuelto). | `pass` |
| Integration Map | Leído. Secciones 2.1-2.7 schemas completos. §2.2 incluye tts_consumer como producer (F-003 resuelto). §2.7 elimina SwayNC como consumer RabbitMQ (F-007 resuelto). | `pass` |
| Workspace Changes | Leído. Último cambio: completado initial-setup de chappie-daemon. Próximo: Fase 3 (chappie-notification). Sin conflictos directos. | `pass` |
| Shared context | Actualizado con todos los encabezados obligatorios. 7 findings resueltos (4 locales + 3 globales). | `pass` |

---

## Spec Validator Approval

verdict: ready
reviewed_at: 2026-06-14
validator_agent: spec-validator
artifact_set_reviewed:
- projects/chappie-notification/docs/specs/master_spec.md
- projects/chappie-notification/docs/specs/.working/initial-setup-sdd-context.md
- docs/specs/master_spec.md
- docs/architecture/integration-map.md
- docs/architecture/system-landscape.md
- docs/specs/workspace_changes.md
summary: 7 findings resueltos correctamente (1 blocker, 1 high, 3 medium, 2 low). MemoryUpdate y NotificationRequest definidos en dominio. system-landscape.md corregido a aio-pika. integration-map.md actualizado con tts_consumer como producer de chappie.errors. ExecutionConsumer eliminado como producer injustificado de chappie.notifications. NotificationConsumer async con D-Bus documentado. Nota: existe duplicación de heading ## Resolved findings (líneas 89 y 151) que debe eliminarse en próxima iteración de documentación (issue low sin impacto funcional).
invalidated_by_changes_since: none

---

## Decisions locked

1. **Arquitectura Hexagonal:** El proyecto usará la estructura domain/application/infrastructure con dependencia estricta unidireccional.
2. **Python 3.12+ con asyncio:** Stack principal del daemon.
3. **aio-pika:** Librería asíncrona para RabbitMQ (no pika síncrono).
4. **pydantic-settings:** Gestión centralizada de configuración.
5. **4 Consumers especializados:** ExecutionConsumer, ErrorConsumer, TTSConsumer, NotificationConsumer.
6. **Edge-TTS como proveedor TTS primario:** Con voz es-AR-ElenaNeural.
7. **SwayNC via notify-send:** Para notificaciones interactivas.
8. **Whitelist de comandos:** Validación obligatoria antes de ejecutar cualquier comando de terminal.
9. **Sin base de datos:** El proyecto no persiste datos localmente; solo escribe archivos de estado efímeros en /tmp.
10. **Sin volume ducking:** Responsabilidad exclusiva de chappie-daemon.
11. **Fire-and-forget para /play-tts:** Sin retry, solo log de error.
12. **Idempotencia por session_id + timestamp:** Para mensajes de RabbitMQ.
13. **NotificationConsumer async con D-Bus:** notify-send retorna inmediatamente (no bloquea event loop). La captura de acción del usuario se realiza via D-Bus signals de SwayNC. Timeout: 600s para preguntas de agente, 120s para notificaciones genéricas. Respuesta por defecto al expirar timeout: "ignore".

---

## Validator findings

_Todos los findings han sido resueltos. Ver `## Resolved findings` para detalles._

---

## Resolved findings

### Finding 1 — `blocker` — RESUELTO — Value Objects `MemoryUpdate` y `NotificationRequest` definidos

- **Acción:** Añadidas dataclass `NotificationRequest` y `MemoryUpdate` en §3.1 del Master Spec.
- **Campos definidos:**
  - `NotificationRequest`: `enabled: bool`, `title: str`, `message: str`, `urgency: NotificationUrgency`
  - `MemoryUpdate`: `save_to_memory: bool`, `tags: list[str]`
- **Alineación con integration-map.md §2.1:** Campos coinciden exactamente con el schema JSON.
- **Decomposition Contract §15.3:** Actualizado para incluir ambos DTOs.
- **Resuelto por:** Planner (corrección local).

### Finding 2 — `high` — RESUELTO — Contract drift system-landscape.md corregido

- **Acción:** Enterprise Architect corrigió `docs/architecture/system-landscape.md` línea 52.
- **Cambio:** `Python 3 + pika` → `Python 3 + aio-pika`
- **Resuelto por:** Enterprise Architect (corrección global).

### Finding 3 — `medium` — RESUELTO — Flujo de error de TTS alineado con integration-map

- **Acción:** Enterprise Architect actualizó `docs/architecture/integration-map.md` §2.2.
- **Cambio:** Producer de `chappie.errors` ahora incluye `tts_consumer` además de `execution_consumer`.
- **Resuelto por:** Enterprise Architect (corrección global).

### Finding 4 — `medium` — RESUELTO — ExecutionConsumer eliminado como producer injustificado

- **Acción:** Eliminado `ExecutionConsumer` como producer de `chappie.notifications` en §6.1 del Master Spec.
- **Razón:** No existe ningún flujo de negocio (§7) donde ExecutionConsumer publique en esta cola.
- **Cambio:** `Producer: n8n, ExecutionConsumer` → `Producer: n8n`
- **Alineación con integration-map.md §2.7:** Consistente (producer: n8n, chappie-notification genérico).
- **Resuelto por:** Planner (corrección local).

### Finding 5 — `medium` — RESUELTO — Open Question #4 resuelta: NotificationConsumer async

- **Decisión arquitectónica:** NotificationConsumer usa modelo asíncrono con D-Bus signals de SwayNC.
- **Mecanismo:**
  1. `notify-send` retorna inmediatamente con notification_id (no bloquea event loop).
  2. Se registra listener D-Bus para capturar acción del usuario.
  3. `asyncio.Event` sincroniza la espera de respuesta.
  4. Timeout: 600s para preguntas de agente, 120s para notificaciones genéricas.
  5. Respuesta por defecto al expirar timeout: "ignore".
- **Artefactos actualizados:**
  - Master Spec §4.1 `ShowNotificationUseCase`: Documentado mecanismo async.
  - Master Spec §4.2 `NotificationSenderPort`: Añadido método `wait_for_action()`.
  - Master Spec §5.1 `NotificationConsumer`: Documentado modelo de ejecución async.
  - Shared Context `## Decisions locked`: Añadida decisión #13.
- **Resuelto por:** Planner (decisión arquitectónica local).

### Finding 6 — `low` — RESUELTO — Estado obsoleto corregido

- **Acción:** Lifecycle status de Master Spec actualizado de `revision-needed` a `planning`.
- **Shared Context:** Estado actualizado a `validator-review`.
- **Resuelto por:** Planner (corrección local).

### Finding 7 — `low` — RESUELTO — SwayNC eliminado como consumer RabbitMQ

- **Acción:** Enterprise Architect corrigió `docs/architecture/integration-map.md` §2.7.
- **Cambio:** Eliminado `SwayNC` como consumer. Aclarado que la integración es via D-Bus/notify-send.
- **Resuelto por:** Enterprise Architect (corrección global).

---

## Resolved findings

_N/A (primera versión de la spec)._

---

## Open questions

1. **¿Se requiere containerización (Docker) para chappie-notification?** La Master Spec global lo lista como "Python 3 + aio-pika" sin mencionar Docker. Se asume ejecución directa con systemd.
2. **¿El archivo commands-whitelist.yaml se copia desde chappie-config o se mantiene local?** Se asume copia local en `config/commands-whitelist.yaml`.
3. **¿Se necesita un health check HTTP endpoint?** Se marca como "Futuras Mejoras" pero podría ser necesario desde el inicio.
4. ~~**¿El NotificationConsumer debe esperar la respuesta del usuario de forma bloqueante o asíncrona?**~~ **RESUELTA:** Ver Decisión locked #13 (async con D-Bus signals de SwayNC).

---

## Stale terms guard

| Término prohibido | Término correcto | Razón |
|---|---|---|
| "TTS Generator workflow" | N/A (no existe en n8n) | La generación TTS es responsabilidad de chappie-notification |
| "chappie-n8n-workflows ejecuta agentes" | "chappie-notification ejecuta agentes" | Corregido en workspace_changes.md 2026-06-14 |
| "chappie-notification hace volume ducking" | "chappie-daemon hace volume ducking" | Responsabilidad exclusiva de chappie-daemon |
| "pika" (síncrono) | "aio-pika" (asíncrono) | Decisión arquitectónica para no bloquear event loop |

---

## Next action

**Awaiting Human Plan Approval** — Spec Validator otorgó veredicto `ready`.

**Flujo SDD vigente:**
1. ✅ Spec Validator validó y otorgó `verdict: ready` (2026-06-14).
2. ⏳ Esperar aprobación humana del plan de implementación (`## Human Plan Approval: pending`).
3. Tras aprobación humana, handoff a Task Decomposer.

**Nota de documentación:** Planner debe eliminar el heading duplicado `## Resolved findings` (líneas 151-153) en la próxima iteración.

---

## Human Plan Approval: pending

_Pendiente de aprobación humana del plan de implementación._

---

*Documento mantenido por: Planner*
