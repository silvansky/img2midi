# img2midi

Single-file Python CLI that converts images to MIDI.

## Layout

- `img2midi.py` — script + `main()` entry point
- `pyproject.toml` — packaging, exposes `img2midi` console script
- `requirements.txt` — runtime deps mirror

## Deps

`pillow`, `mido`, `numpy`. Use `.venv/bin/python` for local runs.

## Algorithm

1. Image → grayscale → tile into `block × block` cells (numpy reshape + mean).
2. Mean brightness → velocity via `brightness_to_velocity` (clamped 1–127, zero below `threshold`).
3. Row index → pitch from `scale_notes(key, scale)` (top row = highest pitch, 3 octaves from C3 by default).
4. `grid_to_events` walks each row left→right, merging runs of equal velocity into one note.
5. `write_midi` interleaves note_on/note_off, sorts by `(tick, off-before-on)`, writes delta times.

## Adding a scale

Append to `SCALES` dict. Auto block size divides height by `len(intervals) * 3`.

## Testing

No test suite. Manual verify: build a synthetic numpy image, run, read back with `mido.MidiFile` and inspect events.
