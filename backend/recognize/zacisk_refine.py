"""Odzyskanie podtypu zacisku z kontekstu przestrzennego (po detekcji YOLO).

YOLO wykrywa jeden wizualny prymityw `zacisk` (terminal i zlaczka sa nierozroznialne).
Podtyp ustalamy regula zawierania:
    zacisk, ktorego srodek lezy wewnatrz `urzadzenie` (lub terminal_plc) -> terminal
    w przeciwnym razie                                                    -> zlaczka

Czysta geometria — dziala na wynikach detekcji, bez bazy. Domyslne kontenery
mozna nadpisac.
"""

from __future__ import annotations

from dataclasses import dataclass

ZACISK = "zacisk"
DEVICE_CONTAINERS = ("urzadzenie", "terminal_plc")


@dataclass
class Box:
    class_name: str
    x: float
    y: float
    width: float
    height: float

    @property
    def cx(self) -> float:
        return self.x + self.width / 2

    @property
    def cy(self) -> float:
        return self.y + self.height / 2


def _center_inside(inner: Box, outer: Box) -> bool:
    return (outer.x <= inner.cx <= outer.x + outer.width
            and outer.y <= inner.cy <= outer.y + outer.height)


def refine_zacisk(
    boxes: list[Box],
    device_containers: tuple[str, ...] = DEVICE_CONTAINERS,
    terminal_name: str = "terminal",
    zlaczka_name: str = "zlaczka",
) -> list[Box]:
    """Zwraca nowa liste z `zacisk` przemianowanym na terminal/zlaczka wg zawierania.

    Przy zagniezdzeniu wybiera NAJMNIEJSZY pasujacy kontener (najblizszy logicznie).
    """
    devices = [b for b in boxes if b.class_name in device_containers]
    out: list[Box] = []
    for b in boxes:
        if b.class_name != ZACISK:
            out.append(b)
            continue
        parents = [d for d in devices if _center_inside(b, d)]
        in_device = bool(parents)
        new_name = terminal_name if in_device else zlaczka_name
        out.append(Box(new_name, b.x, b.y, b.width, b.height))
    return out
