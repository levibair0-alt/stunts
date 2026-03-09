# Voice Control Core - Athena Command OS

The primary intent-to-execution interface for the Athena Command OS, enabling "Speak and Execute" functionality with real-time WebSocket broadcasting to the Fractal Engine View and Emergency Stop safety protocol.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    VOICE CONTROL CORE                        │
├─────────────────────────────────────────────────────────────┤
│  Audio Capture → Wake Word → Transcription → Intent Parser  │
│                       ↓                                     │
│  Command Bus → Executor → WebSocket Broadcast → Audit Log  │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Voice Input Layer (`voice_input.py`)
- **Audio Capture:** Microphone input with configurable sample rate
- **Transcription:** Faster-Whisper for local transcription (no API latency)
- **VAD:** Voice Activity Detection to filter background noise
- **Output:** Raw transcript string + confidence score

### 2. Wake Word Detection (`wake_word.py`)
- **Activation Phrase:** "Athena"
- **Fuzzy Matching:** Tolerates slight variations in pronunciation
- **Sensitivity:** Configurable detection threshold

### 3. Intent Parser (`intent_parser.py`)
- **Intent Classification:**
  - `QUERY`: Run command via subprocess/PyAutoGUI
  - `VERIFY`: Fetch data from Quintuple Engine
  - `CREATE`: Trigger Generator engine
  - `MONETIZE`: Request audit report from Auditor
  - `AUDIT`: Config/status commands
  - `EMERGENCY_STOP`: Immediate system halt
  - `RESUME`: Resume after emergency stop
- **Confidence Thresholds:**
  - ≥0.7: Execute
  - 0.4-0.7: Clarification
  - <0.4: Reject
- **Entity Extraction:** Parse targets, parameters, flags

### 4. Command Bus (`command_bus.py`)
- **SQLite Audit Log:** Every command logged with full context
- **Routing Logic:** Dispatch to appropriate handler
- **Validation Middleware:** Check permissions before execution
- **Async Support:** Non-blocking with callbacks

### 5. Executor (`executor.py`)
- **Shell Commands:** subprocess with timeout and output capture
- **GUI Automation:** PyAutoGUI for mouse/keyboard
- **API Calls:** HTTP client for EVE-3 Oracle integration
- **Confirmation Flow:** High-risk commands require verbal confirmation

### 6. WebSocket Server (`websocket_server.py`)
- **Port:** 8766 (Voice Control Bus)
- **Broadcasts:**
  - `intent_detected`: {intent, confidence, raw_transcript}
  - `status_update`: {status: 'LISTENING'|'PROCESSING'|'EXECUTING'}
  - `engine_triggered`: {engine: 'Sensor'|'Validator'|'Generator'|'Monetizer'|'Auditor'}
  - `execution_result`: {success, output, duration_ms}
  - `emergency_alert`: RED ALERT to all nodes

### 7. Emergency Stop Protocol (`emergency_stop.py`)
- **Voice Commands:** "Athena emergency stop", "kill switch", "halt system"
- **Resume Command:** "Resume Athena operations"
- **Actions:**
  1. Broadcast RED ALERT to all Fractal View nodes
  2. SIGTERM → 0.5s grace → SIGKILL all subprocesses
  3. Write immutable audit entry
  4. Freeze system until verbal resume

### 8. SAFE_MODE (`safe_mode.py`)
Blocks dangerous commands:
- `rm -rf` (mass deletion)
- `format` (disk formatting)
- `shutdown -h now` (system shutdown)
- `sudo rm` (elevated deletion)
- Fork bombs, disk overwrites, etc.

## Usage

### Basic Usage

```bash
# Start voice control
python -m voice_control

# Run in demo mode (no microphone required)
python -m voice_control --demo

# Custom config
python -m voice_control --config /path/to/config.json

# Custom WebSocket port
python -m voice_control --port 8766
```

### Programmatic Usage

```python
from voice_control import VoiceController, VoiceConfig

# Create configuration
config = VoiceConfig()
config.wake_word = "athena"
config.confidence_execute = 0.7
config.safe_mode_enabled = True

# Initialize controller
controller = VoiceController(config=config)

# Run the main loop
import asyncio
asyncio.run(controller.run())
```

### Voice Commands

```
"Athena show me opportunities"        → QUERY → Sensor
"Athena generate offer for freelancers" → CREATE → Generator
"Athena verify last session"          → VERIFY → Validator
"Athena audit status"                 → AUDIT → Auditor
"Athena monetize this project"        → MONETIZE → Monetizer
"Athena emergency stop"               → EMERGENCY_STOP → HALT
"Resume Athena operations"            → RESUME → Continue
```

## Intent-to-Engine Mapping

```python
INTENT_MAP = {
    'QUERY': 'Sensor',
    'VERIFY': 'Validator',
    'CREATE': 'Generator',
    'MONETIZE': 'Monetizer',
    'AUDIT': 'Auditor'
}
```

When voice command detected:
1. Parse intent
2. Broadcast `intent_detected` to WebSocket
3. Broadcast `engine_triggered` with mapped engine name
4. Fractal View node lights up via `useVoiceBridge.ts`
5. Execute command
6. Broadcast `execution_result`
7. Node returns to idle after 3 seconds

## WebSocket Protocol

### Connect
```javascript
const socket = new WebSocket('ws://localhost:8766');
```

### Events Received

