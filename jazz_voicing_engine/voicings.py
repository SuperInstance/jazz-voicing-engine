"""Chord symbols, voicing data structures, and MIDI event generation."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

# ---------------------------------------------------------------------------
# Note-name helpers
# ---------------------------------------------------------------------------

NOTE_NAMES_SHARP = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
NOTE_NAMES_FLAT = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"]

_NOTE_TO_PC: dict[str, int] = {}
for _i, (_s, _f) in enumerate(zip(NOTE_NAMES_SHARP, NOTE_NAMES_FLAT)):
    _NOTE_TO_PC[_s] = _i
    _NOTE_TO_PC[_f] = _i

# Quality → pitch-class intervals from root (0 = root)
QUALITY_INTERVALS: dict[str, list[int]] = {
    "maj7": [0, 4, 7, 11],
    "min7": [0, 3, 7, 10],
    "7": [0, 4, 7, 10],
    "dim7": [0, 3, 6, 9],
    "m7b5": [0, 3, 6, 10],
    "7alt": [0, 4, 8, 10],
    "sus4": [0, 5, 7, 10],
    "aug7": [0, 4, 8, 10],
    "min": [0, 3, 7],
    "maj": [0, 4, 7],
    "dim": [0, 3, 6],
    "aug": [0, 4, 8],
}

EXTENSION_MAP: dict[int, int] = {
    9: 2,
    11: 5,
    13: 9,
}

ALTERATION_MAP: dict[str, int] = {
    "#5": 8,
    "b5": 6,
    "#9": 3,
    "b9": 1,
    "#11": 6,
    "b13": 8,
}

# ---------------------------------------------------------------------------
# ChordSymbol
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ChordSymbol:
    root: int  # MIDI pitch class 0–11
    quality: str  # "maj7", "min7", "7", "dim7", "m7b5", "7alt", "sus4", "aug7"
    extensions: Tuple[int, ...] = ()  # (9, 11, 13)
    alterations: Tuple[int, ...] = ()  # ("#5", "b5", "#9", "b9", "#11", "b13")

    # -- parser ---------------------------------------------------------------

    _PARSE_RE = re.compile(
        r"^(?P<root>[A-G][#b]?)"
        r"(?P<quality>maj7|min7|m7b5|7alt|dim7|sus4|aug7|min|maj|dim|aug|7)?"
        r"(?P<ext>9|11|13)?"
        r"(?P<alts>[#b]\d+)*$"
    )

    @classmethod
    def parse(cls, symbol: str) -> "ChordSymbol":
        """Parse common jazz chord symbols.

        Supported examples: Cm7, G7alt, Dm7b5, F#maj7, Bb7#11, Emaj9,
        C7b9#5, Am9, Bb7b9, D7#9.
        """
        s = symbol.strip()
        # Manual parse (regex can be tricky with the alt combinations)
        # 1. Root
        root_str = s[0]
        s = s[1:]
        if s and s[0] in "#b":
            root_str += s[0]
            s = s[1:]
        if root_str not in _NOTE_TO_PC:
            raise ValueError(f"Unknown root note: {root_str}")
        root = _NOTE_TO_PC[root_str]

        # 2. Quality + extensions + alterations from remaining string
        # Recognise quality keywords
        quality = "maj"  # default major triad
        extensions: list[int] = []
        alterations: list[str] = []

        remaining = s

        # Check specific compound qualities first
        for q in ("m7b5", "7alt", "maj7", "min7", "dim7", "sus4", "aug7", "min", "maj", "dim", "aug", "7"):
            if remaining.startswith(q):
                if q == "min7" or q == "m7":
                    quality = "min7"
                elif q == "m7b5":
                    quality = "m7b5"
                elif q == "7alt":
                    quality = "7alt"
                elif q == "maj7":
                    quality = "maj7"
                elif q == "dim7":
                    quality = "dim7"
                elif q == "sus4":
                    quality = "sus4"
                elif q == "aug7":
                    quality = "aug7"
                elif q == "7":
                    quality = "7"
                elif q == "min" or q == "m":
                    quality = "min"
                elif q == "maj":
                    quality = "maj"
                elif q == "dim":
                    quality = "dim"
                elif q == "aug":
                    quality = "aug"
                remaining = remaining[len(q):]
                break
        else:
            # Check for "m" as shorthand for minor
            if remaining.startswith("m") and not remaining.startswith("maj"):
                quality = "min7"
                remaining = remaining[1:]
                # If it's just a triad indicator without 7, adjust
                if remaining and remaining[0] in "0123456789":
                    pass  # will be handled below
                # Actually "m" alone = minor, "m7" = min7 — but we already consumed "m"
                # Let's check if there's a 7 coming

        # Check for "7" in remaining that upgrades triad to 7th
        # and also captures extension numbers
        ext_match = re.match(r"^(\d+)(.*)", remaining)
        if ext_match:
            num = int(ext_match.group(1))
            rest = ext_match.group(2)
            if num == 7:
                # Upgrade triad to 7th
                if quality == "maj":
                    quality = "maj7"
                elif quality == "min":
                    quality = "min7"
                elif quality == "dim":
                    quality = "dim7"
                elif quality == "aug":
                    quality = "aug7"
                elif quality == "7":
                    pass  # already dominant
                remaining = rest
            elif num in (9, 11, 13):
                extensions.append(num)
                # Implies 7th
                if quality == "maj":
                    quality = "maj7"
                elif quality == "min":
                    quality = "min7"
                elif quality in ("7", "dim7", "m7b5", "7alt", "sus4", "aug7"):
                    pass
                else:
                    quality = "7"
                remaining = rest

        # Parse alterations: #5, b5, #9, b9, #11, b13
        alt_re = re.compile(r"([#b]\d+)")
        for m in alt_re.finditer(remaining):
            alt = m.group(1)
            alterations.append(alt)

        return cls(
            root=root,
            quality=quality,
            extensions=tuple(extensions),
            alterations=tuple(alterations),
        )

    # -- pitch classes --------------------------------------------------------

    @property
    def pitches(self) -> List[int]:
        """All pitch classes (0–11) in this chord."""
        base = list(QUALITY_INTERVALS.get(self.quality, [0, 4, 7]))
        # Add extensions
        for ext in self.extensions:
            pc = EXTENSION_MAP.get(ext)
            if pc is not None and pc not in base:
                base.append(pc)
        # Apply alterations
        for alt in self.alterations:
            alt_pc = ALTERATION_MAP.get(alt)
            if alt_pc is not None and alt_pc not in base:
                # Replace the natural degree if present
                natural_map = {"#5": 7, "b5": 7, "#9": 2, "b9": 2, "#11": 5, "b13": 9}
                natural = natural_map.get(alt)
                if natural and natural in base:
                    base.remove(natural)
                base.append(alt_pc)
        return sorted(set((self.root + iv) % 12 for iv in base))

    @property
    def third(self) -> Optional[int]:
        """Pitch class of the 3rd."""
        intervals = QUALITY_INTERVALS.get(self.quality, [])
        for iv in intervals:
            pc = (self.root + iv) % 12
            if iv in (3, 4):  # minor 3rd or major 3rd
                return pc
        return None

    @property
    def seventh(self) -> Optional[int]:
        """Pitch class of the 7th."""
        intervals = QUALITY_INTERVALS.get(self.quality, [])
        for iv in intervals:
            if iv in (10, 11):  # minor 7th or major 7th
                return (self.root + iv) % 12
        return None

    @property
    def fifth(self) -> Optional[int]:
        intervals = QUALITY_INTERVALS.get(self.quality, [])
        for iv in intervals:
            if iv in (6, 7, 8):
                return (self.root + iv) % 12
        return None

    def __str__(self) -> str:
        return f"{NOTE_NAMES_SHARP[self.root]}{self.quality}"


# ---------------------------------------------------------------------------
# Voicing
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Voicing:
    pitches: Tuple[int, ...]  # actual MIDI pitches (not pitch classes)
    chord: ChordSymbol
    style: str  # "drop2", "rootless", "quartal", "shell", "guide_tones", "kendrick", "tyner"
    bass_note: Optional[int] = None

    def to_midi_events(
        self,
        start: float,
        duration: float,
        channel: int = 0,
        velocity: int = 80,
    ) -> List[dict]:
        """Generate simple MIDI note-event dicts.

        Each event: {"type": "note_on"/"note_off", "note": int, "time": float,
                     "channel": int, "velocity": int}
        """
        events: list[dict] = []
        notes = list(self.pitches)
        if self.bass_note is not None:
            notes.append(self.bass_note)
        for note in notes:
            events.append({
                "type": "note_on",
                "note": note,
                "time": start,
                "channel": channel,
                "velocity": velocity,
            })
            events.append({
                "type": "note_off",
                "note": note,
                "time": start + duration,
                "channel": channel,
                "velocity": 0,
            })
        return events

    def to_midi_file(self, start: float, duration: float, channel: int = 0,
                     velocity: int = 80, filename: str = "output.mid",
                     bpm: int = 120) -> str:
        """Export to a MIDI file using mido (if installed)."""
        try:
            import mido
        except ImportError:
            raise ImportError("Install mido for MIDI export: pip install mido")

        mid = mido.MidiFile(ticks_per_beat=480)
        track = mido.MidiTrack()
        mid.tracks.append(track)

        tempo = mido.bpm2tempo(bpm)
        track.append(mido.MetaMessage("set_tempo", tempo=tempo, time=0))

        def secs_to_ticks(secs: float) -> int:
            return int(mido.second2tick(secs, ticks_per_beat=480, tempo=tempo))

        events = self.to_midi_events(start, duration, channel, velocity)
        events.sort(key=lambda e: (e["time"], 0 if e["type"] == "note_on" else 1))

        abs_time = 0
        for ev in events:
            delta = secs_to_ticks(ev["time"]) - abs_time
            abs_time += delta
            msg_type = "note_on" if ev["type"] == "note_on" else "note_off"
            track.append(mido.Message(
                msg_type, note=ev["note"], velocity=ev["velocity"],
                channel=ev["channel"], time=max(0, delta),
            ))

        mid.save(filename)
        return filename
