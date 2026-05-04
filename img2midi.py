#!/usr/bin/env python3
import argparse
import sys
from fractions import Fraction
from pathlib import Path

import mido
import numpy as np
from PIL import Image

SCALES = {
    "major": [0, 2, 4, 5, 7, 9, 11],
    "minor": [0, 2, 3, 5, 7, 8, 10],
    "harmonic_minor": [0, 2, 3, 5, 7, 8, 11],
    "melodic_minor": [0, 2, 3, 5, 7, 9, 11],
    "pentatonic": [0, 2, 4, 7, 9],
    "pentatonic_minor": [0, 3, 5, 7, 10],
    "blues": [0, 3, 5, 6, 7, 10],
    "chromatic": list(range(12)),
    "dorian": [0, 2, 3, 5, 7, 9, 10],
    "phrygian": [0, 1, 3, 5, 7, 8, 10],
    "lydian": [0, 2, 4, 6, 7, 9, 11],
    "mixolydian": [0, 2, 4, 5, 7, 9, 10],
    "locrian": [0, 1, 3, 5, 6, 8, 10],
}

KEYS = {"C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3, "E": 4,
        "F": 5, "F#": 6, "Gb": 6, "G": 7, "G#": 8, "Ab": 8, "A": 9,
        "A#": 10, "Bb": 10, "B": 11}

OCTAVES = 3
BASE_OCTAVE = 3


def scale_notes(key, scale, octaves=OCTAVES, base=BASE_OCTAVE):
    intervals = SCALES[scale]
    root_midi = (base + 1) * 12 + KEYS[key]
    return [root_midi + o * 12 + i for o in range(octaves) for i in intervals]


def brightness_to_velocity(b, threshold=0.0):
    if b / 255 <= threshold:
        return 0
    return max(1, min(127, int(round(b * 127 / 255))))


def parse_args():
    p = argparse.ArgumentParser(description="Convert an image to a MIDI file.")
    p.add_argument("image", help="input image path")
    p.add_argument("-k", "--key", default="C", choices=list(KEYS),
                   help="musical key (default: C)")
    p.add_argument("-s", "--scale", default="major", choices=list(SCALES),
                   help="musical scale (default: major)")
    p.add_argument("-b", "--block-size", type=int, default=0,
                   help="block size in pixels (0 = auto, default)")
    p.add_argument("-n", "--note-length", default="1/8",
                   help="note length as fraction of whole note (default: 1/8)")
    p.add_argument("--bpm", type=int, default=120, help="tempo (default: 120)")
    p.add_argument("-t", "--threshold", type=float, default=0.01,
                   help="brightness fraction below which blocks are silent (default: 0.01)")
    p.add_argument("-o", "--output", default=None,
                   help="output MIDI path (default: <image>.mid)")
    return p.parse_args()


def build_grid(img, block, rows, cols):
    arr = np.asarray(img, dtype=np.float64)[:rows * block, :cols * block]
    return arr.reshape(rows, block, cols, block).mean(axis=(1, 3))


def grid_to_events(velocities, pitches, note_ticks):
    rows, cols = velocities.shape
    events = []
    for r in range(rows):
        pitch = pitches[rows - 1 - r]
        c = 0
        while c < cols:
            v = int(velocities[r, c])
            if v == 0:
                c += 1
                continue
            start = c
            while c + 1 < cols and int(velocities[r, c + 1]) == v:
                c += 1
            events.append((start * note_ticks, (c + 1) * note_ticks, pitch, v))
            c += 1
    return events


def write_midi(events, bpm, ticks_per_beat, path):
    mid = mido.MidiFile(ticks_per_beat=ticks_per_beat)
    track = mido.MidiTrack()
    mid.tracks.append(track)
    track.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(bpm)))

    msgs = []
    for s, e, p, v in events:
        msgs.append((s, 1, p, v))
        msgs.append((e, 0, p, v))
    msgs.sort(key=lambda m: (m[0], m[1]))

    last = 0
    for t, kind, p, v in msgs:
        dt = t - last
        last = t
        if kind:
            track.append(mido.Message("note_on", note=p, velocity=v, time=dt))
        else:
            track.append(mido.Message("note_off", note=p, velocity=0, time=dt))

    track.append(mido.MetaMessage("end_of_track", time=0))
    mid.save(path)


def main():
    args = parse_args()
    img = Image.open(args.image).convert("L")
    w, h = img.size

    pitches = scale_notes(args.key, args.scale)
    n_pitch = len(pitches)

    block = args.block_size or max(1, h // n_pitch)
    rows = h // block
    cols = w // block
    if rows == 0 or cols == 0:
        sys.exit("image too small for given block size")

    if rows > n_pitch:
        extra_oct = -(-rows // len(SCALES[args.scale]))
        pitches = scale_notes(args.key, args.scale, octaves=extra_oct)
    pitches = pitches[:rows]

    grid = build_grid(img, block, rows, cols)
    velocities = np.vectorize(lambda b: brightness_to_velocity(b, args.threshold))(grid).astype(int)

    ticks_per_beat = 480
    note_ticks = int(ticks_per_beat * 4 * Fraction(args.note_length))
    if note_ticks <= 0:
        sys.exit("note length must be positive")

    events = grid_to_events(velocities, pitches, note_ticks)
    out = args.output or str(Path(args.image).with_suffix(".mid"))
    write_midi(events, args.bpm, ticks_per_beat, out)

    print(f"wrote {out} ({len(events)} notes, grid {rows}x{cols}, block={block}px)")


if __name__ == "__main__":
    main()
