"""Tests de scoring.py. Ejecutar con: .venv/bin/python tests/test_scoring.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config
from scoring import PresenceTracker, UniScorer

STEP = 0.05
ALL_UNI = set(config.UNI_ITEMS)
ROUND = config.UNI_ROUND_S
RESULT = config.UNI_RESULT_S


def t(i: int) -> float:
    """Tiempo simulado del paso i (evita acumular error de punto flotante)."""
    return round(i * STEP, 4)


def run(tracker, frames):
    """frames: lista de (i, keys). Devuelve {i: (present, entered)}."""
    return {i: tracker.update(keys, t(i)) for i, keys in frames}


def test_no_keys():
    scorer = UniScorer(ALL_UNI)
    for i in range(20):
        s = scorer.update(set(), t(i))
    assert s.score == 0
    assert s.level_text == config.NO_ITEMS_TEXT
    assert s.badge is False
    assert s.present == [] and s.entered == []


def test_enter_delay_and_single_entered():
    tracker = PresenceTracker()
    out = run(tracker, [(i, {"laptop"}) for i in range(41)])  # 0.00 … 2.00 s
    assert "laptop" not in out[5][0]   # t = 0.25
    assert "laptop" in out[7][0]       # t = 0.35
    entered_count = sum("laptop" in entered for _, entered in out.values())
    assert entered_count == 1, entered_count

    # Lo mismo visto desde UniScorer
    scorer = UniScorer(ALL_UNI)
    states = [scorer.update({"laptop"}, t(i)) for i in range(41)]
    assert states[5].score == 0 and states[7].score == config.UNI_ITEMS["laptop"][1]
    assert sum(s.entered.count("laptop") for s in states) == 1


def test_gaps():
    tracker = PresenceTracker()
    # Visto de 0.00 a 1.00 s → presente
    out = run(tracker, [(i, {"laptop"}) for i in range(21)])
    assert "laptop" in out[20][0]
    # Hueco de 0.5 s (1.05 … 1.45) → sigue presente todo el hueco
    out = run(tracker, [(i, set()) for i in range(21, 30)])
    assert all("laptop" in present for present, _ in out.values())
    # Reaparece en 1.50 s: misma racha, sigue presente y no vuelve a "entrar"
    out = run(tracker, [(i, {"laptop"}) for i in range(30, 41)])  # 1.50 … 2.00
    assert all("laptop" in present for present, _ in out.values())
    assert not any("laptop" in entered for _, entered in out.values())

    # Hueco de 0.8 s (2.05 … 2.75): presente a 0.65 s del último visto, ausente a 0.75 s
    out = run(tracker, [(i, set()) for i in range(41, 56)])
    assert "laptop" in out[53][0]       # t = 2.65
    assert "laptop" not in out[55][0]   # t = 2.75
    # Reaparece en 2.80 s: necesita otros 0.3 s
    out = run(tracker, [(i, {"laptop"}) for i in range(56, 70)])
    assert "laptop" not in out[56][0]   # t = 2.80
    assert "laptop" not in out[61][0]   # t = 3.05 (+0.25)
    assert "laptop" in out[63][0]       # t = 3.15 (+0.35)
    assert sum("laptop" in entered for _, entered in out.values()) == 1


def test_three_items_badge():
    scorer = UniScorer(ALL_UNI)
    keys = {"backpack", "book", "laptop"}
    for i in range(20):
        s = scorer.update(keys, t(i))
    assert s.score == 55, s.score
    assert s.badge is True
    assert s.level_text == "Listo para el aula"
    assert s.present == [k for k in config.UNI_ITEMS if k in keys]  # orden de UNI_ITEMS


def test_max_score_reduced():
    full = UniScorer(ALL_UNI)
    assert full.update(set(), 0.0).max_score == sum(p for _, p in config.UNI_ITEMS.values())
    available = {"backpack", "laptop", "person"}  # "person" no es ítem universitario
    s = UniScorer(available).update(set(), 0.0)
    assert s.max_score == config.UNI_ITEMS["backpack"][1] + config.UNI_ITEMS["laptop"][1] == 35


def test_unavailable_key_ignored():
    scorer = UniScorer({"backpack", "laptop"})
    for i in range(20):
        s = scorer.update({"backpack", "book", "person"}, t(i))
    assert s.present == ["backpack"]
    assert s.score == config.UNI_ITEMS["backpack"][1]
    assert s.level_text == config.UNI_ITEMS["backpack"][0]


def test_reset():
    scorer = UniScorer(ALL_UNI)
    for i in range(20):
        s = scorer.update({"backpack", "book", "laptop"}, t(i))
    assert s.score > 0
    scorer.reset()
    s = scorer.update(set(), t(20))
    assert s.score == 0 and s.present == [] and s.entered == [] and s.collected == []
    assert s.level_text == config.NO_ITEMS_TEXT and s.badge is False
    assert s.phase == "waiting" and s.time_left == ROUND
    # Tras el reset, un objeto vuelve a necesitar 0.3 s estable
    s = scorer.update({"laptop"}, t(21))
    assert s.score == 0
    for i in range(22, 30):
        s = scorer.update({"laptop"}, t(i))
    assert s.present == ["laptop"]


def test_accumulates_one_by_one():
    """Cada ítem queda guardado aunque se retire: se pueden mostrar uno a uno."""
    scorer = UniScorer(ALL_UNI)
    s = scorer.update(set(), t(0))
    assert s.phase == "waiting" and s.time_left == ROUND
    for i in range(0, 21):  # laptop de 0.00 a 1.00 s: entra en 0.30 y arranca la ronda
        s = scorer.update({"laptop"}, t(i))
    assert s.phase == "running" and s.collected == ["laptop"]
    assert ROUND - 1 < s.time_left < ROUND
    for i in range(21, 60):  # nada de 1.05 a 2.95 s
        s = scorer.update(set(), t(i))
    assert s.present == [] and s.collected == ["laptop"] and s.score == 25
    entered = []
    for i in range(60, 81):  # libro de 3.00 a 4.00 s
        s = scorer.update({"book"}, t(i))
        entered += s.entered
    assert entered == ["book"]
    assert s.collected == ["book", "laptop"]  # orden de UNI_ITEMS
    assert s.present == ["book"]
    assert s.score == 45 and s.level_text == "Listo para el aula" and s.badge is False


def test_round_timeout():
    """Al acabarse el tiempo se congela el puntaje, se muestra el resultado y luego vuelve a 0."""
    scorer = UniScorer(ALL_UNI)
    start = t(6)  # la laptop se vuelve estable en 0.30 s: ahí arranca la ronda
    end_i = round((start + ROUND) / STEP)
    states = {}
    for i in range(end_i + round((RESULT + 1) / STEP)):
        now = t(i)
        if now <= 2:
            keys = {"laptop"}
        elif start + ROUND + 0.7 <= now <= start + ROUND + 1.7:
            keys = {"book"}  # aparece durante el resultado
        else:
            keys = set()
        states[i] = scorer.update(keys, now)
    assert states[end_i - 1].phase == "running" and states[end_i - 1].time_left > 0
    s = states[end_i + 1]
    assert s.phase == "result" and s.time_left == 0 and s.score == 25
    assert 0 < s.result_left <= RESULT
    # El libro que aparece con la ronda terminada no suma
    s = states[end_i + round(1.7 / STEP)]
    assert s.present == ["book"] and s.collected == ["laptop"] and s.score == 25
    # Pasado UNI_RESULT_S vuelve a 0 y espera otra ronda
    s = states[end_i + round((RESULT + 0.1) / STEP)]
    assert s.phase == "waiting" and s.score == 0 and s.collected == [] and s.time_left == ROUND
    assert s.level_text == config.NO_ITEMS_TEXT and s.badge is False and s.result_left == 0


def test_complete_ends_early():
    """Con todos los ítems la ronda termina antes y el tiempo que sobró queda congelado."""
    scorer = UniScorer(ALL_UNI)
    entered = []
    for i in range(0, 41):  # laptop de 0.00 a 2.00 s: la ronda arranca en 0.30
        s = scorer.update({"laptop"}, t(i))
        entered += s.entered
    for i in range(60, 81):  # los cuatro de 3.00 a 4.00 s: se completa en 3.30
        s = scorer.update(ALL_UNI, t(i))
        entered += s.entered
    assert sorted(entered) == sorted(ALL_UNI)  # cada ítem se guarda una sola vez
    assert s.phase == "result" and s.score == s.max_score and s.badge is True
    # Entra en 3.30 o 3.35 s según el redondeo de 3.30 - 3.00: margen de un paso
    left = s.time_left
    assert ROUND - 3.0 - STEP - 1e-9 <= left <= ROUND - 3.0
    for i in range(81, 100):  # el tiempo sigue congelado durante el resultado
        s = scorer.update(set(), t(i))
    assert s.phase == "result" and s.time_left == left


def test_no_chained_rounds():
    """Tras el resultado, los objetos que siguen a la vista no arrancan otra ronda; uno que entra, sí."""
    scorer = UniScorer(ALL_UNI)
    last = round((0.30 + RESULT + 1) / STEP)  # se completa en 0.30 s y el resultado dura RESULT
    for i in range(last + 1):
        s = scorer.update(ALL_UNI, t(i))
    assert s.phase == "waiting" and s.score == 0
    # Se retira la laptop más de PRESENCE_HOLD_S: sigue esperando
    gap = round((config.PRESENCE_HOLD_S + 0.2) / STEP)
    for i in range(last + 1, last + 1 + gap):
        s = scorer.update(ALL_UNI - {"laptop"}, t(i))
    assert s.phase == "waiting"
    # Vuelve la laptop: arranca una ronda y, con los otros tres a la vista, se completa enseguida
    for i in range(last + 1 + gap, last + 1 + gap + 10):
        s = scorer.update(ALL_UNI, t(i))
    assert s.phase == "result" and s.score == s.max_score


def test_clock_without_new_observations():
    """Consultar el reloj no estabiliza detecciones ni reinicia la racha entre frames reales."""
    scorer = UniScorer(ALL_UNI)
    scorer.update({"laptop"}, 0.0)
    for now in (0.1, 0.2, 0.35):
        s = scorer.advance(now)
        assert s.phase == "waiting" and s.score == 0 and s.entered == []
    # El segundo frame sí completa la racha original: las consultas no la borraron.
    s = scorer.update({"laptop"}, 0.35)
    assert s.phase == "running" and s.score == 25 and s.entered == ["laptop"]
    for now in (0.4, 0.5, 0.6):
        s = scorer.advance(now)
        assert s.score == 25 and s.entered == []
    s = scorer.update({"laptop"}, 0.65)
    assert s.score == 25 and s.entered == []


def test_clock_expires_round_without_frames():
    """Sin cámara, la ronda vence a su hora y el resultado conserva solo sus cinco segundos."""
    scorer = UniScorer(ALL_UNI)
    scorer.update({"laptop"}, 0.0)
    scorer.update({"laptop"}, 0.35)
    deadline = 0.35 + ROUND
    s = scorer.advance(deadline - 1)
    assert s.phase == "running" and s.time_left == 1 and s.score == 25
    assert s.present == [] and s.entered == []
    s = scorer.advance(deadline + 2)
    assert s.phase == "result" and s.time_left == 0 and s.score == 25
    assert abs(s.result_left - (RESULT - 2)) < 1e-9 and s.entered == []
    s = scorer.advance(deadline + RESULT + 0.1)
    assert s.phase == "waiting" and s.score == 0 and s.collected == []
    assert s.time_left == ROUND and s.result_left == 0


def test_long_gap_does_not_extend_result():
    """Un bloqueo largo salta a espera si ya vencieron tanto la ronda como el resultado."""
    for use_clock in (True, False):
        scorer = UniScorer(ALL_UNI)
        scorer.update({"laptop"}, 0.0)
        scorer.update({"laptop"}, 0.35)
        now = 0.35 + ROUND + RESULT + 10
        # Cubre el temporizador y el primer frame al reconectar sin consultas intermedias.
        s = scorer.advance(now) if use_clock else scorer.update(set(), now)
        assert s.phase == "waiting" and s.score == 0 and s.collected == []
        assert s.time_left == ROUND and s.result_left == 0 and s.entered == []


def test_no_points_after_deadline():
    """Un objeto que se vuelve estable después del límite no se guarda en la ronda vencida."""
    scorer = UniScorer(ALL_UNI)
    scorer.update({"laptop"}, 0.0)
    scorer.update({"laptop"}, 0.35)
    deadline = 0.35 + ROUND
    scorer.update({"book"}, deadline - 0.2)
    scorer.advance(deadline + 0.1)
    s = scorer.update({"book"}, deadline + 0.2)
    assert s.phase == "result" and s.present == ["book"]
    assert s.collected == ["laptop"] and s.score == 25 and s.entered == []


def test_interleaved_clock_does_not_chain_rounds():
    """El reloj del panel entre frames no provoca dobles ingresos ni encadena rondas completas."""
    scorer = UniScorer(ALL_UNI)
    entered = []
    for i in range(round((RESULT + 2) / STEP)):
        now = t(i)
        s = scorer.update(ALL_UNI, now)
        entered += s.entered
        s = scorer.advance(now + STEP / 2)
        assert s.entered == []
    assert sorted(entered) == sorted(ALL_UNI)
    assert s.phase == "waiting" and s.score == 0


def test_reconnect_requires_fresh_presence():
    """Tras un hueco sin frames, conservar los puntos no concede estabilidad a un objeto nuevo."""
    scorer = UniScorer(ALL_UNI)
    scorer.update({"laptop"}, 0.0)
    scorer.update({"laptop"}, 0.35)
    s = scorer.advance(10.0)
    assert s.score == 25 and s.present == [] and s.entered == []
    for now in (10.0, 10.25):
        s = scorer.update({"book"}, now)
        assert s.score == 25 and s.entered == []
    s = scorer.update({"book"}, 10.35)
    assert s.score == 45 and s.entered == ["book"]
    assert abs(s.time_left - (ROUND - 10)) < 1e-9


if __name__ == "__main__":
    test_no_keys()
    test_enter_delay_and_single_entered()
    test_gaps()
    test_three_items_badge()
    test_max_score_reduced()
    test_unavailable_key_ignored()
    test_reset()
    test_accumulates_one_by_one()
    test_round_timeout()
    test_complete_ends_early()
    test_no_chained_rounds()
    test_clock_without_new_observations()
    test_clock_expires_round_without_frames()
    test_long_gap_does_not_extend_result()
    test_no_points_after_deadline()
    test_interleaved_clock_does_not_chain_rounds()
    test_reconnect_requires_fresh_presence()
    print("OK")
