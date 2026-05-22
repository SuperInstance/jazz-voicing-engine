"""Walking bass line generator."""

from __future__ import annotations

import random
from typing import List, Optional, Tuple

from .voicings import ChordSymbol, QUALITY_INTERVALS

# Approach types
_CHROMATIC = "chromatic"
_SCALE = "scale"
_DOMINANT = "dominant"
_COMMON = "common"  # common tone


class WalkingBassGenerator:
    """Generate idiomatic walking bass lines."""

    STYLES = {
        "ray_brown": {"density": 1.0, "chromatic_ratio": 0.3},
        "paul_chambers": {"density": 1.0, "chromatic_ratio": 0.25},
        "ron_carter": {"density": 1.0, "chromatic_ratio": 0.35},
        "default": {"density": 1.0, "chromatic_ratio": 0.3},
    }

    def __init__(self, style: str = "ray_brown"):
        self.config = self.STYLES.get(style, self.STYLES["default"])

    def walk(
        self,
        chords: List[ChordSymbol],
        bars: int = 4,
        bpm: int = 120,
        style: str = "ray_brown",
    ) -> List[Tuple[int, float]]:
        """Generate a walking bass line.

        Returns list of (pitch, start_time_in_seconds) tuples.
        Quarter-note walking: 4 notes per bar.
        """
        config = self.STYLES.get(style, self.STYLES["default"])
        rng = random.Random(42)

        total_beats = bars * 4
        beats_per_chord = total_beats / max(len(chords), 1)

        # Scale degrees for each chord quality
        def chord_tones(chord: ChordSymbol) -> list[int]:
            intervals = QUALITY_INTERVALS.get(chord.quality, [0, 4, 7])
            return [(chord.root + iv) % 12 for iv in intervals]

        def scale_degrees(chord: ChordSymbol) -> list[int]:
            """Approximate scale tones for the chord."""
            root = chord.root
            if chord.quality in ("min7", "m7b5", "min"):
                # Dorian / natural minor
                return [root + i for i in [0, 2, 3, 5, 7, 9, 10]]
            elif chord.quality in ("7", "7alt", "sus4"):
                # Mixolydian
                return [root + i for i in [0, 2, 4, 5, 7, 9, 10]]
            elif chord.quality in ("maj7", "maj"):
                # Ionian
                return [root + i for i in [0, 2, 4, 5, 7, 9, 11]]
            elif chord.quality in ("dim7", "dim"):
                # Diminished scale
                return [root + i for i in [0, 2, 3, 5, 6, 8, 9, 11]]
            elif chord.quality in ("aug7", "aug"):
                return [root + i for i in [0, 2, 4, 6, 7, 9, 10]]
            else:
                return [root + i for i in [0, 2, 4, 5, 7, 9, 11]]

        # Build the line beat by beat
        notes: list[tuple[int, float]] = []
        current_pitch: Optional[int] = None
        bass_register = (28, 48)  # bass range

        def _in_bass_range(pc: int, prefer: int) -> int:
            """Put pitch class in bass register near *prefer*."""
            best = None
            for p in range(bass_register[0], bass_register[1] + 1):
                if p % 12 == pc:
                    if best is None or abs(p - prefer) < abs(best - prefer):
                        best = p
            if best is None:
                best = pc + (prefer // 12) * 12
                while best < bass_register[0]:
                    best += 12
                while best > bass_register[1]:
                    best -= 12
            return best

        for beat in range(total_beats):
            # Which chord?
            chord_idx = min(int(beat / beats_per_chord), len(chords) - 1)
            chord = chords[chord_idx]

            # Next chord (for approach notes on beats 3-4)
            next_idx = min(chord_idx + 1, len(chords) - 1)
            next_chord = chords[next_idx]

            beat_in_chord = beat - int(chord_idx * beats_per_chord)
            time_sec = beat * 60.0 / bpm

            if beat == 0 or current_pitch is None:
                # Beat 1: play root
                pitch = _in_bass_range(chord.root, bass_register[0] + 12)
            elif beat_in_chord == 0:
                # First beat of a new chord: root
                pitch = _in_bass_range(chord.root, current_pitch)
            elif beat_in_chord == 1:
                # Beat 2: chord tone or scale tone
                tones = chord_tones(chord)
                if current_pitch is not None:
                    # Pick nearest chord tone
                    targets = [_in_bass_range(t, current_pitch) for t in tones]
                    pitch = min(targets, key=lambda p: abs(p - current_pitch))
                else:
                    pitch = _in_bass_range(tones[1] if len(tones) > 1 else tones[0], bass_register[0] + 12)
            elif beat_in_chord == 2:
                # Beat 3: 5th or passing tone
                fifth = (chord.root + 7) % 12
                if rng.random() < 0.7:
                    pitch = _in_bass_range(fifth, current_pitch if current_pitch else 36)
                else:
                    scale = scale_degrees(chord)
                    pitch = _in_bass_range(rng.choice(scale), current_pitch if current_pitch else 36)
            else:
                # Beat 4: approach note to next chord root
                next_root = next_chord.root
                if rng.random() < config["chromatic_ratio"]:
                    # Chromatic approach (one semitone above or below)
                    above = (next_root + 1) % 12
                    below = (next_root - 1) % 12
                    if current_pitch is not None:
                        candidates = [
                            _in_bass_range(above, current_pitch),
                            _in_bass_range(below, current_pitch),
                        ]
                        pitch = min(candidates, key=lambda p: abs(p - current_pitch))
                    else:
                        pitch = _in_bass_range(below, 36)
                elif rng.random() < 0.5:
                    # Scale-wise approach
                    scale = scale_degrees(chord)
                    # Pick the one closest to next root that's not the root itself
                    candidates = [s % 12 for s in scale if s % 12 != next_root]
                    if candidates:
                        pc = min(candidates, key=lambda c: abs(c - next_root))
                        pitch = _in_bass_range(pc, current_pitch if current_pitch else 36)
                    else:
                        pitch = _in_bass_range((next_root - 1) % 12, current_pitch if current_pitch else 36)
                else:
                    # Dominant approach (5th to root)
                    dom = (next_root + 7) % 12
                    pitch = _in_bass_range(dom, current_pitch if current_pitch else 36)

            current_pitch = pitch
            notes.append((pitch, time_sec))

        return notes
