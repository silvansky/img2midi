# img2midi

Convert images to MIDI files. Brightness becomes velocity, Y-coordinate becomes pitch.

## Install

```sh
pip install -e .
```

## Usage

```sh
img2midi <image> [options]
```

| flag | default | description |
|------|---------|-------------|
| `-k, --key` | `C` | musical key (C, C#, Db, D, ..., B) |
| `-s, --scale` | `major` | scale name (see below) |
| `-b, --block-size` | auto | block size in pixels (`0` = auto) |
| `-n, --note-length` | `1/8` | note length as fraction of whole note |
| `--bpm` | `120` | tempo |
| `-t, --threshold` | `0.01` | brightness fraction below which a block is silent |
| `-o, --output` | `<image>.mid` | output path |
| `--base-octave` | auto | lowest octave (auto-fits to MIDI range, prefers `3`) |

Auto block size divides image height into 3 octaves of the chosen scale.

## Scales

`major`, `minor`, `harmonic_minor`, `melodic_minor`, `pentatonic`, `pentatonic_minor`, `blues`, `chromatic`, `dorian`, `phrygian`, `lydian`, `mixolydian`, `locrian`

## Behavior

- Image is converted to grayscale and split into `block × block` cells.
- Each cell's mean brightness maps to MIDI velocity (1–127).
- Cells at or below `threshold` produce no note.
- Top of image = highest pitch; pitches are picked from `key` + `scale`, spanning 3 octaves up from C3.
- Consecutive cells in the same row with identical velocity merge into one longer note.

## Examples

```sh
img2midi photo.jpg
img2midi photo.jpg -k D -s pentatonic -n 1/16 --bpm 140
img2midi photo.jpg -b 20 -t 0.05 -o out.mid
```
