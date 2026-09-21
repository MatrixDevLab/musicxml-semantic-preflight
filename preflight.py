#!/usr/bin/env python3
"""Small, dependency-free MusicXML semantic preflight witness."""

from __future__ import annotations

import argparse
import json
import sys
import zipfile
import xml.etree.ElementTree as ET
from fractions import Fraction
from pathlib import Path
from typing import Any, Iterable


SPANNER_TYPES = {"slur", "tied", "octave-shift"}
OPEN_TYPES = {"start", "up", "down"}


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def children(element: ET.Element, name: str) -> list[ET.Element]:
    return [child for child in element if local_name(child.tag) == name]


def descendants(element: ET.Element, name: str) -> Iterable[ET.Element]:
    return (node for node in element.iter() if local_name(node.tag) == name)


def location(part_id: str, measure: ET.Element, element: ET.Element | None = None) -> dict[str, str]:
    result = {"part": part_id, "measure": measure.get("number", "?")}
    if element is not None:
        result["element"] = local_name(element.tag)
    return result


def finding(
    code: str,
    status: str,
    message: str,
    where: dict[str, str],
    **details: Any,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "code": code,
        "status": status,
        "message": message,
        "location": where,
    }
    if details:
        result["details"] = details
    return result


def read_musicxml(path: Path) -> bytes:
    data = path.read_bytes()
    if path.suffix.lower() != ".mxl":
        return data
    with zipfile.ZipFile(path) as archive:
        names = sorted(archive.namelist())
        container_name = "META-INF/container.xml"
        if container_name in names:
            container = ET.fromstring(archive.read(container_name))
            roots = [
                node.get("full-path")
                for node in container.iter()
                if local_name(node.tag) == "rootfile" and node.get("full-path")
            ]
            if roots:
                return archive.read(roots[0])
        candidates = [name for name in names if name.lower().endswith((".xml", ".musicxml"))]
        if not candidates:
            raise ValueError("MXL archive contains no XML score")
        return archive.read(candidates[0])


def parse_fraction(value: str | None) -> Fraction | None:
    if value is None:
        return None
    try:
        return Fraction(value)
    except (ValueError, ZeroDivisionError):
        return None


def measure_events(measure: ET.Element) -> list[ET.Element]:
    return [child for child in measure if local_name(child.tag) in {"note", "backup", "forward"}]


def check_spanners(root: ET.Element) -> tuple[str, list[dict[str, Any]]]:
    findings: list[dict[str, Any]] = []
    for part in descendants(root, "part"):
        part_id = part.get("id", "?")
        open_spanners: dict[tuple[str, str], tuple[ET.Element, dict[str, str]]] = {}
        for measure in children(part, "measure"):
            for element in measure.iter():
                kind = local_name(element.tag)
                if kind not in SPANNER_TYPES:
                    continue
                span_type = element.get("type", "").lower()
                if span_type not in SPANNER_TYPES | {"continue", "stop", "start", "up", "down"}:
                    continue
                number = element.get("number", "1")
                key = (kind, number)
                where = location(part_id, measure, element)
                if span_type in OPEN_TYPES:
                    if key in open_spanners:
                        findings.append(finding(
                            "paired-spanner-duplicate-start",
                            "error",
                            f"{kind} {number} starts before its previous span closed",
                            where,
                            number=number,
                        ))
                    else:
                        open_spanners[key] = (element, where)
                elif span_type == "continue":
                    if key not in open_spanners:
                        findings.append(finding(
                            "paired-spanner-orphan-continue",
                            "error",
                            f"{kind} {number} continues without an open span",
                            where,
                            number=number,
                        ))
                elif span_type == "stop":
                    if key not in open_spanners:
                        findings.append(finding(
                            "paired-spanner-orphan-stop",
                            "error",
                            f"{kind} {number} stops without an open span",
                            where,
                            number=number,
                        ))
                    else:
                        del open_spanners[key]
        for (kind, number), (_, where) in sorted(open_spanners.items()):
            findings.append(finding(
                "paired-spanner-unclosed-start",
                "error",
                f"{kind} {number} starts but never stops",
                where,
                number=number,
            ))
    return status_for(findings), findings


