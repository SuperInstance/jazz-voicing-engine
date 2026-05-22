# jazz-voicing-engine 🎹

A Python library for generating jazz piano voicings with intelligent voice leading,
comping patterns in the style of legendary pianists, and walking bass lines.

## Features

- **Chord parsing** — `Cm7`, `G7alt`, `Dm7b5`, `F#maj7`, `Bb7#11`, etc.
- **Voicing styles** — drop-2, rootless, quartal, shell, guide tones
- **Voice leading** — minimizes semitone movement between consecutive chords
- **Comping patterns** — Bill Evans, Wynton Kelly, Herbie Hancock, Red Garland, and more
- **Walking bass** — generates idiomatic walking bass lines
- **MIDI export** — optional export via `mido`

## Install

```bash
pip install -e ".[midi]"
```

## Quick Start

```python
from jazz_voicing_engine.voicings import ChordSymbol
from jazz_voicing_engine.generator import VoicingGenerator

gen = VoicingGenerator(style="rootless")
chords = [ChordSymbol.parse(c) for c in ["Cm7", "F7", "Bbmaj7", "Ebmaj7"]]
voicings = gen.voice_lead(chords)

for v in voicings:
    print(v.chord, v.pitches)
```

See `examples/jazz_arrangement.py` for a full "Autumn Leaves" arrangement.

## License

MIT
