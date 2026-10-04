from __future__ import annotations

import queue
import threading
from dataclasses import dataclass
from typing import Callable

from logic_search.core.cancellation import CancellationToken
from logic_search.core.events import EventType, SearchEvent
from logic_search.search.solver import solve


@dataclass
class PlaybackState:
    running: bool = False
    paused: bool = False


class SearchController:
    def __init__(self) -> None:
        self.events: queue.Queue[SearchEvent] = queue.Queue(maxsize=1)
        self.state = PlaybackState()
        self._condition = threading.Condition()
        self._step_budget = 0
        self._token: CancellationToken | None = None
        self._thread: threading.Thread | None = None

    def start(self, problem, algorithm: str, timeout: float | None = None, *, paused: bool = False) -> None:
        self.cancel()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=0.5)
        while not self.events.empty():
            try:
                self.events.get_nowait()
            except queue.Empty:
                break
        token = CancellationToken()
        self._token = token
        self.state = PlaybackState(running=True, paused=paused)
        self._step_budget = 0

        def emit(event: SearchEvent) -> None:
            if event.type in {
                EventType.NODE_EXPANDED,
                EventType.CELL_DOMAIN,
                EventType.VALUE_TRIED,
                EventType.VALUE_REJECTED,
                EventType.NODE_PRUNED,
                EventType.BACKTRACK,
            }:
                with self._condition:
                    while self.state.paused and self._step_budget == 0 and not token.cancelled:
                        self._condition.wait(timeout=0.05)
                    if self._step_budget > 0:
                        self._step_budget -= 1
            if token.cancelled:
                return

            while not token.cancelled:
                try:
                    self.events.put(event, timeout=0.05)
                    break
                except queue.Full:
                    continue

        def worker() -> None:
            try:
                solve(problem, algorithm, timeout=timeout, cancellation=token, on_event=emit, detailed_events=True)
            except Exception as exc:
                try:
                    self.events.put(SearchEvent(EventType.ERROR, 0.0, message=str(exc)), timeout=0.2)
                except Exception:
                    pass
            finally:
                if self._token is token:
                    self.state.running = False

        self._thread = threading.Thread(target=worker, name="logic-search-worker", daemon=True)
        self._thread.start()

    def pause(self) -> None:
        with self._condition:
            self.state.paused = True
            self._condition.notify_all()

    def resume(self) -> None:
        with self._condition:
            self.state.paused = False
            self._condition.notify_all()

    def step(self) -> None:
        with self._condition:
            self.state.paused = True
            self._step_budget += 1
            self._condition.notify_all()

    def cancel(self) -> None:
        if self._token:
            self._token.cancel()
        with self._condition:
            self.state.running = False
            self.state.paused = False
            self._condition.notify_all()
        while not self.events.empty():
            try:
                self.events.get_nowait()
            except queue.Empty:
                break

    def poll(self, callback: Callable[[SearchEvent], None], limit: int = 1) -> None:
        for _ in range(limit):
            try:
                callback(self.events.get_nowait())
            except queue.Empty:
                break