def check_measure_durations(root: ET.Element) -> tuple[str, list[dict[str, Any]]]:
    findings: list[dict[str, Any]] = []
    for part in descendants(root, "part"):
        part_id = part.get("id", "?")
        divisions: Fraction | None = None
        expected: Fraction | None = None
        for measure in children(part, "measure"):
            attributes = next((child for child in measure if local_name(child.tag) == "attributes"), None)
            if attributes is not None:
                div_node = next((child for child in attributes if local_name(child.tag) == "divisions"), None)
                if div_node is not None:
                    divisions = parse_fraction(div_node.text)
                time_node = next((child for child in attributes if local_name(child.tag) == "time"), None)
                if time_node is not None:
                    beats = next((child for child in time_node if local_name(child.tag) == "beats"), None)
                    beat_type = next((child for child in time_node if local_name(child.tag) == "beat-type"), None)
                    beats_value = parse_fraction(beats.text if beats is not None else None)
                    beat_type_value = parse_fraction(beat_type.text if beat_type is not None else None)
                    if beats_value is not None and beat_type_value not in (None, 0):
                        expected = beats_value * 4 / beat_type_value * divisions if divisions else None

            events = measure_events(measure)
            if not events:
                continue
            voices = {
                (next((child.text for child in event if local_name(child.tag) == "voice"), None) or "1")
                for event in events
                if local_name(event.tag) == "note" and next(
                    (child.text for child in event if local_name(child.tag) == "voice"), None
                ) is not None
            }
            if len(voices) > 1:
                findings.append(finding(
                    "measure-duration-unknown",
                    "unknown",
                    "multiple voices require voice-aware timing not proven by this witness",
                    location(part_id, measure),
                ))
                continue
            if expected is None or divisions is None or divisions <= 0:
                findings.append(finding(
                    "measure-duration-unknown",
                    "unknown",
                    "measure duration cannot be computed from the available time/division fields",
                    location(part_id, measure),
                ))
                continue
            cursor = Fraction(0)
            for event in events:
                kind = local_name(event.tag)
                duration_node = next((child for child in event if local_name(child.tag) == "duration"), None)
                duration = parse_fraction(duration_node.text if duration_node is not None else None)
                if duration is None:
                    continue
                if kind == "backup":
                    cursor -= duration
                elif kind == "forward":
                    cursor += duration
                elif kind == "note":
                    is_chord = any(local_name(child.tag) == "chord" for child in event)
                    is_grace = any(local_name(child.tag) == "grace" for child in event)
                    if not is_chord and not is_grace:
                        cursor += duration
            if cursor != expected:
                findings.append(finding(
                    "measure-duration-mismatch",
                    "error",
                    "single-voice event duration does not match the active time signature",
                    location(part_id, measure),
                    actual=str(cursor),
                    expected=str(expected),
                ))
    return status_for(findings), findings


def check_playback_jumps(root: ET.Element) -> tuple[str, list[dict[str, Any]]]:
    markers = {local_name(node.tag) for node in root.iter() if local_name(node.tag) in {"segno", "coda", "fine"}}
    findings: list[dict[str, Any]] = []
    jump_targets = {"dalsegno": "segno", "tocoda": "coda", "fine": "fine"}
    for part in descendants(root, "part"):
        part_id = part.get("id", "?")
        for measure in children(part, "measure"):
            for sound in descendants(measure, "sound"):
                for attribute, target in jump_targets.items():
                    value = sound.get(attribute)
                    if value not in {"yes", "true", "1"}:
                        continue
                    if target not in markers:
                        findings.append(finding(
                            "playback-jump-target-missing",
                            "warning",
                            f"explicit {attribute} jump has no explicit {target} marker",
                            location(part_id, measure, sound),
                            attribute=attribute,
                            target=target,
                        ))
    return status_for(findings), findings


def status_for(findings: list[dict[str, Any]]) -> str:
    statuses = {item["status"] for item in findings}
    if "error" in statuses:
        return "error"
    if "warning" in statuses:
        return "warning"
    if "unknown" in statuses:
        return "unknown"
    return "pass"


def run(path: Path) -> dict[str, Any]:
    try:
        root = ET.fromstring(read_musicxml(path))
    except (OSError, ValueError, zipfile.BadZipFile, ET.ParseError) as exc:
        return {
            "schema_version": 1,
            "file": path.name,
            "status": "error",
            "checks": [{
                "name": "parse",
                "status": "error",
                "findings": [finding("parse-failure", "error", str(exc), {"file": path.name})],
            }],
        }
    checks = []
    for name, checker in (
        ("paired-spanners", check_spanners),
        ("measure-durations", check_measure_durations),
        ("playback-jumps", check_playback_jumps),
    ):
        status, findings = checker(root)
        checks.append({"name": name, "status": status, "findings": findings})
    overall = status_for([finding for check in checks for finding in check["findings"]])
    return {"schema_version": 1, "file": path.name, "status": overall, "checks": checks}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path, help="MusicXML (.xml/.musicxml) or compressed .mxl file")
    args = parser.parse_args(argv)
    result = run(args.path)
    json.dump(result, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 1 if result["status"] == "error" else 0


if __name__ == "__main__":
    raise SystemExit(main())
