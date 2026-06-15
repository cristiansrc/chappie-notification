# Master Spec - chappie-notification

**Lifecycle Status:** `Active`  
**Owner:** Planner  
**Project Path:** `projects/chappie-notification/`  
**Created:** 2026-06-14  
**Last Updated:** 2026-06-14  

---

## 1. Propósito del Proyecto

`chappie-notification` es un daemon en Python que actúa como el **centro de procesamiento de eventos** del ecosistema Chappie. Consume colas de RabbitMQ, ejecuta agentes de OpenCode, genera audio TTS, maneja errores y muestra notificaciones interactivas al usuario.

### Responsabilidades Principales

1. **Consumir eventos de RabbitMQ** mediante 4 consumidores especializados.
2. **Ejecutar agentes de OpenCode** y comandos de terminal en background.
3. **Generar audio TTS** usando Edge-TTS y enviarlo a chappie-daemon para reproducción.
4. **Manejar errores** de ejecución y delegar a n8n para regeneración de respuestas.
5. **Mostrar notificaciones interactivas** con SwayNC para preguntas de agentes.
6. **Escribir archivos de estado** para el widget de Quickshell.

### Responsabilidades NO incluidas

- No realiza volume ducking (responsabilidad de chappie-daemon).
- No escribe `chappie_tts_state.txt` (responsabilidad de chappie-daemon).
- No ejecuta STT (responsabilidad de n8n).
- No captura audio (responsabilidad de chappie-daemon).

---

## 2. Arquitectura Hexagonal

### 2.1 Capas

```
chappie-notification/
├── src/
│   ├── domain/                    # Núcleo de dominio (ZERO dependencies)
│   │   ├── models/                # Entidades y value objects
│   │   ├── events/                # Domain events
│   │   └── exceptions/            # Domain exceptions
│   │
│   ├── application/               # Capa de aplicación
│   │   ├── use_cases/             # Input ports (use cases)
│   │   ├── ports/                 # Output ports (interfaces)
│   │   └── dto/                   # Command/Query/Result objects
│   │
│   └── infrastructure/            # Capa de infraestructura
│       ├── consumers/             # Driving adapters (RabbitMQ consumers)
│       ├── adapters/              # Driven adapters (implementaciones)
│       ├── config/                # Configuración y wiring
│       └── mappers/               # Mappers entre capas
│
├── tests/
│   ├── unit/                      # Tests de dominio y aplicación
│   ├── integration/               # Tests de infraestructura
│   └── e2e/                       # Tests end-to-end
│
├── pyproject.toml                 # Configuración del proyecto (uv)
├── Dockerfile                     # Containerización (opcional)
└── README.md
```

### 2.2 Dirección de Dependencias

```
infrastructure → application → domain
     (depende de)   (depende de)  (ZERO dependencias)
```

- `domain`: No depende de ninguna otra capa. Sin imports de frameworks, librerías externas, HTTP, JSON, colas, etc.
- `application`: Depende solo de `domain`. Define interfaces (ports) que `infrastructure` implementa.
- `infrastructure`: Depende de `application` y `domain`. Implementa los ports y conecta con el mundo exterior.

---

## 3. Modelo de Dominio

### 3.1 Entidades y Value Objects

#### `ChappieResponse` (Entity)
Representa una respuesta procesada del modelo de IA que puede incluir acciones.

```python
@dataclass(frozen=True)
class ChappieResponse:
    session_id: UUID
    timestamp: datetime
    voice_response: str
    agent_call: AgentCall | None
    terminal_command: TerminalCommand | None
    notification: NotificationRequest | None
    memory_update: MemoryUpdate | None
```

#### `AgentCall` (Value Object)
```python
@dataclass(frozen=True)
class AgentCall:
    enabled: bool
    agent: str
    prompt: str
    notify_on_complete: bool
```

#### `TerminalCommand` (Value Object)
```python
@dataclass(frozen=True)
class TerminalCommand:
    enabled: bool
    command: str
    requires_confirmation: bool
```

#### `NotificationRequest` (Value Object)
```python
@dataclass(frozen=True)
class NotificationRequest:
    enabled: bool
    title: str
    message: str
    urgency: NotificationUrgency  # enum: LOW, NORMAL, CRITICAL
```

#### `MemoryUpdate` (Value Object)
```python
@dataclass(frozen=True)
class MemoryUpdate:
    save_to_memory: bool
    tags: list[str]
```

#### `TTSRequest` (Value Object)
```python
@dataclass(frozen=True)
class TTSRequest:
    session_id: UUID
    timestamp: datetime
    text: str
    priority: TTSPriority  # enum: NORMAL, HIGH
    ducking: bool
    show_text: bool
```

#### `AgentResult` (Value Object)
```python
@dataclass(frozen=True)
class AgentResult:
    session_id: UUID
    timestamp: datetime
    agent: str
    status: ExecutionStatus  # enum: SUCCESS, FAILURE
    result: str
    notify_user: bool
```

#### `AgentQuestion` (Value Object)
```python
@dataclass(frozen=True)
class AgentQuestion:
    session_id: UUID
    timestamp: datetime
    agent: str
    question: str
    options: list[QuestionOption]
    notification_id: UUID
```

#### `QuestionOption` (Value Object)
```python
@dataclass(frozen=True)
class QuestionOption:
    key: str
    label: str
```

