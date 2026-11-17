import pytest

from ui.layout import (
    safe_rect,
    anchor_position,
    scale_font,
    reflow,
    ellipsize,
    avoid_keyboard
)


def test_safe_top():
    assert safe_rect((0.0, 0.0, 100.0, 100.0), (10.0, 0.0, 0.0, 0.0)) == (10.0, 0.0, 90.0, 100.0)

def test_safe_bottom():
    assert safe_rect((0.0, 0.0, 100.0, 100.0), (0.0, 0.0, 0.0, 10.0)) == (0.0, 0.0, 100.0, 90.0)

def test_safe_zero():
    assert safe_rect((0.0, 0.0, 100.0, 100.0), (0.0, 0.0, 0.0, 0.0)) == (0.0, 0.0, 100.0, 100.0)

def test_anchor_center():
    assert anchor_position('center', (0.0, 0.0, 100.0, 100.0), (20.0, 20.0), (0.0, 0.0)) == (40.0, 40.0)

def test_anchor_top_left():
    assert anchor_position('top-left', (0.0, 0.0, 100.0, 100.0), (20.0, 20.0), (0.0, 0.0)) == (0.0, 0.0)

def test_anchor_bottom_right():
    assert anchor_position('bottom-right', (0.0, 0.0, 100.0, 100.0), (20.0, 20.0), (-5.0, -5.0)) == (75.0, 75.0)

def test_font_dpi1():
    assert scale_font(12.0, 1.0) == 12

def test_font_dpi2():
    assert scale_font(12.0, 2.0) == 24

def test_font_min():
    assert scale_font(12.0, 0.1) == 12

def test_reflow_landscape():
    assert reflow((0.0, 0.0, 100.0, 50.0), 'landscape') == (0.0, 0.0, 50.0, 100.0)

def test_reflow_portrait():
    assert reflow((0.0, 0.0, 100.0, 50.0), 'portrait') == (0.0, 0.0, 100.0, 50.0)

def test_ellipsize_long():
    assert ellipsize('abcdef', 5) == 'ab...'

def test_ellipsize_short():
    assert ellipsize('abc', 5) == 'abc'

def test_keyboard_avoid():
    assert avoid_keyboard((0.0, 0.0, 100.0, 100.0), 30.0, 100.0) == (0.0, 0.0, 100.0, 70.0)

def test_keyboard_zero():
    assert avoid_keyboard((0.0, 0.0, 100.0, 100.0), 0.0, 100.0) == (0.0, 0.0, 100.0, 100.0)
