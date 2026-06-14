# chappie-notification

**Consumer de RabbitMQ para ejecución de agentes, TTS y notificaciones**

---

## Responsabilidad

- Consumir mensajes de RabbitMQ
- Ejecutar agentes de OpenCode en background
- Ejecutar comandos de terminal (whitelist)
- Generar audio TTS con volume ducking
- Enviar notificaciones con SwayNC
- Manejar errores y reintentos
- Gestionar preguntas/respuestas de agentes

## Estado

**Pendiente** - Será implementado en Fase 2

## Estructura Esperada

```
chappie-notification/
├── src/
│   ├── execution_consumer.py      # Ejecuta agentes y comandos
│   ├── error_consumer.py          # Maneja errores
│   ├── tts_consumer.py            # Genera y reproduce TTS
│   ├── notification_consumer.py   # Notificaciones interactivas
│   ├── rabbitmq_client.py         # Cliente RabbitMQ (aio-pika)
│   └── volume_controller.py       # Control de volume ducking
├── config/
│   └── config.yaml
├── requirements.txt
└── README.md
```

## Consumers

### execution_consumer
- Escucha: `chappie.responses`
- Ejecuta agent_call en background (opencode run --agent)
- Ejecuta terminal_command en background (valida whitelist)
- Publica: `chappie.tts.requests` (si éxito), `chappie.errors` (si falla)

### error_consumer
- Escucha: `chappie.errors`
- Llama a n8n error handler webhook
- Publica: `chappie.tts.requests` (con nueva respuesta)

### tts_consumer
- Escucha: `chappie.tts.requests`
- Genera audio con proveedor TTS configurado
- Aplica volume ducking
- Escribe archivos de estado para Quickshell
- Reproduce audio
- Restaura volumen

### notification_consumer
- Escucha: `chappie.agent.questions`, `chappie.agent.results`, `chappie.notifications`
- Crea notificaciones con SwayNC (acciones interactivas)
- Captura respuestas del usuario
- Publica: `chappie.agent.answers`

## Dependencias

- Python 3.12+
- aio-pika (RabbitMQ async client)
- edge-tts (TTS)
- requests (HTTP client)
- python-dotenv
- PyYAML

## Integraciones

- **RabbitMQ:** Consume y publica en colas
- **chappie-daemon:** Envía audio TTS para reproducción
- **OpenCode CLI:** Ejecuta agentes
- **SwayNC:** Notificaciones interactivas
- **n8n:** Error handler webhook

---

*Proyecto parte del workspace chappie-workspace*
