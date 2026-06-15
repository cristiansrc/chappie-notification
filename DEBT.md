# Technical Debt Register

## D-Bus Implementation Incompleta

**ID:** DEBT-001
**Status:** `acknowledged`
**Severity:** High
**Area:** `SwayNCNotificationSenderAdapter._wait_via_dbus`
**Created:** 2026-06-14

### Descripción

La implementación actual de `_wait_via_dbus` en `SwayNCNotificationSenderAdapter` utiliza un enfoque de polling/fallback en lugar de escuchar correctamente las señales D-Bus de SwayNC (`org.erikreider.swaync.cc.ActionInvoked`).

### Problema

1. **Signal listener no implementado:** Aunque se crea un proxy D-Bus a `org.erikreider.swaync.cc`, no se conecta el callback para el signal `ActionInvoked`. Como resultado, `notification_event.wait()` nunca es señalizado y siempre expira con timeout.
2. **Fallback a sleep síncrono:** Cuando D-Bus no está disponible, el código cae en `await asyncio.sleep(timeout_seconds)`, que bloquea innecesariamente el event loop.
3. **Sin manejo de reconexión:** Si el servicio D-Bus de SwayNC se reinicia, el proxy existente queda stale sin reconexión automática.

### Impacto

- Las notificaciones con acciones (preguntas de agente) nunca reciben respuesta del usuario real.
- Siempre se usa el valor por defecto `"ignore"` después del timeout.
- La funcionalidad de notificaciones interactivas con SwayNC está efectivamente deshabilitada.

### Solución Propuesta

1. Usar `dasbus.loop.EventLoop` o el listener de signals de dasbus para conectar correctamente el signal `ActionInvoked` al `asyncio.Event`.
2. Alternativa: Implementar un bus D-Bus nativo con `dbus-next` (asincrónico) que soporte señales de forma nativa.
3. Eliminar el `asyncio.sleep` de los fallbacks y usar timeouts reales.

### Prioridad

Alta - Impacta directamente la experiencia de usuario con agentes interactivos.

---

## Estado de Implementación de D-Bus

Las notificaciones se envían correctamente mediante `notify-send` (CLI de SwayNC). La parte de captura de respuesta del usuario mediante D-Bus signals (`org.erikreider.swaync.cc.ActionInvoked`) está pendiente de implementación completa.

Actualmente:
- ✅ `send()`: Funcional - envía notificaciones vía `notify-send`
- ❌ `wait_for_action()`: Limitado - usa timeout como fallback porque la escucha de D-Bus signals no está correctamente conectada
- ⏳ `_wait_via_dbus()`: Implementación parcial - crea el proxy D-Bus pero no conecta los signals