#### `AgentAnswer` (Value Object)
```python
@dataclass(frozen=True)
class AgentAnswer:
    notification_id: UUID
    session_id: UUID
    timestamp: datetime
    answer: str
```

#### `ErrorMessage` (Value Object)
```python
@dataclass(frozen=True)
class ErrorMessage:
    session_id: UUID
    timestamp: datetime
    original_request: str
    error_type: ErrorType  # enum: AGENT_FAILURE, COMMAND_FAILURE, VALIDATION_ERROR
    error: str
    context: ErrorContext | None
```

#### `ErrorContext` (Value Object)
```python
@dataclass(frozen=True)
class ErrorContext:
    agent: str | None
    command: str | None
```

#### `NotificationMessage` (Value Object)
```python
@dataclass(frozen=True)
class NotificationMessage:
    timestamp: datetime
    title: str
    message: str
    urgency: NotificationUrgency  # enum: LOW, NORMAL, CRITICAL
    actions: list[NotificationAction]
    category: NotificationCategory  # enum: AGENT_COMPLETE, ERROR, INFO, QUESTION
```

#### `NotificationAction` (Value Object)
```python
@dataclass(frozen=True)
class NotificationAction:
    key: str
    label: str
```

### 3.2 Enums de Dominio

```python
class TTSPriority(str, Enum):
    NORMAL = "normal"
    HIGH = "high"

class ExecutionStatus(str, Enum):
    SUCCESS = "success"
    FAILURE = "failure"

class ErrorType(str, Enum):
    AGENT_FAILURE = "agent_failure"
    COMMAND_FAILURE = "command_failure"
    VALIDATION_ERROR = "validation_error"

class NotificationUrgency(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    CRITICAL = "critical"

class NotificationCategory(str, Enum):
    AGENT_COMPLETE = "agent_complete"
    ERROR = "error"
    INFO = "info"
    QUESTION = "question"
```

### 3.3 Domain Events

```python
@dataclass(frozen=True)
class AgentExecutionStarted:
    session_id: UUID
    agent: str
    timestamp: datetime

@dataclass(frozen=True)
class AgentExecutionCompleted:
    session_id: UUID
    agent: str
    status: ExecutionStatus
    result: str
    timestamp: datetime

@dataclass(frozen=True)
class TTSGenerationRequested:
    session_id: UUID
    text: str
    priority: TTSPriority
    timestamp: datetime
```

### 3.4 Domain Exceptions

```python
class CommandNotAllowedError(Exception):
    """Comando no permitido por whitelist."""
    pass

class AgentExecutionError(Exception):
    """Error durante la ejecución de un agente."""
    pass

class TTSGenerationError(Exception):
    """Error durante la generación de audio TTS."""
    pass

class NotificationError(Exception):
    """Error al crear o enviar una notificación."""
    pass
```

---

## 4. Capa de Aplicación

### 4.1 Input Ports (Use Cases)

#### `ProcessResponseUseCase`
Procesa una respuesta del modelo de IA y decide qué acciones ejecutar.

```python
class ProcessResponseUseCase(Protocol):
    async def execute(self, response: ChappieResponse) -> ProcessResponseResult:
        """
        Procesa la respuesta y:
        1. Si hay agent_call → ejecuta en background
        2. Si hay terminal_command → ejecuta en background
        3. Si hay voice_response → publica TTS request
        4. Si hay notification → publica notificación
        """
        ...
```

#### `HandleErrorUseCase`
Maneja errores de ejecución y delega a n8n.

```python
class HandleErrorUseCase(Protocol):
    async def execute(self, error: ErrorMessage) -> HandleErrorResult:
        """
        1. NO reproduce voz original
        2. Llama al webhook de n8n (chappie-error-handler)
        3. n8n genera nueva respuesta y publica en chappie.tts.requests
        """
        ...
```

#### `GenerateTTSUseCase`
Genera audio TTS y lo envía a chappie-daemon.

```python
class GenerateTTSUseCase(Protocol):
    async def execute(self, request: TTSRequest) -> GenerateTTSResult:
        """
        1. Genera audio con Edge-TTS
        2. Guarda en /tmp/chappie_tts.mp3
        3. Escribe texto en /tmp/chappie_tts_text.txt
        4. Envía POST /play-tts a chappie-daemon
        """
        ...
```

#### `ShowNotificationUseCase`
Muestra notificaciones interactivas con SwayNC.

```python
class ShowNotificationUseCase(Protocol):
    async def execute(self, notification: NotificationMessage) -> ShowNotificationResult:
        """
        1. Crea notificación SwayNC con notify-send (retorna notification_id inmediatamente)
        2. Si hay acciones → registra listener D-Bus para capturar acción del usuario
        3. Espera respuesta del usuario con timeout (600s para preguntas, 120s para genéricas)
        4. Publica respuesta en chappie.agent.answers (si es pregunta de agente)
        
        Mecanismo asíncrono:
        - notify-send retorna inmediatamente (no bloquea el event loop)
        - Se captura la acción del usuario via D-Bus signal de SwayNC
        - asyncio.Event se usa para sincronizar la espera de la respuesta
        - Timeout expirado → se considera "ignore" como respuesta por defecto
        """
        ...
```

#### `ExecuteAgentUseCase`
Ejecuta un agente de OpenCode en background.

