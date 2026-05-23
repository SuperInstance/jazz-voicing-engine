# Developer Guide — jazz-voicing-engine

## Architecture

```
jazz_voicing_engine/
├── __init__.py       # Public API (generate_arrangement)
├── voicings.py       # ChordSymbol parser, VoicingGenerator
├── comping.py        # CompingGenerator — rhythmic comping patterns
├── generator.py      # Arrangement orchestration
└── walking_bass.py   # WalkingBassGenerator
```

### Chord Parsing

The parser handles standard jazz chord symbols using regex matching:
- Root: accidentals (#, b) mapped to pitch classes
- Quality: matched against `QUALITY_INTERVALS` dictionary
- Extensions (9, 11, 13) and alterations (#5, b9, #11, etc.) applied on top

### Voice Leading

Voice leading minimizes total semitone movement between consecutive voicings. The algorithm:
1. Generates candidate voicings for each chord
2. Scores each transition by total voice distance
3. Selects the smoothest path

### Comping Styles

Each pianist style is defined by characteristic rhythmic patterns, register preferences, and chord substitution tendencies.

## Contributing

```bash
git clone https://github.com/SuperInstance/jazz-voicing-engine.git
cd jazz-voicing-engine
pip install -e .
pytest tests/ -v
```

### Adding a New Comping Style

1. Define rhythmic patterns (onset grid per measure)
2. Add register/voicing preferences
3. Register the style name in `CompingGenerator`
4. Add tests demonstrating the style

### Code Style

- Type hints on all public methods
- Pure Python — no C extensions
- MIDI output via `mido` (if available) or raw bytes
