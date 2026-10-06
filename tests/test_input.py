import asyncio

import pytest

from input import DeepgramTranscriber


class ListenV2TurnInfo:
    def __init__(self, transcript: str, end_of_turn: bool) -> None:
        self.transcript = transcript
        self.end_of_turn = end_of_turn


class FakeConnection:
    def __init__(self) -> None:
        self.messages = asyncio.Queue()

    async def recv(self) -> ListenV2TurnInfo:
        return await self.messages.get()


@pytest.mark.asyncio
async def test_final_turn_is_accumulated_for_client_and_llm() -> None:
    transcriber = DeepgramTranscriber(api_key="dummy")
    connection = FakeConnection()
    transcriber._connection = connection
    reader = asyncio.create_task(transcriber._read_transcripts())

    await connection.messages.put(ListenV2TurnInfo("hello", False))
    await connection.messages.put(ListenV2TurnInfo("world", True))

    transcript = await asyncio.wait_for(transcriber.transcripts.get(), timeout=1)
    queued_for_llm = await asyncio.wait_for(transcriber.llm_queue.get(), timeout=1)

    assert transcript is not None
    assert transcript.text == "hello world"
    assert queued_for_llm.text == "hello world"

    reader.cancel()
    await asyncio.gather(reader, return_exceptions=True)
