from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Literal

from mido import Message, MidiFile, MidiTrack, MetaMessage, bpm2tempo


PedalState = Literal["off", "on"]

DATA_ROOT = Path(__file__).resolve().parent
REPO_ROOT = DATA_ROOT.parent

DEFAULT_INSTRUMENT = "Pianoteq 9"
DEFAULT_PRESET = "NY Steinway D Classical"
DEFAULT_SAMPLE_RATE = 48_000
DEFAULT_BPM = 120
DEFAULT_TICKS_PER_BEAT = 480
DEFAULT_HOLD_BEATS = 6
DEFAULT_TAIL_BEATS = 10
DEFAULT_TAIL_SECONDS = 5.0
DEFAULT_CHANNEL = 0

PHRASE_MANIFEST = REPO_ROOT / "data" / "evaluation" / "datasets" / "pasp_phrase_eval_v1.json"
PHRASE_EVENTS_DIR = REPO_ROOT / "data" / "evaluation" / "datasets" / "events"
REGISTER_SET = (
    REPO_ROOT / "examples" / "calibration" / "pasp_register_a3_c5_reference_set.json"
)
REFERENCES_MANIFEST = DATA_ROOT / "pianoteq_references" / "metadata" / "manifest.jsonl"


@dataclass(frozen=True)
class SampleMetadata:
    sample_id: str
    midi_path: str
    wav_path: str

    instrument: str
    preset: str
    sample_rate: int

    midi_note: int
    note_name: str
    velocity: int
    pedal: PedalState

    bpm: int
    ticks_per_beat: int
    hold_beats: int
    tail_beats: int
    hold_seconds: float
    tail_seconds: float

    channel: int
    sustain_cc: int | None
    sustain_value: int | None


NOTE_NAMES_SHARP = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def midi_note_to_name(midi_note: int) -> str:
    octave = midi_note // 12 - 1
    name = NOTE_NAMES_SHARP[midi_note % 12]
    return f"{name}{octave}"


def seconds_from_beats(beats: int, bpm: int) -> float:
    return 60.0 * beats / bpm


def seconds_to_ticks(time_s: float, bpm: int, ticks_per_beat: int) -> int:
    return int(round(time_s * bpm / 60.0 * ticks_per_beat))


def velocity_norm_to_midi(velocity_norm: float) -> int:
    return max(1, min(127, round(float(velocity_norm) * 127)))


def make_dirs(root: Path) -> dict[str, Path]:
    dirs = {
        "midi": root / "midi",
        "wav": root / "wav",
        "metadata": root / "metadata",
    }
    for path in dirs.values():
        path.mkdir(parents=True, exist_ok=True)
    return dirs


def write_single_note_midi(
    midi_path: Path,
    *,
    note: int,
    velocity: int,
    pedal: PedalState,
    bpm: int,
    ticks_per_beat: int,
    hold_beats: int,
    tail_beats: int,
    channel: int,
) -> None:
    mid = MidiFile(ticks_per_beat=ticks_per_beat)
    track = MidiTrack()
    mid.tracks.append(track)

    track.append(MetaMessage("set_tempo", tempo=bpm2tempo(bpm), time=0))

    if pedal == "on":
        track.append(
            Message(
                "control_change",
                control=64,
                value=127,
                channel=channel,
                time=0,
            )
        )

    track.append(
        Message(
            "note_on",
            note=note,
            velocity=velocity,
            channel=channel,
            time=0,
        )
    )

    track.append(
        Message(
            "note_off",
            note=note,
            velocity=0,
            channel=channel,
            time=hold_beats * ticks_per_beat,
        )
    )

    if pedal == "on":
        track.append(
            Message(
                "control_change",
                control=64,
                value=0,
                channel=channel,
                time=tail_beats * ticks_per_beat,
            )
        )
        track.append(MetaMessage("end_of_track", time=ticks_per_beat))
    else:
        track.append(MetaMessage("end_of_track", time=tail_beats * ticks_per_beat))

    mid.save(midi_path)


