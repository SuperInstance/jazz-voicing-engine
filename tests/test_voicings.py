"""Tests for jazz-voicing-engine."""

import pytest

from jazz_voicing_engine.voicings import ChordSymbol, Voicing, NOTE_NAMES_SHARP
from jazz_voicing_engine.generator import VoicingGenerator
from jazz_voicing_engine.comping import CompingGenerator
from jazz_voicing_engine.walking_bass import WalkingBassGenerator


# ---------------------------------------------------------------------------
# ChordSymbol parsing
# ---------------------------------------------------------------------------

class TestChordParsing:
    def test_cm7(self):
        c = ChordSymbol.parse("Cm7")
        assert c.root == 0
        assert c.quality == "min7"
        assert 0 in c.pitches  # C
        assert 3 in c.pitches  # Eb
        assert 7 in c.pitches  # G
        assert 10 in c.pitches  # Bb

    def test_g7alt(self):
        c = ChordSymbol.parse("G7alt")
        assert c.root == 7
        assert c.quality == "7alt"

    def test_dm7b5(self):
        c = ChordSymbol.parse("Dm7b5")
        assert c.root == 2
        assert c.quality == "m7b5"
        # D m7b5: D F Ab C
        assert 2 in c.pitches
        assert 5 in c.pitches
        assert 8 in c.pitches
        assert 0 in c.pitches

    def test_fsharp_maj7(self):
        c = ChordSymbol.parse("F#maj7")
        assert c.root == 6
        assert c.quality == "maj7"

    def test_bb7_sharp11(self):
        c = ChordSymbol.parse("Bb7#11")
        assert c.root == 10
        assert c.quality == "7"
        assert "#11" in c.alterations

    def test_emaj9(self):
        c = ChordSymbol.parse("Emaj9")
        assert c.root == 4
        assert c.quality == "maj7"
        assert 9 in c.extensions

    def test_c7(self):
        c = ChordSymbol.parse("C7")
        assert c.root == 0
        assert c.quality == "7"

    def test_fmin7(self):
        c = ChordSymbol.parse("Fmin7")
        assert c.root == 5
        assert c.quality == "min7"

    def test_pitch_classes_cmaj7(self):
        c = ChordSymbol.parse("Cmaj7")
        pitches = c.pitches
        # Cmaj7: C E G B
        assert sorted(pitches) == [0, 4, 7, 11]

    def test_pitch_classes_g7(self):
        c = ChordSymbol.parse("G7")
        # G7: G B D F
        assert sorted(c.pitches) == [2, 5, 7, 11]

    def test_third_and_seventh(self):
        c = ChordSymbol.parse("Cmaj7")
        assert c.third == 4  # E
        assert c.seventh == 11  # B

        c2 = ChordSymbol.parse("Cm7")
        assert c2.third == 3  # Eb
        assert c2.seventh == 10  # Bb


# ---------------------------------------------------------------------------
# Voicing styles
# ---------------------------------------------------------------------------

class TestVoicingStyles:
    @pytest.fixture
    def gen(self):
        return VoicingGenerator(register=(48, 84))

    def _in_register(self, pitches, lo=48, hi=84):
        return all(lo <= p <= hi for p in pitches)

    def test_drop2(self, gen):
        chord = ChordSymbol.parse("Cmaj7")
        gen.style = "drop2"
        v = gen.drop_2(chord)
        assert len(v.pitches) >= 3
        assert self._in_register(v.pitches)
        assert v.style == "drop2"

    def test_rootless(self, gen):
        chord = ChordSymbol.parse("Cm7")
        gen.style = "rootless"
        v = gen.rootless(chord)
        assert len(v.pitches) >= 3
        assert self._in_register(v.pitches)
        assert v.bass_note is not None
        assert v.style == "rootless"

    def test_quartal(self, gen):
        chord = ChordSymbol.parse("Dm7")
        v = gen.quartal(chord)
        assert len(v.pitches) >= 3
        assert self._in_register(v.pitches)
        assert v.style == "quartal"

    def test_shell(self, gen):
        chord = ChordSymbol.parse("G7")
        v = gen.shell(chord)
        assert 2 <= len(v.pitches) <= 3
        assert self._in_register(v.pitches)
        assert v.style == "shell"

    def test_guide_tones(self, gen):
        chord = ChordSymbol.parse("Fm7")
        v = gen.guide_tones(chord)
        assert 2 <= len(v.pitches) <= 3
        assert self._in_register(v.pitches)


# ---------------------------------------------------------------------------
# Voice leading
# ---------------------------------------------------------------------------