```python
class ExecuteAgentUseCase(Protocol):
    async def execute(self, agent_call: AgentCall, session_id: UUID) -> ExecuteAgentResult:
        """
        1. Ejecuta: opencode run --agent <agent> "<prompt>"
        2. Monitorea ejecución en background
        3. Publica resultado en chappie.agent.results
        """
        ...
```

#### `ExecuteCommandUseCase`
Ejecuta un comando de terminal en background.

```python
class ExecuteCommandUseCase(Protocol):
    async def execute(self, command: TerminalCommand, session_id: UUID) -> ExecuteCommandResult:
        """
        1. Valida contra whitelist
        2. Ejecuta comando en background
        3. Publica resultado en chappie.agent.results
        """
        ...
```

### 4.2 Output Ports (Interfaces)

#### `RabbitMQPublisherPort`
Publica mensajes en colas de RabbitMQ.

```python
class RabbitMQPublisherPort(Protocol):
    async def publish(self, queue: str, message: dict, headers: dict | None = None) -> None:
        """Publica un mensaje en la cola especificada."""
        ...
```

#### `TTSSynthesizerPort`
Genera audio TTS desde texto.

```python
class TTSSynthesizerPort(Protocol):
    async def synthesize(self, text: str, voice: str, output_path: str) -> str:
        """Genera audio TTS y retorna la ruta del archivo generado."""
        ...
```

#### `AgentExecutorPort`
Ejecuta agentes de OpenCode.

```python
class AgentExecutorPort(Protocol):
    async def execute(self, agent: str, prompt: str, timeout: int = 120) -> AgentExecutionResult:
        """Ejecuta un agente y retorna el resultado."""
        ...
```

#### `CommandExecutorPort`
Ejecuta comandos de terminal.

```python
class CommandExecutorPort(Protocol):
    async def execute(self, command: str, timeout: int = 30) -> CommandExecutionResult:
        """Ejecuta un comando y retorna el resultado."""
        ...
```

#### `CommandValidatorPort`
Valida comandos contra whitelist.

```python
class CommandValidatorPort(Protocol):
    def is_allowed(self, command: str) -> bool:
        """Retorna True si el comando está permitido."""
        ...
```

#### `NotificationSenderPort`
Envía notificaciones al sistema.

```python
class NotificationSenderPort(Protocol):
    async def send(self, title: str, message: str, urgency: str, actions: list[dict]) -> str | None:
        """
        Envía notificación via notify-send y retorna inmediatamente.
        Retorna el notification_id si hay acciones (para capturar respuesta posterior).
        Retorna None si no hay acciones (notificación informativa).
        No bloquea el event loop.
        """
        ...
    
    async def wait_for_action(self, notification_id: str, timeout_seconds: int) -> str | None:
        """
        Espera de forma asíncrona la acción del usuario sobre una notificación.
        Usa D-Bus signals de SwayNC para capturar la acción seleccionada.
        Retorna la key de la acción seleccionada o None si expira el timeout.
        """
        ...
```

#### `HTTPClientPort`
Realiza llamadas HTTP a servicios externos.

```python
class HTTPClientPort(Protocol):
    async def post(self, url: str, json: dict, headers: dict | None = None, timeout: int = 10) -> dict:
        """Realiza un POST HTTP y retorna la respuesta."""
        ...
```

#### `FileWriterPort`
Escribe archivos de estado.

```python
class FileWriterPort(Protocol):
    async def write(self, path: str, content: str) -> None:
        """Escribe contenido en un archivo."""
        ...
```

### 4.3 DTOs (Command/Query/Result Objects)

```python
@dataclass(frozen=True)
class ProcessResponseResult:
    success: bool
    tts_requested: bool
    agent_started: bool
    command_started: bool
    error: str | None = None

@dataclass(frozen=True)
class HandleErrorResult:
    success: bool
    n8n_notified: bool
    error: str | None = None

@dataclass(frozen=True)
class GenerateTTSResult:
    success: bool
    audio_path: str | None = None
    error: str | None = None

@dataclass(frozen=True)
class ShowNotificationResult:
    success: bool
    notification_id: str | None = None
    user_answer: str | None = None
    error: str | None = None

@dataclass(frozen=True)
class ExecuteAgentResult:
    success: bool
    status: ExecutionStatus
    result: str
    error: str | None = None

@dataclass(frozen=True)
class CommandExecutionResult:
    success: bool
    stdout: str
    stderr: str
    exit_code: int

@dataclass(frozen=True)
class AgentExecutionResult:
    success: bool
    stdout: str
    stderr: str
    exit_code: int
```

---

## 5. Capa de Infraestructura

### 5.1 Driving Adapters (RabbitMQ Consumers)

#### `ExecutionConsumer`
Consume la cola `chappie.responses`.

```python
class ExecutionConsumer:
    """
    Consume mensajes de chappie.responses y delega a ProcessResponseUseCase.
    
    Cola: chappie.responses
    Ack: Manual (after processing)
    DLQ: chappie.responses.dlq
    TTL: 60 segundos
    Idempotency: session_id + timestamp
    """
    
    async def on_message(self, body: bytes, properties: dict) -> None:
        """Procesa el mensaje y delega al use case."""
        ...
```

#### `ErrorConsumer`
Consume la cola `chappie.errors`.

```python
class ErrorConsumer:
    """
    Consume mensajes de chappie.errors y delega a HandleErrorUseCase.
    
    Cola: chappie.errors
    Ack: Manual
    DLQ: chappie.errors.dlq
    TTL: 30 segundos
    """
    
    async def on_message(self, body: bytes, properties: dict) -> None:
        """Procesa el error y delega al use case."""
        ...
```

