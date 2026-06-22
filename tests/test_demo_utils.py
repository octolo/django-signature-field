"""Tests for demo size parsing."""

from tests.app.demo_utils import (
    DEMO_PRESETS,
    MIN_INITIALS_SIZE,
    initials_size_for_signature,
    parse_initials_size,
    parse_size,
    signature_area,
)


def test_parse_size_reads_width_and_height() -> None:
    assert parse_size("320x200", (0, 0)) == (320, 200)
    assert parse_size("50x50", (0, 0)) == (50, 50)


def test_parse_initials_size_never_below_minimum() -> None:
    assert parse_initials_size("50x50", (0, 0)) == MIN_INITIALS_SIZE
    assert parse_initials_size("80x120", (0, 0)) == (100, 120)
    assert parse_initials_size("120x80", (0, 0)) == (120, 100)
    assert parse_initials_size("140x140", (0, 0)) == (140, 140)


def test_initials_size_scales_with_signature() -> None:
    assert initials_size_for_signature("240x120") == "100x100"
    assert initials_size_for_signature("320x160") == "100x100"
    assert initials_size_for_signature("400x200") == "125x125"
    assert initials_size_for_signature("520x240") == "162x162"


def test_demo_presets_are_sorted_by_signature_area() -> None:
    areas = [signature_area(preset["signature"]) for preset in DEMO_PRESETS]
    assert areas == sorted(areas)
    assert DEMO_PRESETS[0]["label"] == "Small"
    assert DEMO_PRESETS[-1]["label"] == "Wide"


def test_parse_size_falls_back_on_invalid_values() -> None:
    assert parse_size("bad", (320, 160)) == (320, 160)
    assert parse_size("10x10", (320, 160)) == (320, 160)