#### Intent Detected
```json
{
  "type": "intent_detected",
  "payload": {
    "intent": "CREATE",
    "confidence": 0.85,
    "raw_transcript": "generate offer for freelancers",
    "engine": "Generator"
  },
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

#### Status Update
```json
{
  "type": "status_update",
  "payload": {
    "status": "LISTENING"
  },
  "timestamp": "2024-01-15T10:30:01.000Z"
}
```

#### Engine Triggered
```json
{
  "type": "engine_triggered",
  "payload": {
    "engine": "Generator",
    "action": "CREATE"
  },
  "timestamp": "2024-01-15T10:30:02.000Z"
}
```

#### Execution Result
```json
{
  "type": "execution_result",
  "payload": {
    "success": true,
    "output": "Offer generated successfully",
    "duration_ms": 1250,
    "engine": "Generator"
  },
  "timestamp": "2024-01-15T10:30:03.000Z"
}
```

#### Emergency Alert
```json
{
  "type": "emergency_alert",
  "payload": {
    "level": "CRITICAL",
    "message": "EMERGENCY STOP ACTIVATED - SYSTEM HALTING",
    "action": "HALT_ALL_ENGINES"
  },
  "timestamp": "2024-01-15T10:30:04.000Z"
}
```

## React Hook for Fractal View

```typescript
export const useVoiceBridge = () => {
  const [activeNode, setActiveNode] = useState<string | null>(null);
  const [isListening, setIsListening] = useState(false);

  useEffect(() => {
    const socket = new WebSocket('ws://localhost:8766');
    socket.onmessage = (event) => {
      const { type, payload } = JSON.parse(event.data);
      
      if (type === 'status_update') {
        setIsListening(payload.status === 'LISTENING');
      }
      
      if (type === 'engine_triggered') {
        setActiveNode(payload.engine);
        setTimeout(() => setActiveNode(null), 3000);
      }
      
      if (type === 'emergency_alert') {
        // Handle emergency - flash all nodes red
        setActiveNode('EMERGENCY');
      }
    };
    
    return () => socket.close();
  }, []);

  return { activeNode, isListening };
};
```

## Configuration

Create a `config.json` file:

```json
{
  "sample_rate": 16000,
  "chunk_size": 1024,
  "channels": 1,
  "wake_word": "athena",
  "wake_word_sensitivity": 0.8,
  "whisper_model": "base",
  "confidence_execute": 0.7,
  "confidence_clarify": 0.4,
  "websocket_host": "localhost",
  "websocket_port": 8766,
  "audit_db_path": "voice_commands.db",
  "safe_mode_enabled": true,
  "command_timeout": 30
}
```

## Audit Database Schema

```sql
CREATE TABLE voice_commands (
    id INTEGER PRIMARY KEY,
    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
    raw_transcript TEXT,
    intent TEXT,
    confidence REAL,
    parameters TEXT,           -- JSON
    execution_status TEXT,     -- success/failure/blocked
    execution_output TEXT,
    duration_ms INTEGER,
    triggered_engine TEXT      -- Maps to Fractal View node
);
```

## Integration Points

### With Quintuple Engine
- Voice command `generate offer for freelancers` → triggers Generator engine
- Command `audit last session` → queries Auditor engine
- Query `show me opportunities` → calls Sensor/Validator pipeline

### With Athena Dashboard (Fractal View)
- WebSocket on port 8766 broadcasts intent → node highlights
- Voice transcript displayed in floating overlay panel
- Confidence score shown near voice indicator
- Emergency Stop triggers all nodes to flash RED

### With EVE-3 Oracle
- Intent `create creative path` → POST to `/generate-ideas` endpoint
- Use athena_bridge encryption for all external calls

## Dependencies

```
faster-whisper>=0.10.0    # Local transcription
pyaudio>=0.2.13           # Audio capture
pyautogui>=0.9.54         # GUI automation
numpy>=1.24.0             # Audio processing
websockets>=11.0          # WebSocket server
requests>=2.31.0          # API calls
```

## Safety Features

- ✅ **SAFE_MODE**: Blocks dangerous shell commands
- ✅ **Confirmation Flow**: High-risk commands require verbal confirmation
- ✅ **Emergency Stop**: Voice-activated system halt
- ✅ **Audit Logging**: Every command logged with full context
- ✅ **Confidence Thresholds**: Ambiguous commands trigger clarification
- ✅ **Process Management**: Subprocess timeout and cleanup
- ✅ **Graceful Shutdown**: Ctrl+C handler with cleanup

## Demo Mode

Run without microphone:

```bash
python -m voice_control --demo
```

Runs through preset commands:
1. "Athena show me opportunities"
2. "Athena generate offer for freelancers"
3. "Athena verify last session"
4. "Athena audit status"
5. "Athena emergency stop"
6. "Resume Athena operations"

Shows full pipeline: input → intent → broadcast → execution → audit

## Project Structure

```
voice_control/
├── __init__.py              # Package initialization
├── __main__.py              # Entry point
├── controller.py            # Main orchestration loop
├── voice_input.py           # Audio capture + transcription
├── wake_word.py             # "Athena" detection
├── intent_parser.py         # NLU + confidence scoring
├── command_bus.py           # Routing + audit logging
├── executor.py              # Command execution layer
├── websocket_server.py      # Port 8766 broadcaster
├── emergency_stop.py        # Kill switch protocol
├── safe_mode.py             # Dangerous command protection
├── config.py                # Settings + hot reload
├── requirements.txt         # Dependencies
└── README.md                # This file
```

## Development

### Running Tests

```bash
# Install dev dependencies
pip install -r requirements.txt

# Run the voice control
python -m voice_control --demo
```

### Adding New Intents

1. Add intent type to `IntentType` enum in `intent_parser.py`
2. Add classification patterns to `INTENT_PATTERNS`
3. Register handler in `controller.py` `_register_command_handlers()`
4. Implement handler in `executor.py`

### Customizing Safe Mode

Add dangerous patterns to config:

```python
config.dangerous_patterns = [
    r"dangerous_command_pattern",
    r"another_bad_pattern",
]
```

## License

MIT

## Support

Part of the Athena Orchestrator ecosystem.
