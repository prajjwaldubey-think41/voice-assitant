from __future__ import annotations

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from assistant import GeminiOrchestrator
from input import DeepgramTranscriber


app = FastAPI(title="Voice Assistant")
assistant = GeminiOrchestrator()


@app.websocket("/ws/audio")
async def audio_websocket(websocket: WebSocket) -> None:
	await websocket.accept()
	transcriber = DeepgramTranscriber()

	try:
		async with transcriber.connect():
			async with _send_transcripts(websocket, transcriber, assistant):
				while True:
					message = await websocket.receive()
					if message.get("bytes") is not None:
						await transcriber.send_audio(message["bytes"])
					elif message.get("text") is not None:
						await websocket.send_json(
							{"type": "error", "code": "binary_audio_required"}
						)
					else:
						break
	except WebSocketDisconnect:
		pass
	except Exception as error:
		await websocket.send_json({"type": "error", "code": "transcription_failed", "detail": str(error)})


class _send_transcripts:
	def __init__(self, websocket: WebSocket, transcriber: DeepgramTranscriber, assistant: GeminiOrchestrator) -> None:
		self.websocket = websocket
		self.transcriber = transcriber
		self.assistant = assistant
		self.task = None

	async def __aenter__(self) -> _send_transcripts:
		import asyncio

		self.task = asyncio.create_task(self._send())
		return self

	async def __aexit__(self, exc_type: object, exc: object, traceback: object) -> None:
		self.task.cancel()

	async def _send(self) -> None:
		async for transcript in self.transcriber.receive_transcripts():
			result = await self.assistant.process(transcript.text)
			await self.websocket.send_json(
				{
					"type": "assistant_result",
					"transcript": transcript.text,
					"intent": result.intent,
					"response": result.response,
					"operations": result.operations,
					"report_path": result.report_path,
				}
			)
