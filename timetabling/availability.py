"""Derive location start slots from approved opening intervals and closures."""
from __future__ import annotations
from .solver import SpaceVersion, Window


def merge_intervals(windows: tuple[Window, ...]) -> list[Window]:
    merged = []
    for window in sorted(windows, key=lambda w: w.start):
        if merged and window.start <= merged[-1].end:
            merged[-1] = Window(merged[-1].start, max(merged[-1].end, window.end))
        else:
            merged.append(window)
    return merged


def available_starts(space: SpaceVersion, horizon: Window, duration: int,
                     step: int = 5, preparation: int = 0, cleanup: int = 0,
                     grid_origin: int = 0) -> tuple[int, ...]:
    """No openings means no known availability. A blank PDF cell is not an opening."""
    if min(duration, step) <= 0 or min(preparation, cleanup) < 0:
        raise ValueError("Invalid slot duration, step or buffer")
    if not space.reviewed or space.state != "open":
        return ()
    free = []
    for opening in merge_intervals(space.openings):
        start = max(opening.start, horizon.start, space.valid.start)
        end = min(opening.end, horizon.end, space.valid.end)
        if start < end:
            free.append(Window(start, end))
    for blocked in merge_intervals(space.blocked):
        revised = []
        for window in free:
            if blocked.end <= window.start or blocked.start >= window.end:
                revised.append(window)
                continue
            if window.start < blocked.start:
                revised.append(Window(window.start, blocked.start))
            if blocked.end < window.end:
                revised.append(Window(blocked.end, window.end))
        free = revised
    starts = set()
    for window in free:
        earliest = window.start + preparation
        offset = -(-(earliest - grid_origin) // step)
        first = grid_origin + offset * step
        last = window.end - duration - cleanup
        starts.update(range(first, last + 1, step))
    return tuple(sorted(starts))
