# jazz-voicing-engine — Jazz Piano Voicing, Comping & Walking Bass

Generate intelligent jazz piano voicings with voice leading, comping patterns in the style of legendary pianists, and walking bass lines. Parse standard chord symbols, voice-lead them smoothly, and export to MIDI.

## Install

```bash
pip install jazz-voicing-engine
```

For MIDI export: `pip install jazz-voicing-engine[midi]`

## Quick Start

```python
from jazz_voicing_engine.voicings import ChordSymbol
from jazz_voicing_engine.generator import VoicingGenerator

gen = VoicingGenerator(style="rootless")
chords = [ChordSymbol.parse(c) for c in ["Cm7", "F7", "Bbmaj7", "Ebmaj7"]]
voicings = gen.voice_lead(chords)

for v in voicings:
    print(v.chord, v.pitches)
    # Cm7 [48, 51, 57, 60]
    # F7  [48, 53, 57, 60]  — minimal voice movement
    # ...
```

## The Key Idea

Jazz voicing isn't random — it's constraint satisfaction. Each voicing must:
1. Contain the chord's essential tones (3rd, 7th, any alterations)
2. Stay within a playable range for the pianist's hand
3. Minimize movement from the previous voicing (smooth voice leading)

The engine treats these as constraints and solves them the same way counterpoint-engine solves species counterpoint. The result: voicings that sound like a real jazz pianist made musical decisions, not a random generator.

## Features

- **Chord parsing** — `Cm7`, `G7alt`, `Dm7b5`, `F#maj7`, `Bb7#11`, etc.
- **Voicing styles** — drop-2, rootless, quartal, shell, guide tones
- **Voice leading** — minimizes semitone movement between consecutive chords
- **Comping patterns** — Bill Evans, Wynton Kelly, Herbie Hancock, Red Garland
- **Walking bass** — generates idiomatic walking bass lines
- **MIDI export** — optional export via `mido`

## API Reference

### ChordSymbol

```python
ChordSymbol.parse("Cm7")     # → ChordSymbol(root=0, quality="min7")
ChordSymbol.parse("G7alt")   # → ChordSymbol(root=7, quality="7alt")
symbol.root       # Pitch class 0-11
symbol.quality    # Quality string
symbol.extensions # Extension pitch classes
```

Supported: `maj7`, `min7`, `7`, `dim7`, `m7b5`, `7alt`, `sus4`, `aug7`, `min`, `maj`, `dim`, `aug` + extensions (9, 11, 13) and alterations (#5, b5, #9, b9, #11, b13).

### VoicingGenerator

```python
VoicingGenerator(style="rootless")  # rootless | drop2 | quartal | shell | guide
gen.voice_lead(chords)              # Smooth voice-led sequence
gen.generate_voicing("Cmaj7", register=4)
```

### CompingGenerator

```python
CompingGenerator(style="kelly")     # kelly | evans | hancock | garland
comp.generate(chords, measures=4)
```

### WalkingBassGenerator

```python
WalkingBassGenerator()
bass.generate(chords, measures=4)
```

## Documentation

- [User Guide](docs/USER-GUIDE.md) — Complete usage documentation
- [Developer Guide](docs/DEVELOPER-GUIDE.md) — Contributing and internals
- [Examples](examples/) — Full "Autumn Leaves" arrangement

## Related

- [counterpoint-engine](https://github.com/SuperInstance/counterpoint-engine) — Species counterpoint as constraint satisfaction
- [holonomy-harmony](https://github.com/SuperInstance/holonomy-harmony) — Chord progression analysis via holonomy
- [flux-tensor-midi](https://github.com/SuperInstance/flux-tensor-midi) — 4D tensor representation of MIDI events

## License

MIT