#### `TTSConsumer`
Consume la cola `chappie.tts.requests`.

```python
class TTSConsumer:
    """
    Consume mensajes de chappie.tts.requests y delega a GenerateTTSUseCase.
    
    Cola: chappie.tts.requests
    Ack: Manual
    Priority: High (para respuestas de error)
    TTL: 30 segundos
    """
    
    async def on_message(self, body: bytes, properties: dict) -> None:
        """Genera TTS y delega al use case."""
        ...
```

#### `NotificationConsumer`
Consume las colas `chappie.agent.results`, `chappie.agent.questions`, `chappie.notifications`.

```python
class NotificationConsumer:
    """
    Consume mensajes de múltiples colas de notificación.
    
    Colas:
    - chappie.agent.results (TTL: 300s)
    - chappie.agent.questions (TTL: 600s)
    - chappie.notifications (TTL: 120s)
    
    Ack: Manual
    
    Modelo de ejecución:
    - Cada mensaje se procesa de forma asíncrona usando asyncio.create_task()
    - El consumer NO bloquea el event loop mientras espera respuesta del usuario
    - Para preguntas de agente: se crea un listener D-Bus que espera la acción del usuario
    - Timeout de respuesta: 600s para preguntas, 120s para notificaciones genéricas
    - Si expira el timeout: se considera "ignore" como respuesta por defecto
    """
    
    async def on_agent_result(self, body: bytes, properties: dict) -> None:
        """Muestra resultado de agente como notificación (fire-and-forget, sin espera)."""
        ...
    
    async def on_agent_question(self, body: bytes, properties: dict) -> None:
        """
        Muestra pregunta de agente con acciones interactivas.
        Crea task asíncrona para esperar respuesta del usuario sin bloquear el consumer.
        """
        ...
    
    async def on_notification(self, body: bytes, properties: dict) -> None:
        """Muestra notificación genérica (fire-and-forget, sin espera)."""
        ...
```

### 5.2 Driven Adapters (Implementaciones)

#### `RabbitMQPublisherAdapter`
Implementa `RabbitMQPublisherPort` usando `aio-pika`.

```python
class RabbitMQPublisherAdapter:
    """Publica mensajes en RabbitMQ usando aio-pika."""
    
    def __init__(self, connection_url: str):
        self.connection_url = connection_url
    
    async def publish(self, queue: str, message: dict, headers: dict | None = None) -> None:
        """Publica mensaje con retry y error handling."""
        ...
```

#### `EdgeTTSSynthesizerAdapter`
Implementa `TTSSynthesizerPort` usando Edge-TTS.

```python
class EdgeTTSSynthesizerAdapter:
    """Genera audio TTS usando Microsoft Edge-TTS."""
    
    def __init__(self, voice: str = "es-AR-ElenaNeural"):
        self.voice = voice
    
    async def synthesize(self, text: str, voice: str, output_path: str) -> str:
        """Genera audio y guarda en output_path."""
        ...
```

#### `OpenCodeAgentExecutorAdapter`
Implementa `AgentExecutorPort` usando subprocess.

```python
class OpenCodeAgentExecutorAdapter:
    """Ejecuta agentes de OpenCode usando subprocess."""
    
    async def execute(self, agent: str, prompt: str, timeout: int = 120) -> AgentExecutionResult:
        """
        Ejecuta: opencode run --agent <agent> "<prompt>"
        Timeout: 120 segundos
        """
        ...
```

#### `SubprocessCommandExecutorAdapter`
Implementa `CommandExecutorPort` usando asyncio.subprocess.

```python
class SubprocessCommandExecutorAdapter:
    """Ejecuta comandos de terminal usando asyncio.subprocess."""
    
    async def execute(self, command: str, timeout: int = 30) -> CommandExecutionResult:
        """Ejecuta comando y captura stdout/stderr."""
        ...
```

#### `WhitelistCommandValidatorAdapter`
Implementa `CommandValidatorPort` usando YAML config.

```python
class WhitelistCommandValidatorAdapter:
    """Valida comandos contra commands-whitelist.yaml."""
    
    def __init__(self, whitelist_path: str):
        self.whitelist = self._load_whitelist(whitelist_path)
    
    def is_allowed(self, command: str) -> bool:
        """Retorna True si el comando matchea un patrón permitido."""
        ...
```

#### `SwayNCNotificationSenderAdapter`
Implementa `NotificationSenderPort` usando notify-send.

```python
class SwayNCNotificationSenderAdapter:
    """Envía notificaciones usando notify-send (SwayNC)."""
    
    async def send(self, title: str, message: str, urgency: str, actions: list[dict]) -> str | None:
        """
        Ejecuta: notify-send "title" "message" --action="key=label" ...
        Retorna notification_id si hay acciones.
        """
        ...
```

#### `HTTPXClientAdapter`
Implementa `HTTPClientPort` usando httpx.

```python
class HTTPXClientAdapter:
    """Cliente HTTP usando httpx con retry y timeout."""
    
    async def post(self, url: str, json: dict, headers: dict | None = None, timeout: int = 10) -> dict:
        """POST HTTP con retry exponencial."""
        ...
```

#### `AsyncFileWriterAdapter`
Implementa `FileWriterPort` usando aiofiles.