class TestVoiceLeading:
    def test_minimizes_movement(self):
        gen = VoicingGenerator(style="drop2", register=(48, 84))
        chords = [ChordSymbol.parse(c) for c in ["Cmaj7", "Dm7", "G7", "Cmaj7"]]
        voicings = gen.voice_lead(chords)

        assert len(voicings) == 4

        # Check total semitone distance is reasonable
        total = 0
        for i in range(1, len(voicings)):
            n = min(len(voicings[i].pitches), len(voicings[i - 1].pitches))
            for j in range(n):
                total += abs(voicings[i].pitches[j] - voicings[i - 1].pitches[j])

        # With good voice leading, total should be under ~60 semitones for ii-V-I
        assert total < 80, f"Voice leading too choppy: total={total}"

    def test_all_in_register(self):
        gen = VoicingGenerator(style="rootless", register=(48, 84))
        chords = [ChordSymbol.parse(c) for c in ["Cm7", "F7", "Bbmaj7", "Ebmaj7"]]
        voicings = gen.voice_lead(chords)
        for v in voicings:
            assert all(48 <= p <= 84 for p in v.pitches), f"Out of range: {v.pitches}"


# ---------------------------------------------------------------------------
# Walking bass
# ---------------------------------------------------------------------------

class TestWalkingBass:
    def test_hits_root_on_beat_1(self):
        chords = [ChordSymbol.parse(c) for c in ["Cmaj7", "Am7", "Dm7", "G7"]]
        bass = WalkingBassGenerator()
        notes = bass.walk(chords, bars=4, bpm=120)

        # Should have 16 notes (4 beats × 4 bars)
        assert len(notes) == 16

        # First note should be root of first chord (C = 0 mod 12)
        assert notes[0][0] % 12 == 0

    def test_beat_1_per_chord(self):
        chords = [ChordSymbol.parse(c) for c in ["Cmaj7", "Am7", "Dm7", "G7"]]
        bass = WalkingBassGenerator()
        notes = bass.walk(chords, bars=4, bpm=120)

        # Each chord occupies 4 beats
        # Beat 1 (index 0, 4, 8, 12) should be root
        for i, chord in enumerate(chords):
            beat_1 = notes[i * 4]
            assert beat_1[0] % 12 == chord.root, (
                f"Beat 1 of chord {chord} should be root, got pc={beat_1[0] % 12}"
            )

    def test_bass_in_range(self):
        chords = [ChordSymbol.parse(c) for c in ["Cm7", "F7"]]
        bass = WalkingBassGenerator()
        notes = bass.walk(chords, bars=2, bpm=120)
        for pitch, _ in notes:
            assert 28 <= pitch <= 48, f"Bass note {pitch} out of range"


# ---------------------------------------------------------------------------
# Comping
# ---------------------------------------------------------------------------

class TestComping:
    def test_generates_events(self):
        chords = [ChordSymbol.parse(c) for c in ["Cmaj7", "Am7", "Dm7", "G7"]]
        comp = CompingGenerator(style="bill_evans")
        events = comp.comp(chords, bars=4)

        assert len(events) > 0
        # Should have multiple events per chord
        assert len(events) >= len(chords)

    def test_all_styles_work(self):
        chords = [ChordSymbol.parse(c) for c in ["Cmaj7", "Dm7", "G7"]]
        for style in CompingGenerator.STYLES if hasattr(CompingGenerator, 'STYLES') else ["bill_evans"]:
            comp = CompingGenerator(style=style)
            events = comp.comp(chords, bars=2)
            assert len(events) > 0

    def test_velocity_in_range(self):
        from jazz_voicing_engine.comping import STYLES
        chords = [ChordSymbol.parse(c) for c in ["Cm7", "F7"]]
        for style_name in STYLES:
            comp = CompingGenerator(style=style_name)
            events = comp.comp(chords, bars=2)
            for ev in events:
                assert 1 <= ev.velocity <= 127


# ---------------------------------------------------------------------------
# MIDI events
# ---------------------------------------------------------------------------

class TestMIDIEvents:
    def test_to_midi_events(self):
        chord = ChordSymbol.parse("Cmaj7")
        v = Voicing(
            pitches=(60, 64, 67, 71),
            chord=chord,
            style="drop2",
        )
        events = v.to_midi_events(start=0.0, duration=1.0, velocity=80)
        # 4 note_on + 4 note_off
        assert len(events) == 8
        note_ons = [e for e in events if e["type"] == "note_on"]
        note_offs = [e for e in events if e["type"] == "note_off"]
        assert len(note_ons) == 4
        assert len(note_offs) == 4
        # All note-ons at t=0
        assert all(e["time"] == 0.0 for e in note_ons)
        # All note-offs at t=1.0
        assert all(e["time"] == 1.0 for e in note_offs)

    def test_bass_note_included(self):
        chord = ChordSymbol.parse("Cm7")
        v = Voicing(
            pitches=(60, 63, 67, 70),
            chord=chord,
            style="rootless",
            bass_note=36,
        )
        events = v.to_midi_events(start=0.0, duration=2.0)
        notes = {e["note"] for e in events if e["type"] == "note_on"}
        assert 36 in notes
