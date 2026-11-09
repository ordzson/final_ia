"""Lógica pura del modo universitario: antiparpadeo, puntaje y ronda. Solo depende de config."""
from dataclasses import dataclass

import config


class PresenceTracker:
    """Quita el parpadeo de las detecciones: un objeto cuenta como presente si se ve de forma estable."""

    def __init__(self, enter_s: float = config.PRESENCE_ENTER_S,
                 hold_s: float = config.PRESENCE_HOLD_S) -> None:
        self.enter_s = enter_s
        self.hold_s = hold_s
        self.reset()

    def update(self, keys: set[str], now: float) -> tuple[set[str], set[str]]:
        """Devuelve (present, entered). entered = claves que pasaron de ausente a presente en esta llamada."""
        for k in keys:
            st = self._state.get(k)
            if st is None or now - st[1] > self.hold_s:
                # Comienza una racha nueva
                self._state[k] = [now, now]
            else:
                st[1] = now
        present = self.present(now)
        entered = present - self._prev_present
        self._prev_present = present
        # Olvida las rachas vencidas
        self._state = {k: st for k, st in self._state.items() if now - st[1] <= self.hold_s}
        return present, entered

    def present(self, now: float) -> set[str]:
        """Consulta las presencias vigentes sin añadir observaciones ni alterar las rachas."""
        return {
            k for k, (first, last) in self._state.items()
            if now - last <= self.hold_s and last - first >= self.enter_s
        }

    def reset(self) -> None:
        self._state: dict[str, list[float]] = {}  # clave → [first, last]
        self._prev_present: set[str] = set()


@dataclass
class UniState:
    score: int                # suma de los puntos de los ítems guardados en la ronda
    max_score: int            # suma de puntos de los UNI_ITEMS disponibles en el modelo
    level_text: str           # título del ítem guardado con más puntos; config.NO_ITEMS_TEXT si no hay ninguno
    badge: bool               # score >= config.UNI_THRESHOLD
    present: list[str]        # claves presentes ahora, en el orden de config.UNI_ITEMS
    entered: list[str]        # claves que se guardaron en este frame, en el orden de config.UNI_ITEMS
    collected: list[str]      # claves guardadas en la ronda, en el orden de config.UNI_ITEMS
    phase: str                # "waiting" (espera el primer objeto) | "running" | "result"
    time_left: float          # segundos que quedan de la ronda; al terminar queda congelado
    result_left: float        # en "result", segundos hasta volver a 0; si no, 0


class UniScorer:
    """Ronda de config.UNI_ROUND_S segundos. Arranca cuando entra el primer objeto; cada ítem queda
    guardado al verse de forma estable, aunque luego se retire. Termina al juntar todos o al acabarse
    el tiempo; el resultado se muestra config.UNI_RESULT_S segundos y se vuelve a 0 a esperar otra ronda."""

    def __init__(self, available_keys: set[str], *, live: bool = False) -> None:
        self.live = live
        items = config.UNI_LIVE_ITEMS if live else config.UNI_ITEMS
        self.items = {k: v for k, v in items.items() if k in available_keys}
        self.max_score = sum(points for _, points in self.items.values())
        self.tracker = PresenceTracker()
        self.reset()

    def update(self, keys: set[str], now: float) -> UniState:
        self._advance_time(now)
        present_set, entered_set = self.tracker.update(keys & self.items.keys(), now)
        if self.live:
            return self._snapshot(now, present_set, entered_set)
        # Solo un objeto que entra arranca la ronda: los que siguen a la vista desde la anterior no
        # la reinician solos (si no, con todo en cuadro las rondas se encadenarían sin fin)
        if self._phase == "waiting" and entered_set:
            self._phase, self._start = "running", now
        new: set[str] = set()
        if self._phase == "running":
            new = present_set - self._collected
            self._collected |= new
            if len(self._collected) == len(self.items):
                self._finish(now, config.UNI_ROUND_S - (now - self._start))
        return self._snapshot(now, present_set, new)

    def advance(self, now: float) -> UniState:
        """Avanza reloj y resultado sin un frame nuevo: no suma puntos ni cambia el tracker."""
        self._advance_time(now)
        return self._snapshot(now, self.tracker.present(now), set())

    def _advance_time(self, now: float) -> None:
        deadline = self._start + config.UNI_ROUND_S
        if self._phase == "running" and now >= deadline:
            # El resultado vence cinco segundos después del límite real, aunque no lleguen frames.
            self._finish(deadline, 0.0)
        if self._phase == "result" and now - self._end >= config.UNI_RESULT_S:
            self._phase, self._collected = "waiting", set()

    def _snapshot(self, now: float, present_set: set[str], new: set[str]) -> UniState:
        active = present_set if self.live else self._collected
        collected = [k for k in self.items if k in active]
        # Cada clave suma una sola vez, aunque haya varias detecciones de ella
        score = sum(self.items[k][1] for k in collected)
        if collected:
            # max() se queda con el primero en caso de empate (orden de UNI_ITEMS)
            best = max(collected, key=lambda k: self.items[k][1])
            level_text = self.items[best][0]
        else:
            level_text = config.NO_ITEMS_TEXT
        if self._phase == "running":
            time_left = config.UNI_ROUND_S - (now - self._start)
        elif self._phase == "result":
            time_left = self._left
        else:
            time_left = float(config.UNI_ROUND_S)
        return UniState(
            score=score,
            max_score=self.max_score,
            level_text=level_text,
            badge=score >= config.UNI_THRESHOLD,
            present=[k for k in self.items if k in present_set],
            entered=[k for k in self.items if k in new],
            collected=collected,
            phase=self._phase,
            time_left=time_left,
            result_left=config.UNI_RESULT_S - (now - self._end) if self._phase == "result" else 0.0,
        )

    def _finish(self, now: float, time_left: float) -> None:
        self._phase, self._end, self._left = "result", now, time_left

    def reset(self) -> None:
        self.tracker.reset()
        self._phase = "waiting"
        self._collected: set[str] = set()
        self._start = self._end = self._left = 0.0