```python
class AsyncFileWriterAdapter:
    """Escribe archivos de forma asíncrona."""
    
    async def write(self, path: str, content: str) -> None:
        """Escribe contenido en archivo."""
        ...
```

### 5.3 Configuración

#### `AppConfig`
Configuración centralizada usando pydantic-settings.

```python
class AppConfig(BaseSettings):
    # RabbitMQ
    rabbitmq_url: str = "amqp://guest:guest@localhost:5672/"
    
    # chappie-daemon
    daemon_base_url: str = "http://localhost:8765"
    
    # n8n
    n8n_base_url: str = "http://localhost:5678"
    n8n_webhook_secret: str = ""
    
    # TTS
    tts_voice: str = "es-AR-ElenaNeural"
    tts_output_path: str = "/tmp/chappie_tts.mp3"
    tts_text_path: str = "/tmp/chappie_tts_text.txt"
    
    # Whitelist
    whitelist_path: str = "./config/commands-whitelist.yaml"
    
    # Timeouts
    agent_timeout: int = 120
    command_timeout: int = 30
    http_timeout: int = 10
    
    model_config = SettingsConfigDict(env_prefix="CHAPPIE_")
```

---

## 6. Contratos de Integración

### 6.1 RabbitMQ - Colas Consumidas

#### Cola: `chappie.responses`
- **Producer:** n8n (Voice Pipeline Workflow)
- **Consumer:** ExecutionConsumer
- **Schema:** Ver sección 2.1 de integration-map.md
- **Durability:** Durable
- **Ack:** Manual (after processing)
- **DLQ:** chappie.responses.dlq
- **TTL:** 60 segundos
- **Idempotency:** session_id + timestamp

#### Cola: `chappie.errors`
- **Producer:** ExecutionConsumer (chappie-notification)
- **Consumer:** ErrorConsumer (chappie-notification)
- **Schema:** Ver sección 2.2 de integration-map.md
- **Durability:** Durable
- **Ack:** Manual
- **DLQ:** chappie.errors.dlq
- **TTL:** 30 segundos

#### Cola: `chappie.tts.requests`
- **Producer:** ExecutionConsumer, ErrorConsumer, n8n (Error Handler)
- **Consumer:** TTSConsumer
- **Schema:** Ver sección 2.3 de integration-map.md
- **Durability:** Durable
- **Ack:** Manual
- **Priority:** High (para respuestas de error)
- **TTL:** 30 segundos

#### Cola: `chappie.agent.results`
- **Producer:** ExecutionConsumer
- **Consumer:** NotificationConsumer
- **Schema:** Ver sección 2.4 de integration-map.md
- **Durability:** Durable
- **Ack:** Manual
- **TTL:** 300 segundos

#### Cola: `chappie.agent.questions`
- **Producer:** Agentes de OpenCode (via n8n)
- **Consumer:** NotificationConsumer
- **Schema:** Ver sección 2.5 de integration-map.md
- **Durability:** Durable
- **Ack:** Manual
- **TTL:** 600 segundos

#### Cola: `chappie.notifications`
- **Producer:** n8n
- **Consumer:** NotificationConsumer
- **Schema:** Ver sección 2.7 de integration-map.md
- **Durability:** Durable
- **Ack:** Manual
- **TTL:** 120 segundos

### 6.2 RabbitMQ - Colas Producidas

#### Cola: `chappie.tts.requests`
- **Producer:** ExecutionConsumer (cuando hay voice_response)
- **Schema:** Ver sección 2.3 de integration-map.md

#### Cola: `chappie.errors`
- **Producer:** ExecutionConsumer (cuando hay error de ejecución)
- **Schema:** Ver sección 2.2 de integration-map.md

#### Cola: `chappie.agent.results`
- **Producer:** ExecutionConsumer (después de ejecutar agente/comando)
- **Schema:** Ver sección 2.4 de integration-map.md

#### Cola: `chappie.agent.answers`
- **Producer:** NotificationConsumer (cuando usuario responde pregunta)
- **Schema:** Ver sección 2.6 de integration-map.md

### 6.3 HTTP - Endpoints Consumidos

#### `POST /play-tts` (chappie-daemon)
- **URL:** `http://localhost:8765/play-tts`
- **Owner:** chappie-daemon
- **Timeout:** 5 segundos
- **Retry:** No (fire-and-forget)
- **Request:**
  ```json
  {
    "audio_file": "/tmp/chappie_tts.mp3",
    "text": "texto que se está reproduciendo",
    "ducking": true
  }
  ```
- **Response:**
  ```json
  {
    "status": "completed"
  }
  ```

#### `POST /webhook/chappie-error-handler` (n8n)
- **URL:** `http://localhost:5678/webhook/chappie-error-handler`
- **Owner:** chappie-n8n-workflows
- **Timeout:** 15 segundos
- **Retry:** 2 intentos
- **Auth:** Header `X-Webhook-Secret`
- **Request:**
  ```json
  {
    "original_request": "texto original del usuario",
    "error": "descripción del error",
    "context": "contexto adicional",
    "session_id": "uuid-v4"
  }
  ```
- **Response:**
  ```json
  {
    "status": "accepted",
    "workflow_execution_id": "n8n-exec-id"
  }
  ```

### 6.4 CLI - Comandos Ejecutados

#### OpenCode CLI
- **Comando:** `opencode run --agent <agent> "<prompt>"`
- **Timeout:** 120 segundos
- **Retry:** No (se maneja via RabbitMQ)

