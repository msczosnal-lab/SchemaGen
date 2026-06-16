"""Test odzyskiwania podtypu zacisku z zawierania."""

from backend.recognize.zacisk_refine import Box, refine_zacisk


def test_zacisk_inside_device_becomes_terminal():
    boxes = [
        Box("urzadzenie", 0, 0, 100, 100),
        Box("zacisk", 10, 10, 5, 5),    # w urzadzeniu -> terminal
        Box("zacisk", 500, 500, 5, 5),  # poza -> zlaczka
    ]
    out = refine_zacisk(boxes)
    names = [b.class_name for b in out]
    assert names == ["urzadzenie", "terminal", "zlaczka"]


def test_non_zacisk_untouched():
    boxes = [Box("motor", 0, 0, 10, 10), Box("terminal_plc", 0, 0, 50, 50),
             Box("zacisk", 5, 5, 2, 2)]
    out = refine_zacisk(boxes)
    assert out[0].class_name == "motor"
    assert out[1].class_name == "terminal_plc"
    assert out[2].class_name == "terminal"  # w terminal_plc (device container)
