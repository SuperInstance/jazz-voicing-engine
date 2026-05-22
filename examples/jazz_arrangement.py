"""Full arrangement of 'Autumn Leaves' — voicings, comping, walking bass, MIDI export."""

from jazz_voicing_engine.voicings import ChordSymbol, Voicing
from jazz_voicing_engine.generator import VoicingGenerator
from jazz_voicing_engine.comping import CompingGenerator, CompingEvent
from jazz_voicing_engine.walking_bass import WalkingBassGenerator


# Autumn Leaves — standard key of G minor
# Form: AABC (8 bars shown here as 2 choruses of the A section)
AUTUMN_LEAVES = [
    "Cm7",    # bar 1
    "F7",     # bar 2
    "Bbmaj7", # bar 3
    "Ebmaj7", # bar 4
    "Am7b5",  # bar 5
    "D7alt",  # bar 6
    "Gm7",    # bar 7
    "Gm7",    # bar 8 (turnaround)
]


def main():
    # Parse chords
    chords = [ChordSymbol.parse(c) for c in AUTUMN_LEAVES]
    print("=== Autumn Leaves — Chord Progression ===")
    for c in chords:
        print(f"  {c} → pitches: {c.pitches}")

    # Generate rootless voicings with voice leading
    print("\n=== Rootless Voicings (voice led) ===")
    gen = VoicingGenerator(style="rootless", register=(48, 84))
    voicings = gen.voice_lead(chords)
    for v in voicings:
        print(f"  {v.chord}: {v.pitches} (bass: {v.bass_note})")

    # Walking bass
    print("\n=== Walking Bass ===")
    bass_gen = WalkingBassGenerator(style="ray_brown")
    bass_notes = bass_gen.walk(chords, bars=8, bpm=140)
    for i, (pitch, time) in enumerate(bass_notes):
        bar = i // 4 + 1
        beat = i % 4 + 1
        print(f"  Bar {bar}, Beat {beat}: MIDI {pitch} ({time:.2f}s)")

    # Bill Evans style comping
    print("\n=== Comping (Bill Evans style) ===")
    comp_gen = CompingGenerator(style="bill_evans")
    comp_events = comp_gen.comp(chords, bars=8)
    for ev in comp_events:
        bar = int(ev.start_beat // 4) + 1
        beat = ev.start_beat % 4 + 1
        print(f"  Bar {bar}, Beat {beat:.1f}: {ev.voicing.chord} "
              f"vel={ev.velocity} dur={ev.duration:.2f}")

    # Export to MIDI
    print("\n=== MIDI Export ===")
    try:
        import mido
        mid = mido.MidiFile(ticks_per_beat=480)
        track = mido.MidiTrack()
        mid.tracks.append(track)

        bpm = 140
        tempo = mido.bpm2tempo(bpm)
        track.append(mido.MetaMessage("set_tempo", tempo=tempo, time=0))

        def secs_to_ticks(secs):
            return int(mido.second2tick(secs, ticks_per_beat=480, tempo=tempo))

        # Collect all MIDI events
        all_events = []

        # Piano (channel 0)
        for ev in comp_events:
            all_events.extend(ev.to_midi_events(bpm=bpm, channel=0))

        # Bass (channel 1)
        for i, (pitch, start_sec) in enumerate(bass_notes):
            dur = 60.0 / bpm  # quarter note
            all_events.append({
                "type": "note_on", "note": pitch,
                "time": start_sec, "channel": 1, "velocity": 80,
            })
            all_events.append({
                "type": "note_off", "note": pitch,
                "time": start_sec + dur, "channel": 1, "velocity": 0,
            })

        # Sort by time
        all_events.sort(key=lambda e: (e["time"], 0 if e["type"] == "note_on" else 1))

        abs_time = 0
        for ev in all_events:
            delta = secs_to_ticks(ev["time"]) - abs_time
            abs_time += delta
            msg_type = "note_on" if ev["type"] == "note_on" else "note_off"
            track.append(mido.Message(
                msg_type, note=ev["note"], velocity=ev["velocity"],
                channel=ev["channel"], time=max(0, delta),
            ))

        filename = "autumn_leaves.mid"
        mid.save(filename)
        print(f"  Saved: {filename}")
    except ImportError:
        print("  (mido not installed — skipping MIDI file export)")
        print("  Install with: pip install mido")

    print("\n✅ Done!")


if __name__ == "__main__":
    main()