#### notify-send (SwayNC)
- **Comando:** `notify-send "title" "message" --action="key=label" ...`
- **Timeout:** 5 segundos
- **Retry:** No

### 6.5 Archivos de Estado Escritos

#### `/tmp/chappie_tts_text.txt`
- **Writer:** TTSConsumer (chappie-notification)
- **Reader:** chappie-quickshell (ChappieTextWidget)
- **Format:** Texto plano
- **Contenido:** Texto que se está reproduciendo con TTS

---

## 7. Flujos de Negocio

### 7.1 Flujo de Respuesta Normal (Happy Path)

```
1. n8n publica en chappie.responses
   {
     "session_id": "uuid",
     "voice_response": "Hola Creador, ¿en qué puedo ayudarte?",
     "agent_call": { "enabled": false, ... },
     "terminal_command": { "enabled": false, ... }
   }
        │
        ▼
2. ExecutionConsumer recibe el mensaje
        │
        ▼
3. ProcessResponseUseCase procesa:
        ├──▶ SI hay agent_call.enabled = true:
        │   ├──▶ ExecuteAgentUseCase ejecuta en background
        │   ├──▶ Publica AgentExecutionStarted event
        │   └──▶ Monitorea: éxito → chappie.agent.results | error → chappie.errors
        │
        ├──▶ SI hay terminal_command.enabled = true:
        │   ├──▶ ExecuteCommandUseCase valida contra whitelist
        │   ├──▶ SI permitido → ejecuta en background
        │   └──▶ Monitorea: éxito → chappie.agent.results | error → chappie.errors
        │
        └──▶ SI hay voice_response:
            └──▶ Publica en chappie.tts.requests
                {
                  "session_id": "uuid",
                  "text": "Hola Creador, ¿en qué puedo ayudarte?",
                  "priority": "normal",
                  "ducking": true,
                  "show_text": true
                }
        │
        ▼
4. TTSConsumer recibe el mensaje
        │
        ▼
5. GenerateTTSUseCase ejecuta:
        ├──▶ EdgeTTSSynthesizerAdapter genera audio
        │   └──▶ edge-tts --voice es-AR-ElenaNeural --text "..." --write-media /tmp/chappie_tts.mp3
        ├──▶ FileWriterAdapter escribe texto en /tmp/chappie_tts_text.txt
        └──▶ HTTPClientAdapter envía POST /play-tts a chappie-daemon
            └──▶ chappie-daemon reproduce audio y gestiona ducking
```

### 7.2 Flujo de Error

```
1. ExecutionConsumer detecta error (ej. agente falla)
        │
        ▼
2. Publica en chappie.errors
   {
     "session_id": "uuid",
     "original_request": "texto original",
     "error_type": "agent_failure",
     "error": "Agente X falló con error Y",
     "context": { "agent": "X" }
   }
        │
        ▼
3. ErrorConsumer recibe el mensaje
        │
        ▼
4. HandleErrorUseCase ejecuta:
        ├──▶ NO reproduce voz original
        ├──▶ HTTPClientAdapter llama a n8n webhook
        │   └──▶ POST /webhook/chappie-error-handler
        │       {
        │         "original_request": "...",
        │         "error": "...",
        │         "context": "...",
        │         "session_id": "uuid"
        │       }
        └──▶ n8n genera nueva respuesta y publica en chappie.tts.requests
        │
        ▼
5. TTSConsumer procesa normalmente (ver flujo 7.1 paso 4-5)
```

### 7.3 Flujo de Notificación Interactiva

```
1. Agente necesita preguntar algo → publica en chappie.agent.questions
   {
     "session_id": "uuid",
     "agent": "code-reviewer",
     "question": "¿Deseas aplicar estos cambios?",
     "options": [
       {"key": "apply", "label": "Aplicar"},
       {"key": "reject", "label": "Rechazar"},
       {"key": "ignore", "label": "Ignorar"}
     ],
     "notification_id": "uuid"
   }
        │
        ▼
2. NotificationConsumer.on_agent_question recibe el mensaje
        │
        ▼
3. ShowNotificationUseCase ejecuta:
        ├──▶ NotificationSenderAdapter crea notificación SwayNC
        │   └──▶ notify-send "Chappie necesita tu atención" \
        │       "¿Deseas aplicar estos cambios?" \
        │       --action="apply=Aplicar" \
        │       --action="reject=Rechazar" \
        │       --action="ignore=Ignorar"
        │
        └──▶ Espera respuesta del usuario (captura acción)
        │
        ▼
4. Usuario hace clic en "Aplicar"
        │
        ▼
5. NotificationConsumer publica en chappie.agent.answers
   {
     "notification_id": "uuid",
     "session_id": "uuid",
     "answer": "apply"
   }
        │
        ▼
6. Agente recibe la respuesta y continúa
```

---

## 8. Manejo de Errores

### 8.1 Estrategia de Retry

| Integración | Max Retries | Backoff | Después del fallo final |
|---|---|---|---|
| RabbitMQ publish | 3 | Exponencial (1s, 2s, 4s) | Publicar en DLQ local + log error |
| HTTP POST /play-tts | 0 | N/A | Log error + continuar (fire-and-forget) |
| HTTP POST n8n webhook | 2 | Exponencial (1s, 2s) | Log error + publicar en chappie.errors |
| Edge-TTS | 2 | Exponencial (1s, 2s) | Log error + publicar en chappie.errors |
| OpenCode CLI | 0 | N/A | Publicar resultado FAILURE en chappie.agent.results |
| notify-send | 0 | N/A | Log error + continuar |

