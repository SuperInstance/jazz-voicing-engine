"""Voicing generator with multiple styles and voice-leading optimisation."""

from __future__ import annotations

from typing import List, Optional, Tuple

from .voicings import ChordSymbol, Voicing, QUALITY_INTERVALS

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _pc(pitch: int) -> int:
    return pitch % 12


def _closest_octave(pc: int, target_pitch: int) -> int:
    """Return the octave-shifted pitch class nearest to *target_pitch*."""
    candidates = [pc + 12 * o for o in range(-2, 10)]
    return min(candidates, key=lambda p: abs(p - target_pitch))


def _closest_in_range(pc: int, lo: int, hi: int, prefer: int) -> int:
    """Return pitch of *pc* within [lo, hi] closest to *prefer*."""
    best = None
    for p in range(lo, hi + 1):
        if p % 12 == pc:
            if best is None or abs(p - prefer) < abs(best - prefer):
                best = p
    if best is None:
        # No pitch in range; pick nearest octave
        octaves = range(lo // 12 - 1, hi // 12 + 2)
        candidates = [pc + 12 * o for o in octaves]
        best = min(candidates, key=lambda p: abs(p - prefer))
    return best


def _semitone_distance(a: Tuple[int, ...], b: Tuple[int, ...]) -> float:
    """Minimum total semitone movement pairing (greedy)."""
    if len(a) != len(b):
        return float("inf")
    total = 0
    for x, y in zip(a, b):
        total += abs(x - y)
    return total


# ---------------------------------------------------------------------------
# VoicingGenerator
# ---------------------------------------------------------------------------

class VoicingGenerator:
    """Generate jazz piano voicings with smooth voice leading."""

    def __init__(
        self,
        style: str = "drop2",
        register: Tuple[int, int] = (48, 84),
    ):
        self.style = style
        self.register = register  # (low, high) MIDI range

    # -- public API -----------------------------------------------------------

    def voice(
        self,
        chord: ChordSymbol,
        prev_voicing: Optional[Voicing] = None,
    ) -> Voicing:
        """Generate one voicing, with voice-leading from *prev_voicing*."""
        method = {
            "drop2": self.drop_2,
            "rootless": self.rootless,
            "quartal": self.quartal,
            "shell": self.shell,
            "guide_tones": self.guide_tones,
        }.get(self.style, self.drop_2)

        v = method(chord)

        if prev_voicing is not None:
            v = self._voice_lead_single(chord, prev_voicing, v)

        return v

    def voice_lead(self, chords: List[ChordSymbol]) -> List[Voicing]:
        """Generate optimal voice leading through a progression."""
        if not chords:
            return []

        method = {
            "drop2": self.drop_2,
            "rootless": self.rootless,
            "quartal": self.quartal,
            "shell": self.shell,
            "guide_tones": self.guide_tones,
        }.get(self.style, self.drop_2)

        voicings: list[Voicing] = [method(chords[0])]

        for chord in chords[1:]:
            prev = voicings[-1]
            v = self._voice_lead_single(chord, prev, method(chord))
            voicings.append(v)

        return voicings

    # -- voicing styles -------------------------------------------------------

    def drop_2(self, chord: ChordSymbol) -> Voicing:
        """Drop-2 voicing: close position, then drop 2nd-from-top an octave."""
        pcs = chord.pitches
        # Build close position in mid register
        center = (self.register[0] + self.register[1]) // 2
        # Start from root near center, stack upward
        notes: list[int] = []
        base_octave = center // 12
        root_pitch = chord.root + base_octave * 12
        # Find a starting pitch near center
        while root_pitch > center:
            root_pitch -= 12
        while root_pitch < center - 6:
            root_pitch += 12

        # Stack in close position
        for pc in pcs:
            if not notes:
                notes.append(root_pitch)
            else:
                # Find next pitch class above last note, within a few semitones
                candidate = notes[-1]
                while _pc(candidate) != pc:
                    candidate += 1
                notes.append(candidate)

        # Drop 2nd from top
        if len(notes) >= 2:
            notes[-2] -= 12

        # Clamp to register
        notes = self._clamp_to_register(notes)

        return Voicing(
            pitches=tuple(sorted(notes)),
            chord=chord,
            style="drop2",
        )

    def rootless(self, chord: ChordSymbol, bass_note: Optional[int] = None) -> Voicing:
        """Rootless voicing (omit root, play 3-7 plus extensions).

        Common jazz piano style where the bass player covers the root.
        """
        intervals = QUALITY_INTERVALS.get(chord.quality, [0, 4, 7])
        # Remove root (interval 0), keep 3rd, 7th, + color tones
        color_intervals = [iv for iv in intervals if iv != 0]

        # Add extensions
        from .voicings import EXTENSION_MAP
        for ext in chord.extensions:
            pc = EXTENSION_MAP.get(ext)
            if pc is not None:
                color_intervals.append(pc)

        # If we only have 2 notes (shell), add 9th or 5th
        if len(color_intervals) < 3:
            color_intervals.append(2)  # 9th
        if len(color_intervals) < 4:
            color_intervals.append(9)  # 13th / 6th

        # Build pitches
        center = (self.register[0] + self.register[1]) // 2
        base_octave = center // 12
        root_pitch = chord.root + base_octave * 12
        while root_pitch > center:
            root_pitch -= 12
        while root_pitch < center - 6:
            root_pitch += 12

        notes: list[int] = []
        for iv in sorted(color_intervals):
            pc = (chord.root + iv) % 12
            if not notes:
                notes.append(_closest_in_range(pc, self.register[0], self.register[1], root_pitch))
            else:
                # Stack above
                candidate = notes[-1]
                while _pc(candidate) != pc:
                    candidate += 1
                # Make sure it's in range
                if candidate > self.register[1]:
                    candidate -= 12
                notes.append(candidate)

        notes = self._clamp_to_register(notes)

        bn = bass_note
        if bn is None:
            bn = chord.root + 12 * (self.register[0] // 12 - 1)

        return Voicing(
            pitches=tuple(sorted(notes)),
            chord=chord,
            style="rootless",
            bass_note=bn,
        )

    def quartal(self, chord: ChordSymbol) -> Voicing:
        """Stacked fourths (McCoy Tyner style)."""
        pcs = chord.pitches
        center = (self.register[0] + self.register[1]) // 2
        base_octave = center // 12
        root_pitch = chord.root + base_octave * 12
        while root_pitch > center:
            root_pitch -= 12
        while root_pitch < center - 6:
            root_pitch += 12

        # Start from a chord tone near center, stack in 4ths
        notes: list[int] = [root_pitch]
        for _ in range(len(pcs) - 1):
            notes.append(notes[-1] + 5)  # perfect 4th = 5 semitones

        # If we have extensions that fit, keep stacking
        for ext in chord.extensions:
            notes.append(notes[-1] + 5)

        notes = self._clamp_to_register(notes)

        return Voicing(
            pitches=tuple(sorted(notes)),
            chord=chord,
            style="quartal",
        )

    def shell(self, chord: ChordSymbol) -> Voicing:
        """Shell voicing: 3rd and 7th only."""
        third = chord.third
        seventh = chord.seventh

        center = (self.register[0] + self.register[1]) // 2
        notes: list[int] = []
        if third is not None:
            notes.append(_closest_in_range(third, self.register[0], self.register[1], center))
        if seventh is not None:
            target = center + 3 if third is not None else center
            notes.append(_closest_in_range(seventh, self.register[0], self.register[1], target))

        # If no 7th, add 5th
        if seventh is None and chord.fifth is not None:
            notes.append(_closest_in_range(
                chord.fifth, self.register[0], self.register[1], center + 3
            ))

        notes = self._clamp_to_register(notes)

        return Voicing(
            pitches=tuple(sorted(notes)),
            chord=chord,
            style="shell",
        )

    def guide_tones(self, chord: ChordSymbol) -> Voicing:
        """Guide tones: 3rd and 7th, placed for voice leading."""
        return self.shell(chord)  # same notes, different semantic label

    # -- voice leading --------------------------------------------------------

    def _voice_lead_single(
        self,
        chord: ChordSymbol,
        prev: Voicing,
        candidate: Voicing,
    ) -> Voicing:
        """Adjust *candidate* voicing to minimise movement from *prev*."""
        target_pcs = set(chord.pitches)
        prev_notes = list(prev.pitches)
        n_notes = len(prev_notes)

        # We want n_notes pitches, each from the target pitch-class set,
        # minimising total distance from prev_notes.
        new_notes: list[int] = []
        used_targets: list[int] = []

        for prev_n in prev_notes:
            # Find the best matching pitch class
            best = None
            best_dist = float("inf")
            for pc in target_pcs:
                p = _closest_in_range(pc, self.register[0], self.register[1], prev_n)
                dist = abs(p - prev_n)
                if dist < best_dist:
                    best_dist = dist
                    best = p
            if best is not None:
                new_notes.append(best)

        # If we have fewer notes than desired, add missing chord tones
        existing_pcs = {_pc(n) for n in new_notes}
        for pc in target_pcs:
            if pc not in existing_pcs:
                center = (self.register[0] + self.register[1]) // 2
                new_notes.append(_closest_in_range(pc, self.register[0], self.register[1], center))

        # Trim to match candidate voicing size (not previous)
        target_size = len(candidate.pitches)
        if len(new_notes) > target_size:
            new_notes = sorted(new_notes)
            center = (self.register[0] + self.register[1]) // 2
            new_notes.sort(key=lambda n: abs(n - center))
            new_notes = new_notes[:target_size]

        new_notes = self._clamp_to_register(sorted(new_notes))

        return Voicing(
            pitches=tuple(new_notes),
            chord=chord,
            style=candidate.style,
            bass_note=candidate.bass_note,
        )

    # -- helpers --------------------------------------------------------------

    def _clamp_to_register(self, notes: list[int]) -> list[int]:
        """Shift notes that fall outside the register back in."""
        result = []
        for n in notes:
            while n < self.register[0]:
                n += 12
            while n > self.register[1]:
                n -= 12
            result.append(n)
        return result
