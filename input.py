from __future__ import annotations

import asyncio
import os
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import AsyncIterator

from deepgram import AsyncDeepgramClient


@dataclass(frozen=True, slots=True)
class Transcript:
	text: str
	is_final: bool = True


class DeepgramTranscriber:
	"""Own one Deepgram live session and expose final utterances to callers."""

	def __init__(self, api_key: str | None = None) -> None:
		self.api_key = api_key or os.getenv("DEEPGRAM_API_KEY", "dummy-api-key")
		self.transcripts: asyncio.Queue[Transcript | None] = asyncio.Queue()
		self.llm_queue: asyncio.Queue[Transcript] = asyncio.Queue()
		self._connection = None
		self._reader_task: asyncio.Task[None] | None = None

	@asynccontextmanager
	async def connect(self) -> AsyncIterator[DeepgramTranscriber]:
		client = AsyncDeepgramClient(api_key=self.api_key)
		async with client.listen.v2.connect(
			model="flux-general-en",
			encoding="linear16",
			sample_rate=16000,
		) as connection:
			self._connection = connection
			await connection.start_listening()
			self._reader_task = asyncio.create_task(self._read_transcripts())
			try:
				yield self
			finally:
				await self.close()

	async def send_audio(self, chunk: bytes) -> None:
		if self._connection is None:
			raise RuntimeError("Deepgram session is not connected")
		await self._connection.send_media(chunk)

	async def receive_transcripts(self) -> AsyncIterator[Transcript]:
		while True:
			transcript = await self.transcripts.get()
			if transcript is None:
				return
			yield transcript

	async def close(self) -> None:
		if self._connection is None:
			return
		self._connection = None
		if self._reader_task is not None:
			self._reader_task.cancel()
			await asyncio.gather(self._reader_task, return_exceptions=True)
			self._reader_task = None
		await self.transcripts.put(None)

	async def _read_transcripts(self) -> None:
		utterance: list[str] = []
		try:
			while self._connection is not None:
				message = await self._connection.recv()
				if not self._is_turn_info(message):
					continue
				text = str(getattr(message, "transcript", "") or "").strip()
				if text:
					utterance.append(text)
				if bool(getattr(message, "end_of_turn", False)) and utterance:
					transcript = Transcript(" ".join(utterance))
					await self.transcripts.put(transcript)
					await self.llm_queue.put(transcript)
					utterance.clear()
		except asyncio.CancelledError:
			raise
		finally:
			if self._connection is not None:
				await self.transcripts.put(None)

	@staticmethod
	def _is_turn_info(message: object) -> bool:
		return message.__class__.__name__ == "ListenV2TurnInfo"