### 8.2 Dead Letter Queue (DLQ)

- Cada cola tiene su DLQ asociada (ej. `chappie.responses.dlq`).
- Los mensajes que fallan después de agotar reintentos se envían a la DLQ.
- No hay procesamiento automático de DLQ (requiere intervención manual).

### 8.3 Idempotencia

| Operación | Estrategia |
|---|---|
| Procesar respuesta | session_id + timestamp (ignorar duplicados) |
| Generar TTS | session_id + text_hash (cache de audio) |
| Ejecutar agente | session_id + agent_name (evitar ejecuciones duplicadas) |
| Enviar notificación | notification_id (evitar notificaciones duplicadas) |

---

## 9. Observabilidad

### 9.1 Logs

- **Nivel:** INFO por defecto, DEBUG para desarrollo.
- **Formato:** JSON estructurado con campos: `timestamp`, `level`, `logger`, `message`, `session_id`, `error`.
- **Destino:** stdout (capturado por systemd/journalctl).

### 9.2 Métricas (Futuro)

- Contador de mensajes procesados por cola.
- Contador de errores por tipo.
- Latencia de generación TTS.
- Latencia de ejecución de agentes.

### 9.3 Health Checks

- Endpoint HTTP `/health` (futuro, si se expone API).
- Verificación de conexión a RabbitMQ.
- Verificación de disponibilidad de chappie-daemon.

---

## 10. Seguridad

### 10.1 Whitelist de Comandos

- Todos los comandos de terminal deben validarse contra `commands-whitelist.yaml`.
- Comandos no permitidos → `CommandNotAllowedError`.
- No se permiten comandos con `sudo`.

### 10.2 Autenticación

- **RabbitMQ:** Usuario/contraseña en variables de entorno.
- **n8n Webhook:** Header `X-Webhook-Secret`.
- **chappie-daemon:** No requiere autenticación (localhost).

### 10.3 Secretos

- API keys en variables de entorno (no en código).
- No se almacenan secretos en archivos de configuración.

---

## 11. SLA/SLO

| Integración | SLA (Latencia) | SLO (Disponibilidad) |
|---|---|---|
| TTS (Edge-TTS) | < 3s | 99% |
| RabbitMQ | < 100ms | 99.9% |
| n8n Webhook | < 1s | 99% |
| OpenCode CLI | < 120s | 90% |
| notify-send | < 100ms | 99% |

---

## 12. Testing Strategy

### 12.1 Unit Tests

- **Cobertura mínima:** 85% por archivo testable.
- **Herramienta:** pytest + pytest-cov.
- **Exclusiones:** DTOs, configs, mappers.
- **Scope:** Dominio y aplicación (sin dependencias externas).

### 12.2 Integration Tests

- **Herramienta:** pytest + pytest-asyncio.
- **Scope:** Adaptadores de infraestructura con dependencias reales o mocks.
- **Ejemplos:**
  - Conexión a RabbitMQ (testcontainer).
  - Generación TTS con Edge-TTS.
  - Ejecución de comandos de terminal.

### 12.3 End-to-End Tests

- **Herramienta:** pytest + scripts de integración.
- **Scope:** Flujos completos con todos los componentes.
- **Ejemplos:**
  - Publicar mensaje en RabbitMQ → verificar TTS generado.
  - Publicar error → verificar webhook llamado a n8n.

---

## 13. Configuración y Despliegue

### 13.1 Variables de Entorno

```bash
# RabbitMQ
CHAPPIE_RABBITMQ_URL=amqp://guest:guest@localhost:5672/

# chappie-daemon
CHAPPIE_DAEMON_BASE_URL=http://localhost:8765

# n8n
CHAPPIE_N8N_BASE_URL=http://localhost:5678
CHAPPIE_N8N_WEBHOOK_SECRET=secret

# TTS
CHAPPIE_TTS_VOICE=es-AR-ElenaNeural
CHAPPIE_TTS_OUTPUT_PATH=/tmp/chappie_tts.mp3
CHAPPIE_TTS_TEXT_PATH=/tmp/chappie_tts_text.txt

# Whitelist
CHAPPIE_WHITELIST_PATH=./config/commands-whitelist.yaml

# Timeouts
CHAPPIE_AGENT_TIMEOUT=120
CHAPPIE_COMMAND_TIMEOUT=30
CHAPPIE_HTTP_TIMEOUT=10
```

### 13.2 Systemd Service (Futuro)

```ini
[Unit]
Description=Chappie Notification Daemon
After=network.target

[Service]
Type=simple
User=cris
WorkingDirectory=/path/to/chappie-notification
ExecStart=/path/to/uv run python -m chappie_notification
Restart=always
RestartSec=10

[Install]
WantedBy=default.target
```

### 13.3 Estructura de Archivos de Configuración

```
chappie-notification/
├── config/
│   └── commands-whitelist.yaml  # Copia desde chappie-config
└── .env                         # Variables de entorno (no commitear)
```

---

## 14. Criterios de Aceptación

### 14.1 Funcionales

