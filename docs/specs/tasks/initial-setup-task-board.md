# Task Board — chappie-notification / initial-setup

**Spec:** `projects/chappie-notification/docs/specs/master_spec.md`  
**Shared Context:** `projects/chappie-notification/docs/specs/.working/initial-setup-sdd-context.md`  
**Decomposition Contract:** Master Spec §15  
**Created:** 2026-06-14  
**Agent:** task-decomposer  

---

## Board Status: `done`

_All tasks start in `todo`. Executor must claim one task at a time and update status._

---

## Task Order (from Decomposition Contract §15.5)

```
Setup  →  Domain  →  Application  →  Infrastructure  →  Unit Tests  →  Integration Tests  →  Deployment Config
```

Tasks within each phase are ordered by dependency. A task may only start when all its `dependencies` are `done`.

---

## Phase 1: Project Setup

---

### TASK-001 — Scaffold project structure and pyproject.toml

| Field | Value |
|---|---|
| **id** | `TASK-001` |
| **title** | Scaffold project structure and pyproject.toml |
| **agent** | executor |
| **spec_refs** | Master Spec §2.1, §5.3, §13.3; Decomposition Contract §15.5 item 1 |
| **goal** | Create the full directory tree and `pyproject.toml` with all dependencies declared. |
| **scope** |  |
| | - Create directory tree: `src/domain/models/`, `src/domain/events/`, `src/domain/exceptions/`, `src/domain/__init__.py` |
| | - `src/application/use_cases/`, `src/application/ports/`, `src/application/dto/`, `src/application/__init__.py` |
| | - `src/infrastructure/consumers/`, `src/infrastructure/adapters/`, `src/infrastructure/config/`, `src/infrastructure/mappers/`, `src/infrastructure/__init__.py` |
| | - `tests/unit/`, `tests/integration/`, `tests/e2e/`, `tests/__init__.py` |
| | - `config/` directory |
| | - Write `pyproject.toml` using `uv` / standard `[project]` format with Python 3.12+ requirement. |
| | - Declare runtime dependencies: `aio-pika`, `httpx`, `pydantic`, `pydantic-settings`, `pyyaml` |
| | - Declare dev dependencies: `pytest`, `pytest-asyncio`, `pytest-cov`, `ruff`, `mypy` |
| | - Write `__init__.py` in every package directory (empty). |
| **out_of_scope** | Functional code, `.env` file, `commands-whitelist.yaml`. |
| **inputs** | Master Spec §2.1 (directory tree), §5.3 (AppConfig field list for identifying deps), §13.3 (structure). |
| **implementation_notes** | Use `uv` as package manager per python-stack skill. Python minimum 3.12. All `__init__.py` files empty. |
| **edge_cases** | None. |
| **done_criteria** | |
| | - All directories exist with correct names. |
| | - `pyproject.toml` is valid TOML and lists all runtime + dev deps. |
| | - `uv sync` (or `pip install -e .`) completes without error. |
| **verification** | `ls src/domain/ src/application/ src/infrastructure/ tests/ config/` show all subdirectories. `python -c "import chappie_notification"` succeeds (after editable install). |
| **dependencies** | none |
| **handoff_context** | Executor must write `pyproject.toml` with all deps declared; TASK-002 can run concurrently or after. |
| **source_of_truth** | Master Spec §2.1 |
| **stale_terms_guard** | Avoid "pika" — use "aio-pika". No DTO-only directories in domain. |
| **status** | `done` |
| **executor_notes** |  |
| **verification_result** |  |
| **blocker** | `none` |

---

### TASK-002 — Create configuration files (commands-whitelist.yaml, .env.example)

| Field | Value |
|---|---|
| **id** | `TASK-002` |
| **title** | Create configuration files: commands-whitelist.yaml and .env.example |
| **agent** | executor |
| **spec_refs** | Master Spec §5.2 (WhitelistCommandValidatorAdapter), §13.1, §13.3; integration-map.md §4.3 |
| **goal** | Create `config/commands-whitelist.yaml` and `.env.example` with all documented environment variables. |
| **scope** | |
| | - Write `config/commands-whitelist.yaml` from integration-map.md §4.3 (allowed_commands + denied_commands patterns). |
| | - Write `.env.example` from Master Spec §13.1 (all `CHAPPIE_*` variables with placeholder values). |
| **out_of_scope** | Writing `.env` with real secrets. Loading whitelist in adapter (TASK-020). |
| **inputs** | Master Spec §13.1 (env vars), integration-map.md §4.3 (whitelist YAML). |
| **implementation_notes** | `.env.example` must include all 12 `CHAPPIE_*` variables exactly as listed in §13.1 with commented descriptions. `commands-whitelist.yaml` must be a direct copy of integration-map.md §4.3 structure. |
| **edge_cases** | None. |
| **done_criteria** | `config/commands-whitelist.yaml` exists with correct patterns. `.env.example` exists with all documented env vars. |
| **verification** | `cat config/commands-whitelist.yaml` matches integration-map.md §4.3. `grep CHAPPIE_ .env.example | wc -l` returns 11+. |
| **dependencies** | TASK-001 (needs `config/` directory) |
| **handoff_context** | These files are referenced but not loaded until TASK-013 (AppConfig) and TASK-020 (WhitelistValidatorAdapter). |
| **source_of_truth** | integration-map.md §4.3 |
| **stale_terms_guard** | None. |
| **status** | `done` |
| **executor_notes** |  |
| **verification_result** |  |
| **blocker** | `none` |

---

## Phase 2: Domain Implementation

---

### TASK-003 — Implement domain enums

| Field | Value |
|---|---|
| **id** | `TASK-003` |
| **title** | Implement domain enums |
| **agent** | executor |
| **spec_refs** | Master Spec §3.2 |
| **goal** | Create `src/domain/models/enums.py` with all five domain enums exactly as specified. |
| **scope** | |
| | - `TTSPriority`: `NORMAL = "normal"`, `HIGH = "high"` |
| | - `ExecutionStatus`: `SUCCESS = "success"`, `FAILURE = "failure"` |
| | - `ErrorType`: `AGENT_FAILURE`, `COMMAND_FAILURE`, `VALIDATION_ERROR` |
| | - `NotificationUrgency`: `LOW`, `NORMAL`, `CRITICAL` |
| | - `NotificationCategory`: `AGENT_COMPLETE`, `ERROR`, `INFO`, `QUESTION` |
| | - All inherit from `(str, Enum)`. |
| **out_of_scope** | Value objects, events, exceptions. |
| **inputs** | Master Spec §3.2 |
| **implementation_notes** | File: `src/domain/models/enums.py`. Use `(str, Enum)` base for JSON serialization compatibility. |
| **edge_cases** | None. Pure enums. |
| **done_criteria** | All five enum classes defined with exact members and values as in spec. |
| **verification** | `python -c "from chappie_notification.domain.models.enums import TTSPriority, ExecutionStatus, ErrorType, NotificationUrgency, NotificationCategory; print('OK')"` |
| **dependencies** | TASK-001 (directory structure) |
| **handoff_context** | Enums are imported by TASK-004 (value objects), TASK-008 (DTOs). |
| **source_of_truth** | Master Spec §3.2 |
| **stale_terms_guard** | None. |
| **status** | `done` |
| **executor_notes** |  |
| **verification_result** |  |
| **blocker** | `none` |

---

### TASK-004 — Implement domain value objects

| Field | Value |
|---|---|
| **id** | `TASK-004` |
| **title** | Implement domain value objects (dataclasses) |
| **agent** | executor |
| **spec_refs** | Master Spec §3.1; Decomposition Contract §15.3 |
| **goal** | Create `src/domain/models/value_objects.py` with all 11 canonical dataclasses. |
| **scope** | |
| | - `ChappieResponse` (frozen, with Optional fields for agent_call, terminal_command, notification, memory_update) |
| | - `AgentCall` (frozen) |
| | - `TerminalCommand` (frozen) |
| | - `NotificationRequest` (frozen, uses `NotificationUrgency`) |
| | - `MemoryUpdate` (frozen) |
| | - `TTSRequest` (frozen, uses `UUID`, `TTSPriority`) |
| | - `AgentResult` (frozen, uses `ExecutionStatus`) |
| | - `AgentQuestion` (frozen, uses `list[QuestionOption]`, `UUID`) |
| | - `QuestionOption` (frozen) |
| | - `AgentAnswer` (frozen) |
| | - `ErrorMessage` (frozen, uses `ErrorType`, `ErrorContext | None`) |
| | - `ErrorContext` (frozen, optional fields) |
| | - `NotificationMessage` (frozen, uses `NotificationUrgency`, `NotificationCategory`, `list[NotificationAction]`) |
| | - `NotificationAction` (frozen) |
| **out_of_scope** | Domain events, domain exceptions. |
| **inputs** | Master Spec §3.1 (exact field definitions per dataclass), §3.2 (enums from TASK-003). |
| **implementation_notes** | File: `src/domain/models/value_objects.py`. All classes `@dataclass(frozen=True)`. Use `from __future__ import annotations` for forward references. Import enums from `src.domain.models.enums`. No framework imports, no pydantic, no ORM. |
| **edge_cases** | `ChappieResponse` has 4 optional fields — ensure `None` defaults for `agent_call`, `terminal_command`, `notification`, `memory_update`. `ErrorContext` has 2 optional `str | None` fields. |
| **done_criteria** | All 14 dataclasses defined exactly matching spec field names, types, and defaults. |
| **verification** | `python -c "from chappie_notification.domain.models.value_objects import ChappieResponse, AgentCall, TerminalCommand, NotificationRequest, MemoryUpdate, TTSRequest, AgentResult, AgentQuestion, QuestionOption, AgentAnswer, ErrorMessage, ErrorContext, NotificationMessage, NotificationAction; print('OK')"` |
| **dependencies** | TASK-003 (enums) |
| **handoff_context** | Value objects are the core data types used by all downstream layers. |
| **source_of_truth** | Master Spec §3.1 |
| **stale_terms_guard** | Must include `NotificationRequest` and `MemoryUpdate` (F-001 resolved). |
| **status** | `done` |
| **executor_notes** |  |
| **verification_result** |  |
| **blocker** | `none` |

