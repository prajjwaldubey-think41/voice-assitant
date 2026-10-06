## Conversational AI (Voice Assistant)
- It is a voice assistant which will act as a assistant for the user.
- The input will be audio converted to text with the help of the deepgram API.
- The converted text will be feeded into the LLM for a future purpose.
### Tech Stack:
- Language: Python
- Backend Framework: Fast API
- package: uv
- Speech to text API: Deepgram APIs

## Running the service

```powershell
$env:DEEPGRAM_API_KEY = "your-deepgram-api-key"
uv run fastapi dev main.py
```

The service exposes `ws://127.0.0.1:8000/ws/audio`. Clients must send binary
audio frames containing raw, linear PCM audio at 16,000 Hz and one channel.
The server responds with final transcript messages such as:

```json
{"type":"transcript","text":"hello world","final":true}
```

Text frames receive a `binary_audio_required` error. Final utterances are also
available through `DeepgramTranscriber.llm_queue` for a future LLM consumer.
The default `dummy-api-key` is only for local wiring and tests; live Deepgram
transcription requires a valid `DEEPGRAM_API_KEY`.

Final transcripts are passed to `GeminiOrchestrator`. Set `GEMINI_API_KEY` to
enable Gemini command translation. Until then, the service returns a
configuration response and performs no tool operation. The orchestrator
supports `LedgerManager` for named variables, `WebSearcher` for current search
data, `PythonCodeInterpreter` for restricted calculations, and `AuditTrail`
for operation history. Every executed command is audited.

Run the offline adapter test with:

```powershell
uv run pytest
```