- [ ] ExecutionConsumer procesa mensajes de `chappie.responses` correctamente.
- [ ] ErrorConsumer maneja errores y llama al webhook de n8n.
- [ ] TTSConsumer genera audio TTS y lo envía a chappie-daemon.
- [ ] NotificationConsumer muestra notificaciones con SwayNC.
- [ ] NotificationConsumer captura respuestas del usuario y publica en `chappie.agent.answers`.
- [ ] Comandos de terminal se validan contra whitelist.
- [ ] Agentes de OpenCode se ejecutan en background.
- [ ] Archivos de estado se escriben correctamente (`/tmp/chappie_tts_text.txt`).

### 14.2 No Funcionales

- [ ] Arquitectura hexagonal respetada (domain sin dependencias externas).
- [ ] Cobertura de tests >= 85%.
- [ ] Logs estructurados en JSON.
- [ ] Manejo de errores con retry y DLQ.
- [ ] Idempotencia en operaciones críticas.
- [ ] Configuración centralizada con pydantic-settings.

### 14.3 Integración

- [ ] Conexión exitosa a RabbitMQ.
- [ ] Consumo correcto de todas las colas definidas.
- [ ] Publicación correcta en colas de salida.
- [ ] Llamadas HTTP exitosas a chappie-daemon y n8n.
- [ ] Generación TTS exitosa con Edge-TTS.
- [ ] Ejecución de agentes y comandos funcional.

---

## 15. Decomposition Contract

### 15.1 Canonical Endpoint Paths

- `POST http://localhost:8765/play-tts` (chappie-daemon)
- `POST http://localhost:5678/webhook/chappie-error-handler` (n8n)

### 15.2 Canonical Queue Names

- `chappie.responses`
- `chappie.errors`
- `chappie.tts.requests`
- `chappie.agent.results`
- `chappie.agent.questions`
- `chappie.agent.answers`
- `chappie.notifications`

### 15.3 Canonical DTO/Schema Names

- `ChappieResponse`
- `AgentCall`
- `TerminalCommand`
- `NotificationRequest`
- `MemoryUpdate`
- `TTSRequest`
- `ErrorMessage`
- `AgentResult`
- `AgentQuestion`
- `AgentAnswer`
- `NotificationMessage`

### 15.4 Canonical DB Tables/Columns

N/A (no hay base de datos en este proyecto).

### 15.5 Allowed Task Order

1. Setup del proyecto (pyproject.toml, estructura de directorios).
2. Implementación de dominio (models, events, exceptions).
3. Implementación de aplicación (use cases, ports, DTOs).
4. Implementación de infraestructura (adapters, consumers, config).
5. Tests unitarios.
6. Tests de integración.
7. Configuración de despliegue (systemd service).

### 15.6 Forbidden Stale Terms

- No usar "chappie-n8n-workflows" como owner de ejecución de agentes.
- No usar "TTS Generator" como workflow de n8n.
- No asumir que chappie-notification hace volume ducking.

### 15.7 Archivos Autoritativos

- `projects/chappie-notification/docs/specs/master_spec.md` (este documento)
- `docs/architecture/integration-map.md` (contratos globales)
- `docs/specs/master_spec.md` (Master Spec global del workspace)

---

## 16. Decisiones Arquitectónicas

### 16.1 ¿Por qué Arquitectura Hexagonal?

- **Separación de responsabilidades:** Los consumers (infraestructura) no contienen lógica de negocio.
- **Testabilidad:** El dominio y la aplicación pueden probarse sin dependencias externas.
- **Flexibilidad:** Los adaptadores pueden cambiarse sin afectar la lógica de negocio (ej. cambiar Edge-TTS por Azure TTS).

### 16.2 ¿Por qué Python con asyncio?

- **Asincronía nativa:** Ideal para consumers de colas y llamadas HTTP concurrentes.
- **Ecosistema maduro:** aio-pika, httpx, edge-tts, pydantic.
- **Simplicidad:** Menos boilerplate que Java/Kotlin para este caso de uso.

### 16.3 ¿Por qué aio-pika en lugar de pika?

- **Asincronía:** pika es síncrono y bloquearía el event loop.
- **Performance:** aio-pika permite consumir múltiples colas concurrentemente.

### 16.4 ¿Por qué pydantic-settings?

- **Validación automática:** Tipado fuerte y validación de variables de entorno.
- **Documentación:** Genera documentación automática de configuración.
- **Integración:** Funciona bien con el ecosistema Python moderno.

---

## 17. Riesgos y Mitigaciones

| Riesgo | Impacto | Probabilidad | Mitigación |
|---|---|---|---|
| Edge-TTS no disponible | Alto | Baja | Retry + fallback a Azure TTS (futuro) |
| RabbitMQ caído | Alto | Baja | Reconexión automática + DLQ |
| Agente tarda más de 120s | Medio | Media | Timeout configurable + notificación de timeout |
| Comando no permitido | Medio | Media | Whitelist estricta + log de intentos |
| chappie-daemon no responde | Medio | Baja | Fire-and-forget + log de error |

---

## 18. Futuras Mejoras

- **Métricas Prometheus:** Exponer métricas de latencia y errores.
- **Health Check API:** Endpoint HTTP para monitoreo.
- **TTS Fallback:** Soporte para Azure TTS como fallback.
- **Cache de TTS:** Evitar regenerar audio para textos repetidos.
- **Rate Limiting:** Limitar llamadas a APIs externas.
- **Circuit Breaker:** Proteger contra fallos en cascada.

---

*Documento mantenido por: Planner*  
*Próxima revisión: Al completar initial-setup*
