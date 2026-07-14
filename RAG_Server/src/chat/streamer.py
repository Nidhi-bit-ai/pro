import json
from queue import Queue, Empty
from threading import Thread

from .events import (
    status_event,
    final_event,
    error_event,
)


class ChatStreamer:

    def __init__(
        self,
        chat_service,
    ):

        self.chat_service = chat_service

    def stream(
        self,
        query: str,
    ):

        queue = Queue()

        def on_progress(
            stage: str,
            message: str,
        ):

            queue.put(
                status_event(
                    stage,
                    message,
                )
            )

        def worker():

            try:

                response = self.chat_service.chat(
                    query=query,
                    on_progress=on_progress,
                )

                queue.put(
                    final_event(
                        response.model_dump(),
                    )
                )

            except Exception as e:

                queue.put(
                    error_event(
                        str(e),
                    )
                )

            finally:

                queue.put(None)

        Thread(
            target=worker,
            daemon=True,
        ).start()

        while True:

            event = queue.get()

            if event is None:
                break

            yield (
                json.dumps(event)
                + "\n"
            )