---

### TASK-005 — Implement domain events

| Field | Value |
|---|---|
| **id** | `TASK-005` |
| **title** | Implement domain events |
| **agent** | executor |
| **spec_refs** | Master Spec §3.3 |
| **goal** | Create `src/domain/events/domain_events.py` with all three domain events. |
| **scope** | |
| | - `AgentExecutionStarted` (frozen, fields: session_id, agent, timestamp) |
| | - `AgentExecutionCompleted` (frozen, fields: session_id, agent, status, result, timestamp) |
| | - `TTSGenerationRequested` (frozen, fields: session_id, text, priority, timestamp) |
| **out_of_scope** | Event bus, event publishing infrastructure. |
| **inputs** | Master Spec §3.3 |
| **implementation_notes** | File: `src/domain/events/domain_events.py`. All `@dataclass(frozen=True)`. Use `ExecutionStatus` from TASK-003, `TTSPriority` from TASK-003. No infrastructure imports. |
| **edge_cases** | None. Pure data containers. |
| **done_criteria** | Three event classes defined exactly matching spec fields. |
| **verification** | `python -c "from chappie_notification.domain.events.domain_events import AgentExecutionStarted, AgentExecutionCompleted, TTSGenerationRequested; print('OK')"` |
| **dependencies** | TASK-003 (enums) |
| **handoff_context** | Events are referenced by use cases (TASK-012, TASK-015) when orchestrating agent execution. |
| **source_of_truth** | Master Spec §3.3 |
| **stale_terms_guard** | None. |
| **status** | `done` |
| **executor_notes** |  |
| **verification_result** |  |
| **blocker** | `none` |

---

### TASK-006 — Implement domain exceptions

| Field | Value |
|---|---|
| **id** | `TASK-006` |
| **title** | Implement domain exceptions |
| **agent** | executor |
| **spec_refs** | Master Spec §3.4 |
| **goal** | Create `src/domain/exceptions/domain_exceptions.py` with all four domain exceptions. |
| **scope** | |
| | - `CommandNotAllowedError(Exception)` — comando no permitido por whitelist |
| | - `AgentExecutionError(Exception)` — error durante ejecución de agente |
| | - `TTSGenerationError(Exception)` — error durante generación TTS |
| | - `NotificationError(Exception)` — error al crear/enviar notificación |
| **out_of_scope** | Exception handling in consumers; that belongs in infrastructure. |
| **inputs** | Master Spec §3.4 |
| **implementation_notes** | File: `src/domain/exceptions/domain_exceptions.py`. All inherit directly from `Exception`. Include docstrings matching spec descriptions. |
| **edge_cases** | None. |
| **done_criteria** | Four exception classes defined with correct inheritance and docstrings. |
| **verification** | `python -c "from chappie_notification.domain.exceptions.domain_exceptions import CommandNotAllowedError, AgentExecutionError, TTSGenerationError, NotificationError; print('OK')"` |
| **dependencies** | TASK-001 (directory structure) |
| **handoff_context** | Exceptions are raised by use cases (TASK-015, TASK-016) and caught by consumers (TASK-026, TASK-027, TASK-028). |
| **source_of_truth** | Master Spec §3.4 |
| **stale_terms_guard** | None. |
| **status** | `done` |
| **executor_notes** |  |
| **verification_result** |  |
| **blocker** | `none` |

---

## Phase 3: Application Implementation

---

### TASK-007 — Implement application DTOs (Command/Query/Result objects)

| Field | Value |
|---|---|
| **id** | `TASK-007` |
| **title** | Implement application DTOs |
| **agent** | executor |
| **spec_refs** | Master Spec §4.3; Decomposition Contract §15.3 |
| **goal** | Create `src/application/dto/results.py` with all six result DTOs and `src/application/dto/commands.py` if needed. |
| **scope** | |
| | - `ProcessResponseResult` (frozen, fields: success, tts_requested, agent_started, command_started, error=None) |
| | - `HandleErrorResult` (frozen, fields: success, n8n_notified, error=None) |
| | - `GenerateTTSResult` (frozen, fields: success, audio_path=None, error=None) |
| | - `ShowNotificationResult` (frozen, fields: success, notification_id=None, user_answer=None, error=None) |
| | - `ExecuteAgentResult` (frozen, fields: success, status=ExecutionStatus, result, error=None) |
| | - `CommandExecutionResult` (frozen, fields: success, stdout, stderr, exit_code) |
| | - `AgentExecutionResult` (frozen, fields: success, stdout, stderr, exit_code) |
| **out_of_scope** | Use case implementations — DTOs are just data buckets. |
| **inputs** | Master Spec §4.3, §3.2 (ExecutionStatus enum from TASK-003). |
| **implementation_notes** | File: `src/application/dto/results.py`. All `@dataclass(frozen=True)`. `ExecuteAgentResult.status` uses `ExecutionStatus` enum. Reference `from __future__ import annotations`. No domain logic. |
| **edge_cases** | `ProcessResponseResult` has 4 boolean flags — ensure all default to `False` except `success=True` (or `False` as per actual execution). Default `error=None` for optional error fields. |
| **done_criteria** | All 7 result classes defined with exact fields and types as in spec. |
| **verification** | `python -c "from chappie_notification.application.dto.results import ProcessResponseResult, HandleErrorResult, GenerateTTSResult, ShowNotificationResult, ExecuteAgentResult, CommandExecutionResult, AgentExecutionResult; print('OK')"` |
| **dependencies** | TASK-003 (enums), TASK-001 (directory structure) |
| **handoff_context** | DTOs are returned by use case implementations and consumed by consumers. |
| **source_of_truth** | Master Spec §4.3 |
| **stale_terms_guard** | None. |
| **status** | `done` |
| **executor_notes** |  |
| **verification_result** |  |
| **blocker** | `none` |

---

### TASK-008 — Implement output ports (Protocol interfaces)