def _phrase_event_message(
    event: dict[str, Any],
    channel: int,
) -> Message | None:
    etype = str(event.get("type", "")).strip().lower()
    if etype == "note_on":
        note = int(event["note"])
        vel = event.get("velocity_norm", event.get("velocity", 0.5))
        if isinstance(vel, (int, float)) and vel > 1.0:
            midi_vel = max(1, min(127, int(vel)))
        else:
            midi_vel = velocity_norm_to_midi(float(vel))
        return Message("note_on", note=note, velocity=midi_vel, channel=channel, time=0)
    if etype == "note_off":
        note = int(event["note"])
        return Message("note_off", note=note, velocity=0, channel=channel, time=0)
    if etype == "pedal_down":
        return Message("control_change", control=64, value=127, channel=channel, time=0)
    if etype == "pedal_up":
        return Message("control_change", control=64, value=0, channel=channel, time=0)
    return None


def write_phrase_midi(
    midi_path: Path,
    events: list[dict[str, Any]],
    *,
    duration_s: float,
    bpm: int = DEFAULT_BPM,
    ticks_per_beat: int = DEFAULT_TICKS_PER_BEAT,
    tail_seconds: float = DEFAULT_TAIL_SECONDS,
    channel: int = DEFAULT_CHANNEL,
) -> None:
    sorted_events = sorted(events, key=lambda e: float(e.get("time_s", e.get("time", 0.0))))

    last_event_time = 0.0
    for event in sorted_events:
        last_event_time = max(last_event_time, float(event.get("time_s", event.get("time", 0.0))))
    end_time_s = max(float(duration_s), last_event_time + tail_seconds)

    scheduled: list[tuple[int, Message | MetaMessage]] = []
    scheduled.append((0, MetaMessage("set_tempo", tempo=bpm2tempo(bpm), time=0)))

    for event in sorted_events:
        time_s = float(event.get("time_s", event.get("time", 0.0)))
        tick = seconds_to_ticks(time_s, bpm, ticks_per_beat)
        msg = _phrase_event_message(event, channel)
        if msg is not None:
            scheduled.append((tick, msg))

    end_tick = seconds_to_ticks(end_time_s, bpm, ticks_per_beat)
    scheduled.append((end_tick, MetaMessage("end_of_track", time=0)))

    mid = MidiFile(ticks_per_beat=ticks_per_beat)
    track = MidiTrack()
    mid.tracks.append(track)

    prev_tick = 0
    for tick, msg in scheduled:
        delta = max(0, tick - prev_tick)
        msg.time = delta
        track.append(msg)
        prev_tick = tick

    midi_path.parent.mkdir(parents=True, exist_ok=True)
    mid.save(midi_path)


