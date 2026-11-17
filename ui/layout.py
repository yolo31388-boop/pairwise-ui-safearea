"""Safe-area aware layout helpers for game UI.

Coordinate conventions
----------------------
* Every rectangle is ``(x, y, width, height)`` in device-independent pixels
  with the origin at the top-left of the screen.
* Safe-area insets are ``(left, top, right, bottom)`` -- the same edge order
  used by the platforms and by the test fixtures.
* Anchors are ``"<vertical>-<horizontal>"`` strings such as ``"top-left"``,
  ``"bottom-right"`` or ``"center"``.

All helpers are pure functions: they never read a cached resolution or a
stale safe area, so callers can recompute the layout whenever the safe area,
the orientation, the keyboard or the DPI changes.
"""

from __future__ import annotations

from typing import Optional, Sequence, Tuple

Rect = Tuple[float, float, float, float]
Insets = Tuple[float, float, float, float]
Point = Tuple[float, float]
Size = Tuple[float, float]

_HORIZONTAL_ANCHORS = {"left": 0.0, "center": 0.5, "centre": 0.5, "right": 1.0}
_VERTICAL_ANCHORS = {"top": 0.0, "center": 0.5, "centre": 0.5, "bottom": 1.0}


def _rect_parts(rect: Sequence[float]) -> Rect:
    if len(rect) != 4:
        raise ValueError("rect must be (x, y, width, height)")
    x, y, w, h = (float(value) for value in rect)
    return x, y, w, h


def safe_rect(rect: Sequence[float], insets: Sequence[float]) -> Rect:
    """Return *rect* shrunk by the safe-area *insets*.

    ``insets`` is ``(left, top, right, bottom)``; each inset trims the
    corresponding edge so content (health bars, HUD, buttons) never lands
    under a notch, punch-hole or rounded corner.  Negative insets are
    ignored and an over-large inset collapses the rect to zero size instead
    of producing a negative one.
    """
    x, y, w, h = _rect_parts(rect)
    if len(insets) != 4:
        raise ValueError("insets must be (left, top, right, bottom)")
    left, top, right, bottom = (max(0.0, float(value)) for value in insets)
    return (
        x + left,
        y + top,
        max(0.0, w - left - right),
        max(0.0, h - top - bottom),
    )


def _anchor_fraction(anchor: str) -> Point:
    tokens = anchor.strip().lower().replace("_", "-").split("-")
    if len(tokens) == 1:
        token = tokens[0]
        if token in _HORIZONTAL_ANCHORS:
            return _HORIZONTAL_ANCHORS[token], 0.5
        if token in _VERTICAL_ANCHORS:
            return 0.5, _VERTICAL_ANCHORS[token]
    elif len(tokens) == 2:
        first, second = tokens
        if first in _HORIZONTAL_ANCHORS and second in _VERTICAL_ANCHORS:
            return _HORIZONTAL_ANCHORS[first], _VERTICAL_ANCHORS[second]
        if first in _VERTICAL_ANCHORS and second in _HORIZONTAL_ANCHORS:
            return _HORIZONTAL_ANCHORS[second], _VERTICAL_ANCHORS[first]
    raise ValueError("unknown anchor: {!r}".format(anchor))


def anchor_position(
    anchor: str,
    rect: Sequence[float],
    size: Sequence[float],
    offset: Sequence[float] = (0.0, 0.0),
) -> Point:
    """Place a ``size`` box inside *rect* according to *anchor*.

    The anchor is resolved against the **safe** rect supplied by the
    caller, so a top-anchored health bar moves below the notch instead of
    using a raw screen percentage.  ``offset`` is applied after anchoring
    and is expressed in the same units (e.g. ``(-5, -5)`` nudges a
    bottom-right element inward by 5px).
    """
    x, y, w, h = _rect_parts(rect)
    if len(size) != 2:
        raise ValueError("size must be (width, height)")
    box_w, box_h = (float(value) for value in size)
    if len(offset) != 2:
        raise ValueError("offset must be (dx, dy)")
    dx, dy = (float(value) for value in offset)

    fraction_x, fraction_y = _anchor_fraction(anchor)
    return (
        x + (w - box_w) * fraction_x + dx,
        y + (h - box_h) * fraction_y + dy,
    )


def scale_font(
    base_px: float,
    dpi_scale: float,
    readability_scale: float = 1.0,
    max_px: Optional[float] = None,
) -> float:
    """Scale a design-time font size for the current display.

    ``base_px`` is the size authored at 1x.  ``dpi_scale`` is the device
    pixel ratio; values below 1 are clamped to 1 so text never becomes
    smaller than authored (the original bug: hard-coded px made tablet
    buttons too small to tap).  ``readability_scale`` lets the user enlarge
    text via accessibility settings, and ``max_px`` caps the result for
    oversized displays.
    """
    base = float(base_px)
    if base <= 0:
        raise ValueError("base_px must be positive")

    effective_scale = max(1.0, float(dpi_scale)) * max(1.0, float(readability_scale))
    scaled = base * effective_scale
    if max_px is not None:
        scaled = min(scaled, float(max_px))
    return round(scaled, 2)


def reflow(rect: Sequence[float], orientation: str) -> Rect:
    """Recompute a layout rect for *orientation*.

    Layouts are authored portrait-first.  Entering landscape swaps the
    width and height instead of reusing the cached resolution, which is
    what previously shifted the whole UI after a rotation.  Callers are
    expected to invoke this again on every orientation change.
    """
    x, y, w, h = _rect_parts(rect)
    key = orientation.strip().lower()
    if key in ("landscape", "horizontal", "rotated"):
        return (x, y, h, w)
    if key in ("portrait", "vertical", "natural"):
        return (x, y, w, h)
    raise ValueError("unknown orientation: {!r}".format(orientation))


def ellipsize(text: str, max_chars: int, ellipsis: str = "...") -> str:
    """Truncate *text* to at most *max_chars* characters.

    The ellipsis is counted inside the budget, so long translations
    (German, Russian, ...) cannot overflow a button.  When the budget is
    too small even for the ellipsis itself the result is dots only.
    """
    if max_chars is None:
        return text
    budget = int(max_chars)
    if budget <= 0:
        return ""
    if len(text) <= budget:
        return text
    if budget <= len(ellipsis):
        return ellipsis[:budget]
    return text[: budget - len(ellipsis)] + ellipsis


def avoid_keyboard(
    rect: Sequence[float],
    keyboard_height: float,
    screen_height: float,
) -> Rect:
    """Trim *rect* so it stays above the on-screen keyboard.

    ``keyboard_height`` is measured from the bottom edge of a
    ``screen_height``-tall screen.  When the keyboard is hidden (height 0)
    the rect is returned unchanged.  This keeps input fields visible even
    though the keyboard and the safe area overlap at the bottom.
    """
    x, y, w, h = _rect_parts(rect)
    keyboard = max(0.0, float(keyboard_height))
    if keyboard <= 0:
        return (x, y, w, h)

    keyboard_top = max(0.0, float(screen_height) - keyboard)
    visible_bottom = min(y + h, keyboard_top)
    return (x, y, w, max(0.0, visible_bottom - y))
