"""Comping pattern generator in the style of various jazz pianists."""

from __future__ import annotations

import random
from typing import List, Optional, Tuple

from .voicings import ChordSymbol, Voicing
from .generator import VoicingGenerator

# Rhythm patterns: each entry is (beat_subdivision, relative_velocity)
# Beats are in quarter-note subdivisions (1 = quarter note, 0.5 = eighth)
# Velocities are relative: 1.0 = full, 0.0 = rest

STYLES: dict[str, dict] = {
    "freddie_green": {
        "description": "Quarter-note shells, swing feel",
        "density": 0.5,
        "rhythm": [(0.0, 0.9), (1.0, 0.7), (2.0, 0.8), (3.0, 0.6)],
        "voicing_style": "shell",
        "velocity_range": (70, 90),
    },
    "wynton_kelly": {
        "description": "Rhythmic, bluesy comping",
        "density": 0.6,
        "rhythm": [
            (0.0, 0.8), (0.75, 0.5), (1.5, 0.7), (2.0, 0.9),
            (3.0, 0.6), (3.25, 0.4),
        ],
        "voicing_style": "rootless",
        "velocity_range": (60, 95),
    },
    "bill_evans": {
        "description": "Open, intervallic, floating",
        "density": 0.55,
        "rhythm": [
            (0.0, 0.6), (0.5, 0.3), (1.5, 0.8), (2.5, 0.5),
            (3.0, 0.7), (3.5, 0.4),
        ],
        "voicing_style": "drop2",
        "velocity_range": (50, 85),
    },
    "herbie_hancock": {
        "description": "Angular, rhythmic stabs",
        "density": 0.5,
        "rhythm": [
            (0.0, 0.9), (0.75, 0.7), (1.0, 0.3), (2.0, 0.8),
            (2.75, 0.6), (3.5, 0.5),
        ],
        "voicing_style": "rootless",
        "velocity_range": (55, 100),
    },
    "red_garland": {
        "description": "Block chords, bumps",
        "density": 0.65,
        "rhythm": [
            (0.0, 0.8), (0.5, 0.6), (1.0, 0.7), (1.5, 0.5),
            (2.0, 0.9), (2.5, 0.6), (3.0, 0.8), (3.5, 0.5),
        ],
        "voicing_style": "drop2",
        "velocity_range": (65, 95),
    },
    "tommy_flanagan": {
        "description": "Sparse, melodic comping",
        "density": 0.4,
        "rhythm": [
            (0.0, 0.7), (2.0, 0.8), (3.5, 0.5),
        ],
        "voicing_style": "shell",
        "velocity_range": (55, 85),
    },
}


class CompingEvent:
    """A single comping hit."""

    def __init__(
        self,
        voicing: Voicing,
        start_beat: float,
        duration: float,
        velocity: int,
    ):
        self.voicing = voicing
        self.start_beat = start_beat
        self.duration = duration
        self.velocity = velocity

    def to_midi_events(self, bpm: int = 120, channel: int = 0) -> list:
        """Convert to MIDI events. Returns list of note dicts."""
        start_sec = self.start_beat * 60.0 / bpm
        dur_sec = self.duration * 60.0 / bpm
        return self.voicing.to_midi_events(start_sec, dur_sec, channel, self.velocity)

    def __repr__(self) -> str:
        return (
            f"CompingEvent(chord={self.voicing.chord}, beat={self.start_beat}, "
            f"dur={self.duration:.2f}, vel={self.velocity})"
        )


class CompingGenerator:
    """Generate comping patterns in a specific pianist's style."""

    def __init__(self, style: str = "bill_evans"):
        if style not in STYLES:
            raise ValueError(
                f"Unknown style '{style}'. Available: {list(STYLES.keys())}"
            )
        self.style = style
        self.config = STYLES[style]

    def comp(
        self,
        chords: List[ChordSymbol],
        bars: int = 4,
        time_signature: Tuple[int, int] = (4, 4),
    ) -> List[CompingEvent]:
        """Generate comping rhythm + voicings."""
        beats_per_bar = time_signature[0]
        total_beats = bars * beats_per_bar

        # Distribute chords evenly across bars
        beats_per_chord = total_beats / max(len(chords), 1)

        # Use the style's preferred voicing style
        gen = VoicingGenerator(
            style=self.config["voicing_style"],
            register=(48, 84),
        )

        # Generate voice-led voicings
        voicings = gen.voice_lead(chords)

        # Apply rhythm patterns
        events: list[CompingEvent] = []
        rng = random.Random(42)  # deterministic seed for reproducibility

        vel_lo, vel_hi = self.config["velocity_range"]
        rhythm = self.config["rhythm"]

        for i, voicing in enumerate(voicings):
            chord_start_beat = i * beats_per_chord
            chord_end_beat = chord_start_beat + beats_per_chord

            # Apply rhythm pattern, offset to chord start
            for beat_offset, rel_vel in rhythm:
                absolute_beat = chord_start_beat + beat_offset
                if absolute_beat >= total_beats:
                    continue

                # Random velocity variation within style range
                velocity = int(vel_lo + (vel_hi - vel_lo) * rel_vel)
                velocity = max(1, min(127, velocity + rng.randint(-8, 8)))

                # Duration: until next hit or end of chord slot
                # Find next hit in this chord slot
                next_hits = [
                    chord_start_beat + bo
                    for bo, _ in rhythm
                    if chord_start_beat + bo > absolute_beat
                    and chord_start_beat + bo < chord_end_beat
                ]
                if next_hits:
                    duration = min(next_hits) - absolute_beat
                else:
                    duration = chord_end_beat - absolute_beat

                duration = max(0.25, min(duration, 2.0))

                events.append(CompingEvent(
                    voicing=voicing,
                    start_beat=absolute_beat,
                    duration=duration,
                    velocity=velocity,
                ))

        return events