def _manifest_record(
    sample_id: str,
    midi_path: Path,
    wav_path: str,
    *,
    instrument: str = DEFAULT_INSTRUMENT,
    preset: str = DEFAULT_PRESET,
    sample_rate: int = DEFAULT_SAMPLE_RATE,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    record: dict[str, Any] = {
        "sample_id": sample_id,
        "midi_path": str(midi_path.relative_to(DATA_ROOT)),
        "wav_path": wav_path,
        "instrument": instrument,
        "preset": preset,
        "sample_rate": sample_rate,
    }
    if extra:
        record.update(extra)
    return record


def generate_phrase_plan(
    *,
    manifest_path: Path = PHRASE_MANIFEST,
    events_dir: Path = PHRASE_EVENTS_DIR,
    midi_root: Path = DATA_ROOT / "pianoteq_phrases",
    instrument: str = DEFAULT_INSTRUMENT,
    preset: str = DEFAULT_PRESET,
    sample_rate: int = DEFAULT_SAMPLE_RATE,
    bpm: int = DEFAULT_BPM,
    ticks_per_beat: int = DEFAULT_TICKS_PER_BEAT,
    tail_seconds: float = DEFAULT_TAIL_SECONDS,
    channel: int = DEFAULT_CHANNEL,
) -> list[dict[str, Any]]:
    raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    midi_dir = midi_root / "midi"
    midi_dir.mkdir(parents=True, exist_ok=True)

    records: list[dict[str, Any]] = []

    for item in raw.get("items", []):
        item_id = str(item["id"])
        events_path = events_dir / f"{item_id}.json"
        if not events_path.is_file():
            raise FileNotFoundError(f"Missing events for phrase {item_id}: {events_path}")

        events = json.loads(events_path.read_text(encoding="utf-8"))
        if not isinstance(events, list):
            raise ValueError(f"Expected event list in {events_path}")

        midi_path = midi_dir / f"{item_id}.mid"
        wav_path = f"data/references/piano_phrases/audio/{item_id}.wav"
        duration_s = float(item.get("duration_s", 4.0))

        write_phrase_midi(
            midi_path,
            events,
            duration_s=duration_s,
            bpm=bpm,
            ticks_per_beat=ticks_per_beat,
            tail_seconds=tail_seconds,
            channel=channel,
        )

        records.append(
            _manifest_record(
                item_id,
                midi_path,
                wav_path,
                instrument=instrument,
                preset=preset,
                sample_rate=sample_rate,
                extra={"phrase_id": item_id, "duration_s": duration_s},
            )
        )

    print(f"Generated {len(records)} phrase MIDI files under {midi_dir}")
    return records


def generate_register_plan(
    *,
    reference_set_path: Path = REGISTER_SET,
    midi_root: Path = DATA_ROOT / "pianoteq_register",
    instrument: str = DEFAULT_INSTRUMENT,
    preset: str = DEFAULT_PRESET,
    sample_rate: int = DEFAULT_SAMPLE_RATE,
    bpm: int = DEFAULT_BPM,
    ticks_per_beat: int = DEFAULT_TICKS_PER_BEAT,
    hold_beats: int = DEFAULT_HOLD_BEATS,
    tail_beats: int = DEFAULT_TAIL_BEATS,
    channel: int = DEFAULT_CHANNEL,
) -> list[dict[str, Any]]:
    raw = json.loads(reference_set_path.read_text(encoding="utf-8"))
    items = raw.get("reference_set", {}).get("items", [])
    midi_dir = midi_root / "midi"
    midi_dir.mkdir(parents=True, exist_ok=True)

    records: list[dict[str, Any]] = []

    for item in items:
        midi_note = int(item["midi_note"])
        velocity_norm = float(item["velocity_norm"])
        midi_velocity = velocity_norm_to_midi(velocity_norm)
        wav_path = str(item["reference"])
        sample_id = Path(wav_path).stem

        midi_path = midi_dir / f"{sample_id}.mid"

        write_single_note_midi(
            midi_path,
            note=midi_note,
            velocity=midi_velocity,
            pedal="off",
            bpm=bpm,
            ticks_per_beat=ticks_per_beat,
            hold_beats=hold_beats,
            tail_beats=tail_beats,
            channel=channel,
        )

        records.append(
            _manifest_record(
                sample_id,
                midi_path,
                wav_path,
                instrument=instrument,
                preset=preset,
                sample_rate=sample_rate,
                extra={
                    "midi_note": midi_note,
                    "velocity_norm": velocity_norm,
                    "midi_velocity": midi_velocity,
                },
            )
        )

    print(f"Generated {len(records)} register MIDI files under {midi_dir}")
    return records


def write_references_manifest(
    records: list[dict[str, Any]],
    manifest_path: Path = REFERENCES_MANIFEST,
) -> Path:
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with manifest_path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(f"Wrote manifest: {manifest_path} ({len(records)} records)")
    return manifest_path


def generate_dataset_plan(
    *,
    root: Path = Path("pianoteq_dataset"),
    instrument: str = DEFAULT_INSTRUMENT,
    preset: str = DEFAULT_PRESET,
    sample_rate: int = DEFAULT_SAMPLE_RATE,
    notes: Iterable[int] = range(21, 109),
    velocities: Iterable[int] = (
        1, 4, 8, 12, 16,
        24, 32, 40, 48, 56,
        64, 72, 80, 88, 96,
        104, 112, 120, 127,
    ),
    pedal_states: Iterable[PedalState] = ("off", "on"),
    bpm: int = DEFAULT_BPM,
    ticks_per_beat: int = DEFAULT_TICKS_PER_BEAT,
    hold_beats: int = DEFAULT_HOLD_BEATS,
    tail_beats: int = DEFAULT_TAIL_BEATS,
    channel: int = DEFAULT_CHANNEL,
) -> list[SampleMetadata]:
    dirs = make_dirs(root)
    manifest_path = dirs["metadata"] / "manifest.jsonl"

    records: list[SampleMetadata] = []

    with manifest_path.open("w", encoding="utf-8") as f:
        for note in notes:
            note_name = midi_note_to_name(note)

            for velocity in velocities:
                if not 1 <= velocity <= 127:
                    raise ValueError(f"Invalid MIDI velocity: {velocity}")

                for pedal in pedal_states:
                    sample_id = f"note_{note:03d}_{note_name}_vel_{velocity:03d}_pedal_{pedal}"

                    midi_path = dirs["midi"] / f"{sample_id}.mid"
                    wav_path = dirs["wav"] / f"{sample_id}.wav"

                    write_single_note_midi(
                        midi_path,
                        note=note,
                        velocity=velocity,
                        pedal=pedal,
                        bpm=bpm,
                        ticks_per_beat=ticks_per_beat,
                        hold_beats=hold_beats,
                        tail_beats=tail_beats,
                        channel=channel,
                    )

                    record = SampleMetadata(
                        sample_id=sample_id,
                        midi_path=str(midi_path),
                        wav_path=str(wav_path),
                        instrument=instrument,
                        preset=preset,
                        sample_rate=sample_rate,
                        midi_note=note,
                        note_name=note_name,
                        velocity=velocity,
                        pedal=pedal,
                        bpm=bpm,
                        ticks_per_beat=ticks_per_beat,
                        hold_beats=hold_beats,
                        tail_beats=tail_beats,
                        hold_seconds=seconds_from_beats(hold_beats, bpm),
                        tail_seconds=seconds_from_beats(tail_beats, bpm),
                        channel=channel,
                        sustain_cc=64 if pedal == "on" else None,
                        sustain_value=127 if pedal == "on" else None,
                    )

                    f.write(json.dumps(asdict(record), ensure_ascii=False) + "\n")
                    records.append(record)

    print(f"Generated {len(records)} MIDI files")
    print(f"Wrote manifest: {manifest_path}")
    return records


def build_reference_manifest(
    *,
    phrases: bool = False,
    register: bool = False,
) -> Path:
    records: list[dict[str, Any]] = []
    if phrases:
        records.extend(generate_phrase_plan())
    if register:
        records.extend(generate_register_plan())
    if not records:
        raise ValueError("No reference plans selected (use --phrases and/or --register)")
    return write_references_manifest(records)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate MIDI files for Pianoteq rendering")
    parser.add_argument(
        "--phrases",
        action="store_true",
        help="Generate phrase eval MIDI + manifest rows",
    )
    parser.add_argument(
        "--register",
        action="store_true",
        help="Generate register panel MIDI + manifest rows",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Generate phrases and register references (default when no flags)",
    )
    parser.add_argument(
        "--single-notes",
        action="store_true",
        help="Generate full single-note pianoteq_dataset (legacy, large)",
    )
    args = parser.parse_args(argv)

    if args.single_notes:
        generate_dataset_plan()
        return 0

    phrases = args.phrases or args.all
    register = args.register or args.all
    if not phrases and not register:
        phrases = True
        register = True

    build_reference_manifest(phrases=phrases, register=register)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
