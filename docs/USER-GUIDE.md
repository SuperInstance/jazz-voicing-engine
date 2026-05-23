# User Guide — jazz-voicing-engine

Jazz piano voicing, comping patterns, and walking bass line generation.

## Installation

```bash
pip install jazz-voicing-engine
```

Requires Python 3.10+.

## Chord Parsing

The engine parses standard jazz chord symbols:

```python
from jazz_voicing_engine.voicings import ChordSymbol

# Major 7th
cmaj7 = ChordSymbol.parse("Cmaj7")
print(cmaj7.root)      # 0 (C)
print(cmaj7.quality)   # "maj7"

# Minor 7th with alterations
g7alt = ChordSymbol.parse("G7alt")
dm7b5 = ChordSymbol.parse("Dm7b5")

# Complex chords
bb7s11 = ChordSymbol.parse("Bb7#11")
fsharp_maj7 = ChordSymbol.parse("F#maj7")
```

Supported qualities: `maj7`, `min7`, `7`, `dim7`, `m7b5`, `7alt`, `sus4`, `aug7`, `min`, `maj`, `dim`, `aug`.

Extensions: 9, 11, 13 are automatically mapped to their pitch-class equivalents.

## Voicing Generation

```python
from jazz_voicing_engine.voicings import VoicingGenerator

gen = VoicingGenerator()

# Generate a voicing for Cmaj7 in a specific register
voicing = gen.generate_voicing("Cmaj7", register=4)  # 4th octave area
print(voicing.notes)  # List of MIDI pitch numbers
```

## Comping Patterns

Generate rhythmic comping patterns in the style of legendary pianists:

```python
from jazz_voicing_engine.comping import CompingGenerator

comp = CompingGenerator(style="kelly")  # Wynton Kelly style
pattern = comp.generate(chords=["Cmaj7", "Am7", "Dm7", "G7"], measures=4)
```

## Walking Bass Lines

```python
from jazz_voicing_engine.walking_bass import WalkingBassGenerator

bass = WalkingBassGenerator()
line = bass.generate(chords=["Cmaj7", "Am7", "Dm7", "G7"], measures=4)
for note in line:
    print(f"Beat {note.beat}: {note.pitch} (duration: {note.duration})")
```

## Full Arrangement

Generate a complete piano arrangement with melody, voicings, and bass:

```python
from jazz_voicing_engine import generate_arrangement

arrangement = generate_arrangement(
    chords=["Cmaj7", "Am7", "Dm7", "G7", "Cmaj7"],
    melody=[60, 64, 67, 72, 71],  # MIDI pitches
    style="evans",  # Bill Evans style
)
arrangement.export("output.mid")
```

See `examples/jazz_arrangement.py` for a complete working demo.

## API Reference

### ChordSymbol

| Method | Returns | Description |
|--------|---------|-------------|
| `ChordSymbol.parse(symbol)` | `ChordSymbol` | Parse "Cm7", "G7alt", etc. |
| `.root` | `int` | Pitch class (0-11) |
| `.quality` | `str` | Chord quality string |
| `.extensions` | `list[int]` | Extension pitch classes |

### VoicingGenerator

| Method | Returns | Description |
|--------|---------|-------------|
| `.generate_voicing(chord, register=4)` | `Voicing` | Generate a piano voicing |
| `.voice_lead(prev, current)` | `Voicing` | Smooth voice leading between chords |

### CompingGenerator

| Method | Returns | Description |
|--------|---------|-------------|
| `.generate(chords, measures)` | `CompingPattern` | Rhythmic comping pattern |

### WalkingBassGenerator

| Method | Returns | Description |
|--------|---------|-------------|
| `.generate(chords, measures)` | `BassLine` | Walking bass line |