| Field | Value |
|---|---|
| **id** | `TASK-008` |
| **title** | Implement output ports (Protocol interfaces) |
| **agent** | executor |
| **spec_refs** | Master Spec §4.2 |
| **goal** | Create `src/application/ports/` with all 7 output port Protocols. |
| **scope** | |
| | - `RabbitMQPublisherPort` (Protocol): `publish(queue, message, headers=None) -> None` |
| | - `TTSSynthesizerPort` (Protocol): `synthesize(text, voice, output_path) -> str` |
| | - `AgentExecutorPort` (Protocol): `execute(agent, prompt, timeout=120) -> AgentExecutionResult` |
| | - `CommandExecutorPort` (Protocol): `execute(command, timeout=30) -> CommandExecutionResult` |
| | - `CommandValidatorPort` (Protocol): `is_allowed(command) -> bool` |
| | - `NotificationSenderPort` (Protocol): `send(title, message, urgency, actions) -> str | None` AND `wait_for_action(notification_id, timeout_seconds) -> str | None` |
| | - `HTTPClientPort` (Protocol): `post(url, json, headers=None, timeout=10) -> dict` |
| | - `FileWriterPort` (Protocol): `write(path, content) -> None` |
| **out_of_scope** | Use case implementations, adapter implementations. |
| **inputs** | Master Spec §4.2 (each port signature), §4.3 (result types from TASK-007). |
| **implementation_notes** | File: `src/application/ports/` with individual files (`messaging_port.py`, `tts_port.py`, `agent_port.py`, `command_port.py`, `notification_port.py`, `http_port.py`, `file_writer_port.py`) or single file. Use `typing.Protocol` with `@runtime_checkable`. All methods are `async` where spec indicates. `NotificationSenderPort` has TWO methods (`send` and `wait_for_action`) — Decision locked #13. |
| **edge_cases** | `NotificationSenderPort.wait_for_action` — distinct from `send`, reflects D-Bus async model. `RabbitMQPublisherPort.headers` is optional. |
| **done_criteria** | All 7 Protocol classes defined with exact method signatures matching spec. |
| **verification** | `grep -r "class.*Protocol" src/application/ports/` returns 7 matches. Python import succeeds. |
| **dependencies** | TASK-007 (DTOs for return types) |
| **handoff_context** | These ports are implemented by TASK-017 through TASK-022 (adapters) and injected into TASK-010 through TASK-015 (use cases). |
| **source_of_truth** | Master Spec §4.2 |
| **stale_terms_guard** | `NotificationSenderPort` must include `wait_for_action()` method (Decision locked #13). No "pika". |
| **status** | `done` |
| **executor_notes** |  |
| **verification_result** |  |
| **blocker** | `none` |

---

### TASK-009 — Implement ProcessResponseUseCase

| Field | Value |
|---|---|
| **id** | `TASK-009` |
| **title** | Implement ProcessResponseUseCase |
| **agent** | executor |
| **spec_refs** | Master Spec §4.1 (ProcessResponseUseCase), §7.1 (happy path flow) |
| **goal** | Implement `src/application/use_cases/process_response.py` with `ProcessResponseUseCase` that orchestrates response processing. |
| **scope** | |
| | - Accept `ChappieResponse` and return `ProcessResponseResult`. |
| | - If `agent_call.enabled`: delegate to `ExecuteAgentUseCase` (TASK-015) via dependency injection, mark `agent_started=True`. |
| | - If `terminal_command.enabled`: delegate to `ExecuteCommandUseCase` (TASK-014) via DI, mark `command_started=True`. |
| | - If `voice_response` is non-empty: publish `TTSRequest` to RabbitMQ via `RabbitMQPublisherPort`, mark `tts_requested=True`. |
| | - Emit domain events as appropriate (AgentExecutionStarted). |
| **out_of_scope** | Actually executing agents/commands — delegates to other use cases. Publishing to RabbitMQ — delegates to port. |
| **inputs** | Master Spec §4.1 ProcessResponseUseCase, §7.1; TASK-004 (ChappieResponse), TASK-007 (ProcessResponseResult), TASK-008 (RabbitMQPublisherPort). |
| **implementation_notes** | Constructor injection: `__init__(self, rabbitmq_publisher: RabbitMQPublisherPort, execute_agent_uc: ExecuteAgentUseCase, execute_command_uc: ExecuteCommandUseCase)`. Methods are `async`. Orchstrates but does not own business logic (delegates to domain). |
| **edge_cases** | All four optional fields (`agent_call`, `terminal_command`, `voice_response`, `notification`) can be `None`/disabled simultaneously → still returns success. |
| **done_criteria** | Class exists, accepts ChappieResponse, delegates to correct sub-use-cases, publishes to correct queues, returns ProcessResponseResult. |
| **verification** | Unit test TASK-029 verifies delegation logic. Executor should write class implementing the Protocol signature from spec. |
| **dependencies** | TASK-004 (ChappieResponse), TASK-007 (ProcessResponseResult), TASK-008 (ports), TASK-014 (ExecuteCommandUseCase — weak), TASK-015 (ExecuteAgentUseCase — weak) |
| **handoff_context** | Called by ExecutionConsumer (TASK-026). Depends on TASK-014 and TASK-015 at runtime (constructor injection). |
| **source_of_truth** | Master Spec §4.1 ProcessResponseUseCase |
| **stale_terms_guard** | ExecutionConsumer is NOT a producer of chappie.notifications (F-004). NotificationRequest is handled by a separate flow, not in this use case. |
| **status** | `done` |
| **executor_notes** |  |
| **verification_result** |  |
| **blocker** | `none` |

---

### TASK-010 — Implement HandleErrorUseCase

| Field | Value |
|---|---|
| **id** | `TASK-010` |
| **title** | Implement HandleErrorUseCase |
| **agent** | executor |
| **spec_refs** | Master Spec §4.1 (HandleErrorUseCase), §7.2 (error flow) |
| **goal** | Implement `src/application/use_cases/handle_error.py` with `HandleErrorUseCase`. |
| **scope** | |
| | - Accept `ErrorMessage` and return `HandleErrorResult`. |
| | - Call n8n webhook via `HTTPClientPort.post()` with error payload. |
| | - Do NOT reproduce voice (no TTS call in error path). |
| | - Return `n8n_notified=True` on success. |
| **out_of_scope** | TTS generation (error path goes to n8n for regeneration). Direct HTTP implementation (delegates to HTTPClientPort). |
| **inputs** | Master Spec §4.1 HandleErrorUseCase, §6.3 (n8n webhook contract), TASK-004 (ErrorMessage), TASK-007 (HandleErrorResult), TASK-008 (HTTPClientPort). |
| **implementation_notes** | Constructor injection: `__init__(self, http_client: HTTPClientPort, config: AppConfig)`. Uses `config.n8n_base_url`, `config.n8n_webhook_secret`. Endpoint: `{n8n_base_url}/webhook/chappie-error-handler`. Header: `X-Webhook-Secret`. |
| **edge_cases** | n8n webhook unreachable → retry (2 attempts per Master Spec §8.1). After max retries → log error + return `success=False`. |
| **done_criteria** | Class accepts ErrorMessage, calls n8n webhook with correct payload, returns HandleErrorResult with n8n_notified flag. |
| **verification** | Verify signature matches Protocol from spec. Unit test TASK-029. |
| **dependencies** | TASK-004 (ErrorMessage), TASK-007 (HandleErrorResult), TASK-008 (HTTPClientPort), TASK-013 (AppConfig) |
| **handoff_context** | Called by ErrorConsumer (TASK-027). |
| **source_of_truth** | Master Spec §4.1 HandleErrorUseCase |
| **stale_terms_guard** | Error path does NOT reproduce voz original. Error path does NOT call TTS directly — n8n publishes to chappie.tts.requests. |
| **status** | `done` |
| **executor_notes** |  |
| **verification_result** |  |
| **blocker** | `none` |

---

### TASK-011 — Implement GenerateTTSUseCase

| Field | Value |
|---|---|
| **id** | `TASK-011` |
| **title** | Implement GenerateTTSUseCase |
| **agent** | executor |
| **spec_refs** | Master Spec §4.1 (GenerateTTSUseCase), §7.1 steps 4-5 |
| **goal** | Implement `src/application/use_cases/generate_tts.py` with `GenerateTTSUseCase`. |
| **scope** | |
| | - Accept `TTSRequest` and return `GenerateTTSResult`. |
| | - Call `TTSSynthesizerPort.synthesize()` to generate audio → save to `/tmp/chappie_tts.mp3`. |
| | - Call `FileWriterPort.write()` to write text to `/tmp/chappie_tts_text.txt`. |
| | - Call `HTTPClientPort.post()` to chappie-daemon `POST /play-tts` (fire-and-forget). |
| **out_of_scope** | Edge-TTS implementation (delegates to port). chappie-daemon implementation. |
| **inputs** | Master Spec §4.1 GenerateTTSUseCase, §6.3 (POST /play-tts contract), TASK-004 (TTSRequest), TASK-007 (GenerateTTSResult), TASK-008 (TTSSynthesizerPort, FileWriterPort, HTTPClientPort). |
| **implementation_notes** | Constructor injection: `__init__(self, tts_synthesizer: TTSSynthesizerPort, file_writer: FileWriterPort, http_client: HTTPClientPort, config: AppConfig)`. Uses `config.tts_voice`, `config.tts_output_path`, `config.tts_text_path`, `config.daemon_base_url`. `/play-tts` is fire-and-forget: no retry, just log error. |
| **edge_cases** | TTS synthesis fails → retry 2x (Master Spec §8.1). After max retries → return `success=False` with error. Text file write fails → log error but continue. |
| **done_criteria** | Class accepts TTSRequest, generates audio, writes text file, calls daemon, returns GenerateTTSResult. |
| **verification** | Verify signature. Unit test TASK-029. |
| **dependencies** | TASK-004 (TTSRequest), TASK-007 (GenerateTTSResult), TASK-008 (TTSSynthesizerPort, FileWriterPort, HTTPClientPort), TASK-013 (AppConfig) |
| **handoff_context** | Called by TTSConsumer (TASK-028). |
| **source_of_truth** | Master Spec §4.1 GenerateTTSUseCase |
| **stale_terms_guard** | Does NOT write chappie_tts_state.txt (chappie-daemon's responsibility). Does NOT do volume ducking. |
| **status** | `done` |
| **executor_notes** |  |
| **verification_result** |  |
| **blocker** | `none` |

---

### TASK-012 — Implement ShowNotificationUseCase

| Field | Value |
|---|---|
| **id** | `TASK-012` |
| **title** | Implement ShowNotificationUseCase |
| **agent** | executor |
| **spec_refs** | Master Spec §4.1 (ShowNotificationUseCase), §7.3 (notification flow), Decision locked #13 |
| **goal** | Implement `src/application/use_cases/show_notification.py` with `ShowNotificationUseCase`. |
| **scope** | |
| | - Accept `NotificationMessage` and return `ShowNotificationResult`. |
| | - Call `NotificationSenderPort.send()` to show notification via SwayNC (returns notification_id immediately). |
| | - If `actions` list is non-empty and category is `QUESTION`: call `NotificationSenderPort.wait_for_action()` with timeout 600s. |
| | - If generic notification with actions: timeout 120s. |
| | - If no actions: fire-and-forget (return immediately). |
| | - Publish answer to `chappie.agent.answers` via `RabbitMQPublisherPort` if user responded. |
| **out_of_scope** | SwayNC/notify-send implementation (delegates to port). D-Bus signal capture (in adapter TASK-021). |
| **inputs** | Master Spec §4.1 ShowNotificationUseCase, §7.3; TASK-004 (NotificationMessage, AgentAnswer), TASK-007 (ShowNotificationResult), TASK-008 (NotificationSenderPort, RabbitMQPublisherPort). |
| **implementation_notes** | Constructor injection: `__init__(self, notification_sender: NotificationSenderPort, rabbitmq_publisher: RabbitMQPublisherPort)`. Timeout per category: 600s for QUESTION, 120s otherwise. Default answer on timeout: "ignore". Must NOT block event loop — uses `asyncio.Event` internally via `wait_for_action`. |
| **edge_cases** | Timeout expires → return `user_answer="ignore"`. No actions → `notification_id=None`, skip wait_for_action. |
| **done_criteria** | Class shows notification, waits for response with correct timeout, publishes answer to queue, returns ShowNotificationResult. |
| **verification** | Verify async pattern. Unit test TASK-029. |
| **dependencies** | TASK-004 (NotificationMessage, AgentAnswer), TASK-007 (ShowNotificationResult), TASK-008 (NotificationSenderPort, RabbitMQPublisherPort) |
| **handoff_context** | Called by NotificationConsumer (TASK-029 — actually TASK-025 notification consumer). |
| **source_of_truth** | Master Spec §4.1 ShowNotificationUseCase |
| **stale_terms_guard** | notify-send retorna inmediatamente (no bloquea event loop). Espera via D-Bus signals, no polling. Default answer "ignore" on timeout. |
| **status** | `done` |
| **executor_notes** |  |
| **verification_result** |  |
| **blocker** | `none` |

---

### TASK-013 — Implement ExecuteAgentUseCase

| Field | Value |
|---|---|
| **id** | `TASK-013` |
| **title** | Implement ExecuteAgentUseCase |
| **agent** | executor |
| **spec_refs** | Master Spec §4.1 (ExecuteAgentUseCase), §6.4 (OpenCode CLI) |
| **goal** | Implement `src/application/use_cases/execute_agent.py` with `ExecuteAgentUseCase`. |
| **scope** | |
| | - Accept `AgentCall` + `session_id: UUID` and return `ExecuteAgentResult`. |
| | - Call `AgentExecutorPort.execute(agent, prompt, timeout=config.agent_timeout)`. |
| | - Map `AgentExecutionResult` to `ExecuteAgentResult`. |
| | - Publish result to `chappie.agent.results` via `RabbitMQPublisherPort`. |
| | - On failure → publish `ErrorMessage` to `chappie.errors`. |
| **out_of_scope** | OpenCode CLI execution (delegates to port). |
| **inputs** | Master Spec §4.1 ExecuteAgentUseCase; TASK-004 (AgentCall, AgentResult, ErrorMessage), TASK-007 (ExecuteAgentResult, AgentExecutionResult), TASK-008 (AgentExecutorPort, RabbitMQPublisherPort), TASK-003 (ExecutionStatus, ErrorType). |
| **implementation_notes** | Constructor injection: `__init__(self, agent_executor: AgentExecutorPort, rabbitmq_publisher: RabbitMQPublisherPort, config: AppConfig)`. Default timeout from `config.agent_timeout` (120s). |
| **edge_cases** | Agent timeout → treat as FAILURE, publish error. Agent not found → immediate FAILURE. |
| **done_criteria** | Class executes agent, publishes result/error to correct queues, returns ExecuteAgentResult. |
| **verification** | Unit test TASK-029. |
| **dependencies** | TASK-004 (AgentCall, AgentResult, ErrorMessage), TASK-007 (ExecuteAgentResult, AgentExecutionResult), TASK-008 (AgentExecutorPort, RabbitMQPublisherPort), TASK-013 (AppConfig) |
| **handoff_context** | Called by ProcessResponseUseCase (TASK-009) when agent_call.enabled=True. |
| **source_of_truth** | Master Spec §4.1 ExecuteAgentUseCase |
| **stale_terms_guard** | No retry on agent execution failure — publish result FAILURE and continue. |
| **status** | `done` |
| **executor_notes** |  |
| **verification_result** |  |
| **blocker** | `none` |

---

### TASK-014 — Implement ExecuteCommandUseCase

| Field | Value |
|---|---|
| **id** | `TASK-014` |
| **title** | Implement ExecuteCommandUseCase |
| **agent** | executor |
| **spec_refs** | Master Spec §4.1 (ExecuteCommandUseCase), §10.1 (whitelist) |
| **goal** | Implement `src/application/use_cases/execute_command.py` with `ExecuteCommandUseCase`. |
| **scope** | |
| | - Accept `TerminalCommand` + `session_id: UUID` and return `ExecuteAgentResult`. |
| | - Call `CommandValidatorPort.is_allowed(command)` — raise `CommandNotAllowedError` if not allowed. |
| | - Call `CommandExecutorPort.execute(command, timeout=config.command_timeout)`. |
| | - Map `CommandExecutionResult` to `ExecuteAgentResult`. |
| | - Publish result to `chappie.agent.results`. |
| | - On failure → publish `ErrorMessage` to `chappie.errors`. |
| **out_of_scope** | Whitelist loading (delegates to port). Subprocess execution (delegates to port). |
| **inputs** | Master Spec §4.1 ExecuteCommandUseCase; TASK-004 (TerminalCommand, ErrorMessage, ErrorContext), TASK-007 (ExecuteAgentResult, CommandExecutionResult), TASK-008 (CommandExecutorPort, CommandValidatorPort, RabbitMQPublisherPort), TASK-006 (CommandNotAllowedError). |
| **implementation_notes** | Constructor injection: `__init__(self, command_executor: CommandExecutorPort, command_validator: CommandValidatorPort, rabbitmq_publisher: RabbitMQPublisherPort, config: AppConfig)`. Must validate BEFORE executing. Default timeout from `config.command_timeout` (30s). |
| **edge_cases** | Command not in whitelist → raise `CommandNotAllowedError`. Command with `sudo` → deny (Master Spec §10.1). |
| **done_criteria** | Class validates command, executes if allowed, publishes result/error to correct queues. |
| **verification** | Unit test TASK-029. |
| **dependencies** | TASK-004 (TerminalCommand, ErrorMessage), TASK-007 (ExecuteAgentResult, CommandExecutionResult), TASK-008 (CommandExecutorPort, CommandValidatorPort, RabbitMQPublisherPort), TASK-006 (CommandNotAllowedError), TASK-013 (AppConfig) |
| **handoff_context** | Called by ProcessResponseUseCase (TASK-009) when terminal_command.enabled=True. |
| **source_of_truth** | Master Spec §4.1 ExecuteCommandUseCase |
| **stale_terms_guard** | Commands with `sudo` are denied. Whitelist is authoritative. |
| **status** | `done` |
| **executor_notes** |  |
| **verification_result** |  |
| **blocker** | `none` |

---

## Phase 4: Infrastructure — Configuration

---

### TASK-015 — Implement AppConfig (pydantic-settings)

| Field | Value |
|---|---|
| **id** | `TASK-015` |
| **title** | Implement AppConfig with pydantic-settings |
| **agent** | executor |
| **spec_refs** | Master Spec §5.3, §13.1 |
| **goal** | Create `src/infrastructure/config/app_config.py` with `AppConfig(BaseSettings)`. |
| **scope** | |
| | - Implement exactly as spec §5.3: `rabbitmq_url`, `daemon_base_url`, `n8n_base_url`, `n8n_webhook_secret`, `tts_voice`, `tts_output_path`, `tts_text_path`, `whitelist_path`, `agent_timeout`, `command_timeout`, `http_timeout`. |
| | - Use `SettingsConfigDict(env_prefix="CHAPPIE_")`. |
| | - Provide defaults exactly as spec. |
| **out_of_scope** | Wiring/injection logic (TASK-016). |
| **inputs** | Master Spec §5.3, §13.1 |
| **implementation_notes** | Use `pydantic_settings.BaseSettings`. All fields have default values matching §5.3. `model_config = SettingsConfigDict(env_prefix="CHAPPIE_", env_file=".env", env_file_encoding="utf-8")`. |
| **edge_cases** | Missing `.env` file → defaults should work for local dev. |
| **done_criteria** | `AppConfig` class loads from env vars with `CHAPPIE_` prefix. All 12 fields present with correct types and defaults. |
| **verification** | `python -c "from chappie_notification.infrastructure.config.app_config import AppConfig; c = AppConfig(); print(c.rabbitmq_url)"` prints default AMQP URL. |
| **dependencies** | TASK-001 (directory structure) |
| **handoff_context** | AppConfig is injected into all use cases, adapters, and consumers. |
| **source_of_truth** | Master Spec §5.3 |
| **stale_terms_guard** | None. |
| **status** | `done` |
| **executor_notes** |  |
| **verification_result** |  |
| **blocker** | `none` |

---

### TASK-016 — Implement dependency injection wiring

| Field | Value |
|---|---|
| **id** | `TASK-016` |
| **title** | Implement dependency injection wiring (container) |
| **agent** | executor |
| **spec_refs** | Master Spec §5 (infrastructure wiring), hexagonal-architecture skill |
| **goal** | Create `src/infrastructure/config/container.py` with a simple DI container that wires all ports to adapters and injects into use cases and consumers. |
| **scope** | |
| | - Declare a `Container` class (or factory functions) that instantiates: |
| |   - `AppConfig` |
| |   - All 7 driven adapters (TASK-017 through TASK-022) |
| |   - All 5 use cases (TASK-009 through TASK-014) |
| |   - All 4 consumers (TASK-023 through TASK-025) |
| | - Constructor injection everywhere. |
| **out_of_scope** | Running the application (main.py TASK-026). |
| **inputs** | Master Spec §5.1, §5.2; all adapter and consumer tasks. |
| **implementation_notes** | Keep it simple — manual wiring is acceptable for Python. A `create_container()` async factory that returns all wired consumers. Each consumer receives its use case via constructor. Each use case receives its ports via constructor. Each port is implemented by an adapter. |
| **edge_cases** | Container must handle async initialization (e.g., RabbitMQ connection in TASK-017). |
| **done_criteria** | `Container` class provides fully wired instances. `container.execution_consumer` is ready to consume. |
| **verification** | Integration test verifies wiring (TASK-033). Executor can test: `container = await create_container(); assert container.execution_consumer is not None`. |
| **dependencies** | TASK-015 (AppConfig), TASK-017–TASK-022 (adapters), TASK-009–TASK-014 (use cases), TASK-023–TASK-025 (consumers) |
| **handoff_context** | Used by main.py (TASK-026) to bootstrap the application. |
| **source_of_truth** | hexagonal-architecture skill (DI section), Master Spec §5 |
| **stale_terms_guard** | No global state, no singletons, no service locator anti-pattern. |
| **status** | `done` |
| **executor_notes** |  |
| **verification_result** |  |
| **blocker** | `none` |

---

## Phase 5: Infrastructure — Driven Adapters

---

### TASK-017 — Implement RabbitMQPublisherAdapter

| Field | Value |
|---|---|
| **id** | `TASK-017` |
| **title** | Implement RabbitMQPublisherAdapter (aio-pika) |
| **agent** | executor |
| **spec_refs** | Master Spec §5.2 (RabbitMQPublisherAdapter), §4.2 (RabbitMQPublisherPort), §8.1 (retry strategy) |
| **goal** | Create `src/infrastructure/adapters/rabbitmq_publisher_adapter.py` implementing `RabbitMQPublisherPort`. |
| **scope** | |
| | - Constructor: `__init__(self, connection_url: str)`. |
| | - `async publish(self, queue: str, message: dict, headers: dict | None = None) -> None`. |
| | - Use `aio-pika` to connect, declare channel, declare queue (durable), publish message (persistent, delivery_mode=2). |
| | - Retry: 3 attempts with exponential backoff (1s, 2s, 4s). |
| | - After max retries: log error (no DLQ publishing from publisher itself). |
| **out_of_scope** | Consumer logic (separate adapter in consumers). DLQ management (config in RabbitMQ infrastructure). |
| **inputs** | Master Spec §5.2 RabbitMQPublisherAdapter, §8.1; TASK-008 (RabbitMQPublisherPort), TASK-015 (AppConfig). |
| **implementation_notes** | Use `aio_pika.connect_robust` for auto-reconnect. Queue declare with `durable=True`. Message publish with `DeliveryMode.PERSISTENT`. JSON serialize `message` dict. Refer to rabbitmq-standard skill for conventions. |
| **edge_cases** | Connection lost mid-publish → aio-pika `connect_robust` handles reconnect. Queue doesn't exist yet → declare on publish. |
| **done_criteria** | Class implements `RabbitMQPublisherPort`, publishes JSON to named queue with retry. |
| **verification** | Integration test TASK-033 with RabbitMQ testcontainer or mock. |
| **dependencies** | TASK-008 (RabbitMQPublisherPort), TASK-015 (AppConfig for URL) |
| **handoff_context** | Used by ProcessResponseUseCase, HandleErrorUseCase, ShowNotificationUseCase, ExecuteAgentUseCase, ExecuteCommandUseCase. |
| **source_of_truth** | Master Spec §5.2 |
| **stale_terms_guard** | Use `aio-pika`, not `pika`. Queue names must match Decomposition Contract §15.2 exactly. |
| **status** | `done` |
| **executor_notes** |  |
| **verification_result** |  |
| **blocker** | `none` |

---

### TASK-018 — Implement EdgeTTSSynthesizerAdapter

| Field | Value |
|---|---|
| **id** | `TASK-018` |
| **title** | Implement EdgeTTSSynthesizerAdapter |
| **agent** | executor |
| **spec_refs** | Master Spec §5.2 (EdgeTTSSynthesizerAdapter), §4.2 (TTSSynthesizerPort), §8.1 |
| **goal** | Create `src/infrastructure/adapters/edge_tts_adapter.py` implementing `TTSSynthesizerPort`. |
| **scope** | |
| | - Constructor: `__init__(self, voice: str = "es-AR-ElenaNeural")`. |
| | - `async synthesize(self, text: str, voice: str, output_path: str) -> str`. |
| | - Use `edge-tts` CLI or Python library to generate MP3 at `output_path`. |
| | - Retry: 2 attempts with exponential backoff (1s, 2s). |
| | - On failure → raise/log `TTSGenerationError`. |
| **out_of_scope** | Playing audio, writing text file — handled by GenerateTTSUseCase. |
| **inputs** | Master Spec §5.2 EdgeTTSSynthesizerAdapter, §8.1; TASK-008 (TTSSynthesizerPort), TASK-006 (TTSGenerationError). |
| **implementation_notes** | Use `edge_tts.Communicate` async API. Returns the `output_path` on success. Voice defaults from `config.tts_voice`. |
| **edge_cases** | Edge-TTS service unreachable → retry 2x, then raise TTSGenerationError. Empty text → skip generation. |
| **done_criteria** | Class synthesizes text to MP3 file at given path, implements TTSSynthesizerPort. |
| **verification** | Integration test TASK-033 verifies actual TTS generation. |
| **dependencies** | TASK-008 (TTSSynthesizerPort), TASK-006 (TTSGenerationError) |
| **handoff_context** | Used by GenerateTTSUseCase (TASK-011). |
| **source_of_truth** | Master Spec §5.2 |
| **stale_terms_guard** | Voice default: "es-AR-ElenaNeural". |
| **status** | `done` |
| **executor_notes** |  |
| **verification_result** |  |
| **blocker** | `none` |

---

### TASK-019 — Implement OpenCodeAgentExecutorAdapter

| Field | Value |
|---|---|
| **id** | `TASK-019` |
| **title** | Implement OpenCodeAgentExecutorAdapter |
| **agent** | executor |
| **spec_refs** | Master Spec §5.2 (OpenCodeAgentExecutorAdapter), §4.2 (AgentExecutorPort), §6.4 |
| **goal** | Create `src/infrastructure/adapters/opencode_agent_adapter.py` implementing `AgentExecutorPort`. |
| **scope** | |
| | - Constructor: `__init__(self, timeout: int = 120)`. |
| | - `async execute(self, agent: str, prompt: str, timeout: int = 120) -> AgentExecutionResult`. |
| | - Execute: `opencode run --agent <agent> "<prompt>"` via `asyncio.create_subprocess_exec`. |
| | - Capture stdout, stderr, exit_code. |
| | - Timeout via `asyncio.wait_for`. |
| **out_of_scope** | Retry logic (handled by use case / RabbitMQ DLQ). |
| **inputs** | Master Spec §5.2 OpenCodeAgentExecutorAdapter, §6.4; TASK-008 (AgentExecutorPort), TASK-007 (AgentExecutionResult). |
| **implementation_notes** | Use `asyncio.create_subprocess_exec("opencode", "run", "--agent", agent, prompt, stdout=PIPE, stderr=PIPE)`. Wrap with `asyncio.wait_for(process.communicate(), timeout=timeout)`. |
| **edge_cases** | Timeout → kill process, return `AgentExecutionResult(success=False, stderr="timeout", exit_code=-1)`. Agent binary not found → immediate failure. Prompt contains quotes → handle escaping. |
| **done_criteria** | Class executes opencode CLI, captures output, implements AgentExecutorPort. |
| **verification** | Integration test TASK-033 (may need opencode CLI available or mock). |
| **dependencies** | TASK-008 (AgentExecutorPort), TASK-007 (AgentExecutionResult) |
| **handoff_context** | Used by ExecuteAgentUseCase (TASK-013). |
| **source_of_truth** | Master Spec §5.2 |
| **stale_terms_guard** | Command: exactly `opencode run --agent <agent> "<prompt>"`. |
| **status** | `done` |
| **executor_notes** |  |
| **verification_result** |  |
| **blocker** | `none` |

---

### TASK-020 — Implement SubprocessCommandExecutorAdapter

| Field | Value |
|---|---|
| **id** | `TASK-020` |
| **title** | Implement SubprocessCommandExecutorAdapter |
| **agent** | executor |
| **spec_refs** | Master Spec §5.2 (SubprocessCommandExecutorAdapter), §4.2 (CommandExecutorPort) |
| **goal** | Create `src/infrastructure/adapters/subprocess_command_adapter.py` implementing `CommandExecutorPort`. |
| **scope** | |
| | - Constructor: `__init__(self, timeout: int = 30)`. |
| | - `async execute(self, command: str, timeout: int = 30) -> CommandExecutionResult`. |
| | - Execute command via `asyncio.create_subprocess_shell`. |
| | - Capture stdout, stderr, exit_code. |
| **out_of_scope** | Whitelist validation (delegated to CommandValidatorPort, called by use case). |
| **inputs** | Master Spec §5.2 SubprocessCommandExecutorAdapter; TASK-008 (CommandExecutorPort), TASK-007 (CommandExecutionResult). |
| **implementation_notes** | Use `asyncio.create_subprocess_shell(command, stdout=PIPE, stderr=PIPE)`. The use case (TASK-014) must validate BEFORE calling this adapter. |
| **edge_cases** | Timeout → kill process, return failure. Command returns non-zero exit → still return result with exit_code (use case decides if it's error). |
| **done_criteria** | Class executes shell command, captures output, implements CommandExecutorPort. |
| **verification** | Integration test TASK-033. |
| **dependencies** | TASK-008 (CommandExecutorPort), TASK-007 (CommandExecutionResult) |
| **handoff_context** | Used by ExecuteCommandUseCase (TASK-014). |
| **source_of_truth** | Master Spec §5.2 |
| **stale_terms_guard** | This adapter does NOT validate — validation is in the use case via CommandValidatorPort. |
| **status** | `done` |
| **executor_notes** |  |
| **verification_result** |  |
| **blocker** | `none` |

---

### TASK-021 — Implement WhitelistCommandValidatorAdapter

| Field | Value |
|---|---|
| **id** | `TASK-021` |
| **title** | Implement WhitelistCommandValidatorAdapter |
| **agent** | executor |
| **spec_refs** | Master Spec §5.2 (WhitelistCommandValidatorAdapter), §4.2 (CommandValidatorPort), §10.1 |
| **goal** | Create `src/infrastructure/adapters/whitelist_validator_adapter.py` implementing `CommandValidatorPort`. |
| **scope** | |
| | - Constructor: `__init__(self, whitelist_path: str)`. |
| | - Load `commands-whitelist.yaml` (created in TASK-002). |
| | - `is_allowed(self, command: str) -> bool`: check against `allowed_commands` patterns using fnmatch/glob matching, reject if matches any `denied_commands`. |
| | - Always reject commands containing `sudo`. |
| **out_of_scope** | Command execution. |
| **inputs** | Master Spec §5.2 WhitelistCommandValidatorAdapter, §10.1; TASK-008 (CommandValidatorPort), TASK-002 (whitelist file). |
| **implementation_notes** | Use `yaml.safe_load` to load whitelist. Use `fnmatch.fnmatch` for pattern matching. Denied patterns take precedence over allowed. |
| **edge_cases** | Whitelist file missing → log warning, deny all commands (fail-safe). Empty command → deny. Command with `sudo` → deny. |
| **done_criteria** | Class loads whitelist, validates commands against patterns, implements CommandValidatorPort. |
| **verification** | Unit test TASK-029: `is_allowed("systemctl poweroff")` → True; `is_allowed("rm -rf /")` → False; `is_allowed("sudo ls")` → False. |
| **dependencies** | TASK-008 (CommandValidatorPort), TASK-002 (whitelist file) |
| **handoff_context** | Used by ExecuteCommandUseCase (TASK-014). |
| **source_of_truth** | Master Spec §5.2, integration-map.md §4.3 |
| **stale_terms_guard** | `sudo` commands always denied regardless of whitelist. |
| **status** | `done` |
| **executor_notes** |  |
| **verification_result** |  |
| **blocker** | `none` |

---

### TASK-022 — Implement SwayNCNotificationSenderAdapter

| Field | Value |
|---|---|
| **id** | `TASK-022` |
| **title** | Implement SwayNCNotificationSenderAdapter (notify-send + D-Bus) |
| **agent** | executor |
| **spec_refs** | Master Spec §5.2 (SwayNCNotificationSenderAdapter), §4.2 (NotificationSenderPort), §7.3, Decision locked #13 |
| **goal** | Create `src/infrastructure/adapters/swaync_notification_adapter.py` implementing `NotificationSenderPort`. |
| **scope** | |
| | - Constructor: no special deps beyond system notify-send. |
| | - `async send(self, title: str, message: str, urgency: str, actions: list[dict]) -> str | None`. |
| |   - Build `notify-send` command: `notify-send "<title>" "<message>" -u <urgency> --action="key=label" ...`. |
| |   - Execute via asyncio subprocess. |
| |   - Parse notification_id from stdout. |
| |   - Return notification_id if actions present, else None. |
| | - `async wait_for_action(self, notification_id: str, timeout_seconds: int) -> str | None`. |
| |   - Listen for D-Bus signal from SwayNC (`org.erikreider.swaync.cc.ActionInvoked`). |
| |   - Use `asyncio.Event` for synchronization. |
| |   - Return the action key or `None` on timeout. |
| **out_of_scope** | Notification display logic — handled by SwayNC. |
| **inputs** | Master Spec §5.2 SwayNCNotificationSenderAdapter, §7.3; TASK-008 (NotificationSenderPort). |
| **implementation_notes** | For `send`: use `shlex.quote` for shell safety. For `wait_for_action`: use `dasbus` or `pydbus` or direct D-Bus via `dbus-next` to listen for SwayNC's ActionInvoked signal. `asyncio.Event` set when matching notification_id received. |
| **edge_cases** | notify-send binary not found → raise NotificationError (domain). D-Bus not available → log warning, return None. Multiple actions → all passed via multiple `--action` flags. |
| **done_criteria** | Class sends notifications via notify-send, waits for action via D-Bus, implements both methods of NotificationSenderPort. |
| **verification** | Integration test TASK-033. Manual: `notify-send "test" "hello"` on dev machine. |
| **dependencies** | TASK-008 (NotificationSenderPort), TASK-006 (NotificationError) |
| **handoff_context** | Used by ShowNotificationUseCase (TASK-012). |
| **source_of_truth** | Master Spec §5.2, Decision locked #13 |
| **stale_terms_guard** | `send()` retorna inmediatamente (no bloquea). `wait_for_action()` usa D-Bus signals, no polling. |
| **status** | `done` |
| **executor_notes** |  |
| **verification_result** |  |
| **blocker** | `none` |

---

### TASK-023 — Implement HTTPXClientAdapter

| Field | Value |
|---|---|
| **id** | `TASK-023` |
| **title** | Implement HTTPXClientAdapter |
| **agent** | executor |
| **spec_refs** | Master Spec §5.2 (HTTPXClientAdapter), §4.2 (HTTPClientPort), §6.3 |
| **goal** | Create `src/infrastructure/adapters/httpx_client_adapter.py` implementing `HTTPClientPort`. |
| **scope** | |
| | - Constructor: `__init__(self)` — uses `httpx.AsyncClient`. |
| | - `async post(self, url: str, json: dict, headers: dict | None = None, timeout: int = 10) -> dict`. |
| | - Send POST with JSON body, return response JSON dict. |
| | - Retry: configurable per caller (handled by use case via Master Spec §8.1). |
| **out_of_scope** | Use-case-specific retry logic (handled by use cases). |
| **inputs** | Master Spec §5.2 HTTPXClientAdapter; TASK-008 (HTTPClientPort). |
| **implementation_notes** | Use `httpx.AsyncClient` with `timeout=httpx.Timeout(timeout)`. Raise on HTTP errors (4xx, 5xx) — callers handle. Keep the client alive for reuse (context manager pattern). |
| **edge_cases** | Connection refused → raise `httpx.ConnectError` (caller handles). Timeout → raise `httpx.TimeoutException`. |
| **done_criteria** | Class performs HTTP POST with JSON, returns response dict, implements HTTPClientPort. |
| **verification** | Integration test TASK-033. |
| **dependencies** | TASK-008 (HTTPClientPort) |
| **handoff_context** | Used by GenerateTTSUseCase (TASK-011) and HandleErrorUseCase (TASK-010). |
| **source_of_truth** | Master Spec §5.2 |
| **stale_terms_guard** | None. |
| **status** | `done` |
| **executor_notes** |  |
| **verification_result** |  |
| **blocker** | `none` |

---

### TASK-024 — Implement AsyncFileWriterAdapter

| Field | Value |
|---|---|
| **id** | `TASK-024` |
| **title** | Implement AsyncFileWriterAdapter |
| **agent** | executor |
| **spec_refs** | Master Spec §5.2 (AsyncFileWriterAdapter), §4.2 (FileWriterPort) |
| **goal** | Create `src/infrastructure/adapters/async_file_writer_adapter.py` implementing `FileWriterPort`. |
| **scope** | |
| | - `async write(self, path: str, content: str) -> None`. |
| | - Write content asynchronously using `aiofiles`. |
| **out_of_scope** | File reading, file watching. |
| **inputs** | Master Spec §5.2 AsyncFileWriterAdapter; TASK-008 (FileWriterPort). |
| **implementation_notes** | Use `aiofiles.open(path, 'w')` and `await f.write(content)`. Ensure parent directory exists (`Path(path).parent.mkdir(parents=True, exist_ok=True)`). |
| **edge_cases** | Permission denied → log error, raise IOError. Path is a directory → raise. |
| **done_criteria** | Class writes content to file asynchronously, implements FileWriterPort. |
| **verification** | Unit test TASK-029 (with tempfile). |
| **dependencies** | TASK-008 (FileWriterPort) |
| **handoff_context** | Used by GenerateTTSUseCase (TASK-011) to write `/tmp/chappie_tts_text.txt`. |
| **source_of_truth** | Master Spec §5.2 |
| **stale_terms_guard** | Must write `/tmp/chappie_tts_text.txt` (NOT `chappie_tts_state.txt` — that is chappie-daemon). |
| **status** | `done` |
| **executor_notes** |  |
| **verification_result** |  |
| **blocker** | `none` |

---

## Phase 6: Infrastructure — Driving Adapters (Consumers)

---

### TASK-025 — Implement ExecutionConsumer

| Field | Value |
|---|---|
| **id** | `TASK-025` |
| **title** | Implement ExecutionConsumer (chappie.responses) |
| **agent** | executor |
| **spec_refs** | Master Spec §5.1 (ExecutionConsumer), §6.1 (chappie.responses queue), §7.1 |
| **goal** | Create `src/infrastructure/consumers/execution_consumer.py`. |
| **scope** | |
| | - Connect to RabbitMQ, consume `chappie.responses` queue. |
| | - Parse JSON body into `ChappieResponse`. |
| | - Delegate to `ProcessResponseUseCase.execute(response)`. |
| | - Manual ACK after successful processing. |
| | - On processing error → NACK (requeue=false) → message goes to DLQ. |
| | - Idempotency: session_id + timestamp (skip if already processed). |
| **out_of_scope** | RabbitMQ connection setup (shared across consumers via TASK-016 container). |
| **inputs** | Master Spec §5.1 ExecutionConsumer, §6.1; TASK-004 (ChappieResponse), TASK-009 (ProcessResponseUseCase), TASK-015 (AppConfig). |
| **implementation_notes** | Use `aio-pika` consumer pattern. Constructor: `__init__(self, connection: aio_pika.RobustConnection, use_case: ProcessResponseUseCase, config: AppConfig)`. Queue declare with `durable=True`, `arguments={"x-message-ttl": 60000, "x-dead-letter-exchange": "", "x-dead-letter-routing-key": "chappie.responses.dlq"}`. |
| **edge_cases** | Invalid JSON → NACK + log error. Duplicate message (session_id+timestamp cached) → ACK without processing. Use case raises exception → NACK + publish error to chappie.errors. |
| **done_criteria** | Consumer connects, parses messages, delegates to use case, handles ACK/NACK correctly. |
| **verification** | Integration test TASK-033. |
| **dependencies** | TASK-004 (ChappieResponse), TASK-009 (ProcessResponseUseCase), TASK-015 (AppConfig), TASK-016 (container for connection) |
| **handoff_context** | Started by main.py (TASK-026). |
| **source_of_truth** | Master Spec §5.1 |
| **stale_terms_guard** | Queue name exactly `chappie.responses`. DLQ: `chappie.responses.dlq`. ACK manual. NOT a producer of `chappie.notifications`. |
| **status** | `done` |
| **executor_notes** |  |
| **verification_result** |  |
| **blocker** | `none` |

---

### TASK-026 — Implement ErrorConsumer

| Field | Value |
|---|---|
| **id** | `TASK-026` |
| **title** | Implement ErrorConsumer (chappie.errors) |
| **agent** | executor |
| **spec_refs** | Master Spec §5.1 (ErrorConsumer), §6.1 (chappie.errors queue), §7.2 |
| **goal** | Create `src/infrastructure/consumers/error_consumer.py`. |
| **scope** | |
| | - Consume `chappie.errors` queue. |
| | - Parse JSON into `ErrorMessage`. |
| | - Delegate to `HandleErrorUseCase.execute(error)`. |
| | - Manual ACK after processing. |
| **out_of_scope** | Error publishing (that's ExecutionConsumer + TTSConsumer). |
| **inputs** | Master Spec §5.1 ErrorConsumer, §6.1; TASK-004 (ErrorMessage), TASK-010 (HandleErrorUseCase). |
| **implementation_notes** | Queue: `chappie.errors` with 30s TTL, DLQ `chappie.errors.dlq`. Manual ACK. |
| **edge_cases** | n8n webhook fails → NACK, message retried (up to TTL). After max retries → DLQ. |
| **done_criteria** | Consumer processes error messages, delegates to HandleErrorUseCase. |
| **verification** | Integration test TASK-033. |
| **dependencies** | TASK-004 (ErrorMessage), TASK-010 (HandleErrorUseCase), TASK-016 (container) |
| **handoff_context** | Started by main.py (TASK-026). |
| **source_of_truth** | Master Spec §5.1 |
| **stale_terms_guard** | Queue: `chappie.errors`. DLQ: `chappie.errors.dlq`. Does NOT reproduce voice. |
| **status** | `done` |
| **executor_notes** |  |
| **verification_result** |  |
| **blocker** | `none` |

---

### TASK-027 — Implement TTSConsumer

| Field | Value |
|---|---|
| **id** | `TASK-027` |
| **title** | Implement TTSConsumer (chappie.tts.requests) |
| **agent** | executor |
| **spec_refs** | Master Spec §5.1 (TTSConsumer), §6.1 (chappie.tts.requests queue), §7.1 step 4-5 |
| **goal** | Create `src/infrastructure/consumers/tts_consumer.py`. |
| **scope** | |
| | - Consume `chappie.tts.requests` queue. |
| | - Parse JSON into `TTSRequest`. |
| | - Delegate to `GenerateTTSUseCase.execute(request)`. |
| | - Manual ACK after processing. |
| | - On TTS failure → publish `ErrorMessage` to `chappie.errors`. |
| **out_of_scope** | TTS generation (delegates to use case). |
| **inputs** | Master Spec §5.1 TTSConsumer, §6.1; TASK-004 (TTSRequest, ErrorMessage), TASK-011 (GenerateTTSUseCase). |
| **implementation_notes** | Queue: `chappie.tts.requests` with 30s TTL. Priority: high for error messages. Manual ACK. On TTS error → publish ErrorMessage to chappie.errors then ACK original (error path handled by ErrorConsumer). |
| **edge_cases** | High priority messages should be processed before normal (if queue supports priority). TTS generation fails → error path. |
| **done_criteria** | Consumer processes TTS requests, delegates to GenerateTTSUseCase, handles errors correctly. |
| **verification** | Integration test TASK-033. |
| **dependencies** | TASK-004 (TTSRequest, ErrorMessage), TASK-011 (GenerateTTSUseCase), TASK-016 (container) |
| **handoff_context** | Started by main.py (TASK-026). |
| **source_of_truth** | Master Spec §5.1 |
| **stale_terms_guard** | Queue: `chappie.tts.requests`. TTSConsumer IS a producer of `chappie.errors` (F-003). |
| **status** | `done` |
| **executor_notes** |  |
| **verification_result** |  |
| **blocker** | `none` |

---

### TASK-028 — Implement NotificationConsumer

| Field | Value |
|---|---|
| **id** | `TASK-028` |
| **title** | Implement NotificationConsumer (chappie.agent.results, chappie.agent.questions, chappie.notifications) |
| **agent** | executor |
| **spec_refs** | Master Spec §5.1 (NotificationConsumer), §6.1 (three queues), §7.3 |
| **goal** | Create `src/infrastructure/consumers/notification_consumer.py`. |
| **scope** | |
| | - Consume three queues simultaneously: `chappie.agent.results`, `chappie.agent.questions`, `chappie.notifications`. |
| | - `on_agent_result`: parse `AgentResult`, build `NotificationMessage`, call `ShowNotificationUseCase` (fire-and-forget, no wait). |
| | - `on_agent_question`: parse `AgentQuestion`, build `NotificationMessage` with actions, call `ShowNotificationUseCase`, wait for answer, publish `AgentAnswer` to `chappie.agent.answers`. |
| | - `on_notification`: parse `NotificationMessage`, call `ShowNotificationUseCase` (fire-and-forget if no actions). |
| | - Each message handler runs as `asyncio.create_task()` to not block the consumer loop. |
| **out_of_scope** | Actual notification display (delegates to use case). |
| **inputs** | Master Spec §5.1 NotificationConsumer, §7.3; TASK-004 (AgentResult, AgentQuestion, AgentAnswer, NotificationMessage), TASK-012 (ShowNotificationUseCase). |
| **implementation_notes** | One consumer class that binds to 3 queues. Constructor: `__init__(self, connection, use_case: ShowNotificationUseCase, publisher: RabbitMQPublisherPort)`. Each handler parses queue-specific schema. `on_agent_question` runs async task for response wait. Queue TTLs: results=300s, questions=600s, notifications=120s. |
| **edge_cases** | User doesn't respond to question → timeout → answer="ignore", publish to chappie.agent.answers. Multiple concurrent questions → each handled independently via separate tasks. |
| **done_criteria** | Consumer handles all 3 queues, delegates to use case appropriately, publishes answers to chappie.agent.answers. |
| **verification** | Integration test TASK-033. |
| **dependencies** | TASK-004 (AgentResult, AgentQuestion, AgentAnswer, NotificationMessage), TASK-012 (ShowNotificationUseCase), TASK-008 (RabbitMQPublisherPort), TASK-016 (container) |
| **handoff_context** | Started by main.py (TASK-026). |
| **source_of_truth** | Master Spec §5.1 |
| **stale_terms_guard** | Answer default on timeout: "ignore". Publish to `chappie.agent.answers`. NotificationConsumer uses async tasks, does NOT block event loop. |
| **status** | `done` |
| **executor_notes** |  |
| **verification_result** |  |
| **blocker** | `none` |

---

## Phase 7: Entrypoint

---

### TASK-029 — Implement main.py entrypoint

| Field | Value |
|---|---|
| **id** | `TASK-029` |
| **title** | Implement main.py entrypoint |
| **agent** | executor |
| **spec_refs** | Master Spec §13.2 (systemd service reference), hexagonal-architecture skill |
| **goal** | Create `src/main.py` as the application entrypoint that initializes the DI container, starts all 4 consumers, and runs forever. |
| **scope** | |
| | - Create `create_container()` from TASK-016. |
| | - Start ExecutionConsumer, ErrorConsumer, TTSConsumer, NotificationConsumer concurrently. |
| | - Handle graceful shutdown (SIGTERM, SIGINT). |
| | - Configure structured JSON logging. |
| **out_of_scope** | Systemd unit file (TASK-034). |
| **inputs** | Master Spec §9.1 (logging format), §13.2; TASK-016 (container), TASK-025–TASK-028 (consumers). |
| **implementation_notes** | File: `src/main.py`. Use `asyncio.gather()` to run all consumers. Graceful shutdown via signal handlers: cancel tasks, close RabbitMQ connection. Structured logging: `logging.basicConfig(format='{"timestamp":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s","message":"%(message)s"}')` or use `python-json-logger`. |
| **edge_cases** | RabbitMQ connection lost → aio-pika `connect_robust` handles reconnect. Any consumer crashes → log and continue (don't crash entire daemon). |
| **done_criteria** | `python -m chappie_notification` starts the daemon, connects to RabbitMQ, begins consuming. Graceful shutdown on Ctrl+C. |
| **verification** | Manual: start daemon, check logs. |
| **dependencies** | TASK-016 (container), TASK-025 (ExecutionConsumer), TASK-026 (ErrorConsumer), TASK-027 (TTSConsumer), TASK-028 (NotificationConsumer) |
| **handoff_context** | This is the executable entrypoint. Run via `uv run python -m chappie_notification` or `python src/main.py`. |
| **source_of_truth** | Master Spec §9.1, §13.2 |
| **stale_terms_guard** | JSON structured logging format. |
| **status** | `done` |
| **executor_notes** |  |
| **verification_result** |  |
| **blocker** | `none` |

---

## Phase 8: Tests

---

### TASK-030 — Configure pytest, pytest-asyncio, and pytest-cov

| Field | Value |
|---|---|
| **id** | `TASK-030` |
| **title** | Configure pytest, pytest-asyncio, and pytest-cov |
| **agent** | executor |
| **spec_refs** | Master Spec §12.1, §12.2; testing-strategy skill |
| **goal** | Add `[tool.pytest.ini_options]` to `pyproject.toml` and write `tests/conftest.py` with async fixtures. |
| **scope** | |
| | - Configure pytest: `asyncio_mode = "auto"`, testpaths = `["tests"]`. |
| | - Configure pytest-cov: `--cov=src --cov-report=term --cov-report=html --cov-fail-under=85` (per-file threshold configured separately). |
| | - Add `.coveragerc` or `[tool.coverage]` section excluding DTOs, config, exceptions, `__init__.py`. |
| | - Create `tests/conftest.py` with shared fixtures: mock ports, test AppConfig, etc. |
| **out_of_scope** | Writing actual test cases. |
| **inputs** | Master Spec §12; testing-strategy skill; TASK-001 (pyproject.toml). |
| **implementation_notes** | Exclude from coverage: DTOs (`src/application/dto/`), Config (`src/infrastructure/config/app_config.py`), Exceptions (`src/domain/exceptions/`), `__init__.py` files, Protocols (`src/application/ports/`). Coverage threshold per file testable: 85%. |
| **edge_cases** | None. |
| **done_criteria** | `pytest --cov` runs and reports coverage. Exclusions are applied. |
| **verification** | `pytest --cov --cov-report=term` runs successfully with 0 tests (passes because no tests yet). |
| **dependencies** | TASK-001 (pyproject.toml) |
| **handoff_context** | Test infrastructure ready for TASK-031 and TASK-032. |
| **source_of_truth** | testing-strategy skill, Master Spec §12 |
| **stale_terms_guard** | Min 85% by testable file. Exclusions declared explicitly. |
| **status** | `done` |
| **executor_notes** |  |
| **verification_result** |  |
| **blocker** | `none` |

---

### TASK-031 — Write unit tests for domain and application layers

| Field | Value |
|---|---|
| **id** | `TASK-031` |
| **title** | Write unit tests for domain and application layers |
| **agent** | executor |
| **spec_refs** | Master Spec §12.1; testing-strategy skill |
| **goal** | Create comprehensive unit tests for domain models, domain exceptions, and application use cases. |
| **scope** | |
| | - `tests/unit/domain/test_enums.py`: verify enum values. |
| | - `tests/unit/domain/test_value_objects.py`: verify dataclass construction, immutability, defaults. |
| | - `tests/unit/domain/test_events.py`: verify event creation. |
| | - `tests/unit/domain/test_exceptions.py`: verify exception hierarchy. |
| | - `tests/unit/application/test_process_response_use_case.py`: mock ports, verify delegation. |
| | - `tests/unit/application/test_handle_error_use_case.py`: mock HTTPClientPort. |
| | - `tests/unit/application/test_generate_tts_use_case.py`: mock TTSSynthesizerPort, FileWriterPort, HTTPClientPort. |
| | - `tests/unit/application/test_show_notification_use_case.py`: mock NotificationSenderPort. |
| | - `tests/unit/application/test_execute_agent_use_case.py`: mock AgentExecutorPort. |
| | - `tests/unit/application/test_execute_command_use_case.py`: mock CommandExecutorPort, CommandValidatorPort. |
| | - `tests/unit/infrastructure/test_whitelist_validator.py`: test with temp whitelist file. |
| | - `tests/unit/infrastructure/test_file_writer.py`: test with tempfile. |
| **out_of_scope** | Integration tests (TASK-032). E2E tests (TASK-033). |
| **inputs** | All domain, application, and infrastructure tasks (TASK-003 through TASK-024). |
| **implementation_notes** | Follow testing-strategy naming: `should_Result_when_Condition`. E.g., `should_return_success_when_all_actions_disabled`. Mock all ports. Use `pytest-asyncio` for async use cases. Domain tests are synchronous. |
| **edge_cases** | Test: ChappieResponse with all optional fields None. Test: CommandNotAllowedError raised. Test: ExecuteAgentUseCase publishes to chappie.errors on failure. Test: ShowNotificationUseCase timeout → answer="ignore". |
| **done_criteria** | All unit test files exist. `pytest tests/unit/ --cov=src` shows coverage ≥ 85% for domain and application testable files. |
| **verification** | `pytest tests/unit/ -v --cov=src/domain --cov=src/application --cov-report=term` — all pass, coverage meets threshold. |
| **dependencies** | TASK-003–TASK-024 (all domain, application, infrastructure tasks), TASK-030 (test config) |
| **handoff_context** | Unit tests protect business logic. Run before integration tests. |
| **source_of_truth** | Master Spec §12.1, testing-strategy skill |
| **stale_terms_guard** | Test all use case edge cases from spec §4.1. Test whitelist validator thoroughly. |
| **status** | `done` |
| **executor_notes** |  |
| **verification_result** |  |
| **blocker** | `none` |

---

### TASK-032 — Write integration tests for infrastructure adapters and consumers

| Field | Value |
|---|---|
| **id** | `TASK-032` |
| **title** | Write integration tests for infrastructure adapters and consumers |
| **agent** | executor |
| **spec_refs** | Master Spec §12.2; testing-strategy skill |
| **goal** | Create integration tests for adapters and consumers with real or containerized dependencies. |
| **scope** | |
| | - `tests/integration/test_rabbitmq_publisher.py`: use RabbitMQ testcontainer or mock broker. |
| | - `tests/integration/test_edge_tts.py`: test actual Edge-TTS generation (may need network). |
| | - `tests/integration/test_opencode_agent.py`: test with mock opencode binary. |
| | - `tests/integration/test_httpx_client.py`: test with mock HTTP server (httpx mock or pytest-httpx). |
| | - `tests/integration/test_consumers.py`: end-to-end consumer test with RabbitMQ testcontainer. |
| **out_of_scope** | E2E tests with full ecosystem (TASK-033). |
| **inputs** | TASK-017–TASK-028 (all adapters and consumers), TASK-030 (test config). |
| **implementation_notes** | Use `pytest-asyncio`. RabbitMQ tests: use `testcontainers` Python or mock with `aio-pika` in-memory. HTTP tests: use `pytest-httpx` or `respx`. Edge-TTS tests: may be skipped in CI (network-dependent). |
| **edge_cases** | RabbitMQ testcontainer not available → skip test with reason. Edge-TTS offline → skip test. |
| **done_criteria** | Integration test files exist. Tests pass when dependencies are available. Skipped tests have clear reasons. |
| **verification** | `pytest tests/integration/ -v` — all pass or are properly skipped. |
| **dependencies** | TASK-017–TASK-028 (adapters + consumers), TASK-030 (test config) |
| **handoff_context** | Integration tests verify real component interactions. |
| **source_of_truth** | Master Spec §12.2, testing-strategy skill |
| **stale_terms_guard** | Skip tests gracefully when external deps unavailable (not fail). |
| **status** | `done` |
| **executor_notes** |  |
| **verification_result** |  |
| **blocker** | `none` |

---

## Phase 9: Deployment Configuration

---

### TASK-033 — Create systemd user service unit

| Field | Value |
|---|---|
| **id** | `TASK-033` |
| **title** | Create systemd user service unit file |
| **agent** | executor |
| **spec_refs** | Master Spec §13.2 |
| **goal** | Create `chappie-notification.service` for systemd user deployment. |
| **scope** | |
| | - Write systemd unit file matching §13.2: `Type=simple`, `User=cris`, `ExecStart` using `uv run python -m chappie_notification`. |
| | - `After=network.target chappie-infra.service`. |
| | - `Restart=always`, `RestartSec=10`. |
| | - Add install instructions in README.md. |
| **out_of_scope** | Docker containerization (marked optional in spec). |
| **inputs** | Master Spec §13.2, TASK-029 (main.py). |
| **implementation_notes** | Place file in project root or `deploy/` directory. Unit file assumes `uv` is installed and project is in the right path. README should include `systemctl --user enable chappie-notification.service`. |
| **edge_cases** | `uv run` needs working directory set. `ExecStart` path must be absolute. |
| **done_criteria** | `chappie-notification.service` file exists matching spec. README has install instructions. |
| **verification** | `cat chappie-notification.service` matches §13.2. |
| **dependencies** | TASK-029 (main.py entrypoint works) |
| **handoff_context** | Deployment artifact. Not needed for development — daemon can run directly via `uv run`. |
| **source_of_truth** | Master Spec §13.2 |
| **stale_terms_guard** | `User=cris` is from spec. Adjust if needed. |
| **status** | `done` |
| **executor_notes** |  |
| **verification_result** |  |
| **blocker** | `none` |

---

## Dependency Graph Summary

```
Phase 1: Setup
  TASK-001 (scaffold) ────────────────────────► TASK-002 (config files)

Phase 2: Domain
  TASK-001 ───────────────────────────────────► TASK-003 (enums)
  TASK-003 ───────────────────────────────────► TASK-004 (value objects)
  TASK-003 ───────────────────────────────────► TASK-005 (events)
  TASK-001 ───────────────────────────────────► TASK-006 (exceptions)

Phase 3: Application
  TASK-003, TASK-001 ─────────────────────────► TASK-007 (DTOs)
  TASK-007 ───────────────────────────────────► TASK-008 (output ports)
  TASK-004, TASK-007, TASK-008 ───────────────► TASK-009 (ProcessResponseUseCase)
  TASK-004, TASK-007, TASK-008, TASK-015 ─────► TASK-010 (HandleErrorUseCase)
  TASK-004, TASK-007, TASK-008, TASK-015 ─────► TASK-011 (GenerateTTSUseCase)
  TASK-004, TASK-007, TASK-008 ───────────────► TASK-012 (ShowNotificationUseCase)
  TASK-004, TASK-007, TASK-008, TASK-015 ─────► TASK-013 (ExecuteAgentUseCase)
  TASK-004, TASK-006, TASK-007, TASK-008, TASK-015 ► TASK-014 (ExecuteCommandUseCase)

Phase 4: Config
  TASK-001 ───────────────────────────────────► TASK-015 (AppConfig)
  TASK-009–014, TASK-017–022, TASK-023–025 ───► TASK-016 (DI wiring)

Phase 5: Driven Adapters
  TASK-008, TASK-015 ─────────────────────────► TASK-017 (RabbitMQPublisherAdapter)
  TASK-008, TASK-006 ─────────────────────────► TASK-018 (EdgeTTSSynthesizerAdapter)
  TASK-008, TASK-007 ─────────────────────────► TASK-019 (OpenCodeAgentExecutorAdapter)
  TASK-008, TASK-007 ─────────────────────────► TASK-020 (SubprocessCommandExecutorAdapter)
  TASK-008, TASK-002 ─────────────────────────► TASK-021 (WhitelistCommandValidatorAdapter)
  TASK-008, TASK-006 ─────────────────────────► TASK-022 (SwayNCNotificationSenderAdapter)
  TASK-008 ───────────────────────────────────► TASK-023 (HTTPXClientAdapter)
  TASK-008 ───────────────────────────────────► TASK-024 (AsyncFileWriterAdapter)

Phase 6: Consumers
  TASK-004, TASK-009, TASK-015 ───────────────► TASK-025 (ExecutionConsumer)
  TASK-004, TASK-010 ─────────────────────────► TASK-026 (ErrorConsumer)
  TASK-004, TASK-011 ─────────────────────────► TASK-027 (TTSConsumer)
  TASK-004, TASK-012, TASK-008 ───────────────► TASK-028 (NotificationConsumer)

Phase 7: Entrypoint
  TASK-016, TASK-025–028 ─────────────────────► TASK-029 (main.py)

Phase 8: Tests
  TASK-001 ───────────────────────────────────► TASK-030 (test config)
  TASK-003–024, TASK-030 ─────────────────────► TASK-031 (unit tests)
  TASK-017–028, TASK-030 ─────────────────────► TASK-032 (integration tests)

Phase 9: Deploy
  TASK-029 ───────────────────────────────────► TASK-033 (systemd service)
```

---

## Summary

| Phase | Tasks | Task IDs |
|---|---|---|
| 1. Setup | 2 | TASK-001, TASK-002 |
| 2. Domain | 4 | TASK-003, TASK-004, TASK-005, TASK-006 |
| 3. Application | 8 | TASK-007, TASK-008, TASK-009, TASK-010, TASK-011, TASK-012, TASK-013, TASK-014 |
| 4. Config | 2 | TASK-015, TASK-016 |
| 5. Driven Adapters | 8 | TASK-017, TASK-018, TASK-019, TASK-020, TASK-021, TASK-022, TASK-023, TASK-024 |
| 6. Consumers | 4 | TASK-025, TASK-026, TASK-027, TASK-028 |
| 7. Entrypoint | 1 | TASK-029 |
| 8. Tests | 3 | TASK-030, TASK-031, TASK-032 |
| 9. Deploy | 1 | TASK-033 |
| **Total** | **33** | |

---

*Board maintained by: task-decomposer*  
*Next action: Handoff to Executor — claim TASK-001 first.*
