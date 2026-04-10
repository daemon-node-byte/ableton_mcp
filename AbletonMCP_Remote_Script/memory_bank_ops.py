"""Project-root Memory Bank support for system-owned racks."""

from __future__ import absolute_import, print_function, unicode_literals

import hashlib
import json
import os
import re
from datetime import datetime
from uuid import uuid4


RACK_ENTRY_PATTERN = re.compile(
    r"<!-- ableton-mcp:rack-entry (?P<rack_id>[A-Za-z0-9_\-]+) -->\n"
    r"```json\n(?P<payload>.*?)\n```",
    re.DOTALL,
)


class MemoryBankOpsMixin(object):
    """Memory Bank commands and helpers."""

    def _memory_now_iso(self):
        return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

    def _memory_require_saved_session_path(self):
        session_path = str(getattr(self.song(), "file_path", "") or "").strip()
        if not session_path:
            raise ValueError("Memory Bank persistence requires saving the Live Set first")
        return session_path

    def _memory_project_root(self):
        return os.path.dirname(self._memory_require_saved_session_path())

    def _memory_base_dir(self):
        return os.path.join(self._memory_project_root(), ".ableton-mcp", "memory")

    def _memory_normalize_file_name(self, file_name):
        normalized = str(file_name or "").strip().replace("\\", "/")
        if not normalized:
            raise ValueError("file_name is required")
        if normalized.startswith("/") or normalized.startswith("~"):
            raise ValueError("file_name must be a relative path inside .ableton-mcp/memory")
        normalized = os.path.normpath(normalized).replace("\\", "/")
        if normalized == ".." or normalized.startswith("../"):
            raise ValueError("file_name must stay inside .ableton-mcp/memory")
        return normalized

    def _memory_file_path(self, file_name):
        normalized = self._memory_normalize_file_name(file_name)
        return os.path.join(self._memory_base_dir(), normalized)

    def _memory_ensure_layout(self):
        base_dir = self._memory_base_dir()
        sessions_dir = os.path.join(base_dir, "sessions")
        if not os.path.isdir(base_dir):
            os.makedirs(base_dir)
        if not os.path.isdir(sessions_dir):
            os.makedirs(sessions_dir)

    def _memory_read_text_file(self, path):
        if not os.path.exists(path):
            return ""
        with open(path, "r") as file_handle:
            return file_handle.read()

    def _memory_write_text_file(self, path, content):
        directory = os.path.dirname(path)
        if directory and not os.path.isdir(directory):
            os.makedirs(directory)
        with open(path, "w") as file_handle:
            file_handle.write(content)

    def _memory_project_id(self):
        session_path = self._memory_require_saved_session_path()
        return hashlib.sha1(session_path.encode("utf-8")).hexdigest()[:12]

    def _memory_track_type_label(self, track):
        if getattr(track, "has_midi_input", False):
            return "MIDI"
        return "Audio"

    def _memory_extract_control_groups(self, structure):
        groups = []
        for chain in list(structure.get("chains", []) or []):
            groups.append(
                {
                    "chain": chain["name"],
                    "path": chain["path"],
                    "devices": [device["name"] for device in list(chain.get("devices", []) or [])],
                }
            )
        return groups

    def _memory_rack_note_lines(self, entry):
        notes = list(entry.get("notes", []) or [])
        if not notes:
            return "- None"
        return "\n".join("- {}".format(note) for note in notes)

    def _memory_render_rack_entry(self, entry):
        structure = entry["structure"]
        lines = [
            "## Rack: {}".format(entry["rack_id"]),
            "",
            "- **Name**: {}".format(entry["name"]),
            "- **Track**: {} ({})".format(entry["track_index"], entry["track_name"]),
            "- **Type**: {}".format(entry["rack_type"]),
            "- **Rack Path**: `{}`".format(entry["rack_path"]),
            "- **Created**: {}".format(entry["created_at"]),
            "- **Updated**: {}".format(entry["updated_at"]),
            "- **Created By**: {}".format(entry["created_by"]),
            "- **Macro Count**: {}".format(int(entry.get("macro_count", 0))),
            "- **Imported**: {}".format("yes" if entry.get("imported") else "no"),
            "",
            "### Control Groups",
        ]

        control_groups = list(entry.get("control_groups", []) or [])
        if control_groups:
            for group in control_groups:
                lines.append(
                    "- **{}**: {}".format(group["chain"], ", ".join(group["devices"]) if group["devices"] else "empty")
                )
        else:
            lines.append("- None")

        lines.extend(
            [
                "",
                "### Notes",
                self._memory_rack_note_lines(entry),
                "",
                "<!-- ableton-mcp:rack-entry {} -->".format(entry["rack_id"]),
                "```json",
                json.dumps(entry, indent=2, sort_keys=True),
                "```",
            ]
        )
        if structure.get("macros"):
            lines.extend(["", "### Current Macros", ""])
            lines.append("| Index | Name | Value |")
            lines.append("|---|---|---|")
            for macro in structure["macros"]:
                lines.append("| {} | {} | {} |".format(macro["index"], macro["name"], macro["display_value"]))
        return "\n".join(lines)

    def _memory_load_rack_entries(self):
        self._memory_ensure_layout()
        racks_path = self._memory_file_path("racks.md")
        content = self._memory_read_text_file(racks_path)
        entries = []
        for match in RACK_ENTRY_PATTERN.finditer(content):
            payload = match.group("payload").strip()
            try:
                entry = json.loads(payload)
            except ValueError:
                continue
            entries.append(entry)
        return entries

    def _memory_write_rack_catalog(self, entries):
        self._memory_ensure_layout()
        now_iso = self._memory_now_iso()
        lines = ["# Rack Catalog", "", "Last Updated: {}".format(now_iso), ""]
        for index, entry in enumerate(entries):
            lines.append(self._memory_render_rack_entry(entry))
            if index != len(entries) - 1:
                lines.extend(["", "---", ""])
        lines.append("")
        self._memory_write_text_file(self._memory_file_path("racks.md"), "\n".join(lines))

    def _memory_write_project_summary(self, entries):
        song = self.song()
        lines = [
            "# Project: {}".format(os.path.basename(self._memory_project_root())),
            "",
            "- **File Path**: {}".format(self._memory_require_saved_session_path()),
            "- **Project ID**: `{}`".format(self._memory_project_id()),
            "- **Tempo**: {} BPM".format(getattr(song, "tempo", 0.0)),
            "- **Time Signature**: {}/{}".format(
                getattr(song, "signature_numerator", 4),
                getattr(song, "signature_denominator", 4),
            ),
            "",
            "## Track Overview",
            "",
            "| Index | Name | Type | Color |",
            "|---|---|---|---|",
        ]
        for index, track in enumerate(list(getattr(song, "tracks", []) or [])):
            lines.append(
                "| {} | {} | {} | {} |".format(
                    index,
                    track.name,
                    self._memory_track_type_label(track),
                    getattr(track, "color", 0),
                )
            )
        lines.extend(
            [
                "",
                "## MCP-Created Elements",
                "",
                "- Racks: {}".format(len(entries)),
            ]
        )
        self._memory_write_text_file(self._memory_file_path("project.md"), "\n".join(lines) + "\n")

    def _memory_write_track_summary(self, track_index, entries):
        track = self._get_track(track_index)
        matching_entries = [entry for entry in entries if int(entry["track_index"]) == int(track_index)]
        lines = [
            "# Track {}: {}".format(track_index, track.name),
            "",
            "- **Type**: {}".format(self._memory_track_type_label(track)),
            "- **Color**: {}".format(getattr(track, "color", 0)),
            "- **System-Owned Racks**: {}".format(len(matching_entries)),
            "",
            "## Rack References",
            "",
        ]
        if matching_entries:
            for entry in matching_entries:
                lines.append(
                    "- `{}`: {} at `{}`".format(entry["rack_id"], entry["name"], entry["rack_path"])
                )
        else:
            lines.append("- None")
        self._memory_write_text_file(
            self._memory_file_path("track_{}.md".format(track_index)),
            "\n".join(lines) + "\n",
        )

    def _memory_append_session_log(self, action, detail):
        self._memory_ensure_layout()
        session_date = datetime.utcnow().strftime("%Y-%m-%d")
        session_path = self._memory_file_path("sessions/{}.md".format(session_date))
        content = self._memory_read_text_file(session_path)
        if not content:
            content = "# Session Log {}\n\n".format(session_date)
        content += "- {} `{}`: {}\n".format(self._memory_now_iso(), action, detail)
        self._memory_write_text_file(session_path, content)

    def _memory_rewrite_support_files(self, entries):
        self._memory_write_rack_catalog(entries)
        self._memory_write_project_summary(entries)
        touched_tracks = sorted(set(int(entry["track_index"]) for entry in entries))
        for track_index in touched_tracks:
            self._memory_write_track_summary(track_index, entries)

    def _memory_find_rack_entry_by_path(self, track_index, rack_path):
        normalized_path = str(rack_path).strip()
        for entry in self._memory_load_rack_entries():
            if int(entry["track_index"]) == int(track_index) and entry["rack_path"] == normalized_path:
                return entry
        return None

    def _memory_path_is_prefix(self, prefix_path, candidate_path):
        prefix_parts = str(prefix_path).split()
        candidate_parts = str(candidate_path).split()
        return candidate_parts[: len(prefix_parts)] == prefix_parts

    def _memory_build_rack_entry(
        self,
        rack_id,
        track_index,
        rack_path,
        rack_type,
        blueprint=None,
        macro_labels=None,
        imported=False,
        existing_entry=None,
    ):
        track = self._get_track(track_index)
        structure = self._get_rack_structure({"track_index": track_index, "rack_path": rack_path})["rack"]
        existing_entry = existing_entry or {}
        created_at = existing_entry.get("created_at", self._memory_now_iso())
        created_by = existing_entry.get("created_by", "AbletonMCP")
        notes = [
            "Native macro mapping authoring is not confirmed in this repo yet.",
            "Structure and control metadata are authoritative only for system-owned or explicitly imported racks.",
        ]
        if imported:
            notes.append("Imported into the Memory Bank via refresh_rack_memory_entry.")
        entry = {
            "rack_id": rack_id,
            "system_owned": True,
            "imported": bool(imported),
            "track_index": int(track_index),
            "track_name": track.name,
            "rack_type": rack_type,
            "rack_path": rack_path,
            "name": structure["name"],
            "created_at": created_at,
            "updated_at": self._memory_now_iso(),
            "created_by": created_by,
            "blueprint": blueprint if blueprint is not None else existing_entry.get("blueprint"),
            "macro_labels": macro_labels if macro_labels is not None else existing_entry.get("macro_labels", []),
            "control_groups": self._memory_extract_control_groups(structure),
            "macro_count": len(list(structure.get("macros", []) or [])),
            "macro_snapshot": list(structure.get("macros", []) or []),
            "notes": notes,
            "structure": structure,
        }
        return entry

    def _memory_register_system_owned_rack(
        self,
        track_index,
        rack_path,
        rack_type,
        blueprint=None,
        macro_labels=None,
        imported=False,
    ):
        self._memory_require_saved_session_path()
        entries = self._memory_load_rack_entries()
        normalized_path = str(rack_path).strip()
        matching_entry = None
        for entry in entries:
            if int(entry["track_index"]) == int(track_index) and entry["rack_path"] == normalized_path:
                matching_entry = entry
                break

        rack_id = matching_entry["rack_id"] if matching_entry is not None else "rack_{}".format(uuid4().hex[:12])
        updated_entry = self._memory_build_rack_entry(
            rack_id,
            int(track_index),
            normalized_path,
            rack_type,
            blueprint=blueprint,
            macro_labels=macro_labels,
            imported=imported,
            existing_entry=matching_entry,
        )

        updated_entries = []
        replaced = False
        for entry in entries:
            if entry["rack_id"] == rack_id:
                updated_entries.append(updated_entry)
                replaced = True
            else:
                updated_entries.append(entry)
        if not replaced:
            updated_entries.append(updated_entry)
        self._memory_rewrite_support_files(updated_entries)
        self._memory_append_session_log(
            "rack_entry",
            "{} {} on track {} at {}".format(rack_id, updated_entry["name"], track_index, normalized_path),
        )
        return rack_id

    def _memory_refresh_related_rack_entries(self, track_index, changed_path):
        self._memory_require_saved_session_path()
        entries = self._memory_load_rack_entries()
        if not entries:
            return []
        updated_entries = []
        refreshed = []
        for entry in entries:
            if int(entry["track_index"]) == int(track_index) and self._memory_path_is_prefix(
                entry["rack_path"], changed_path
            ):
                updated_entries.append(
                    self._memory_build_rack_entry(
                        entry["rack_id"],
                        int(track_index),
                        entry["rack_path"],
                        entry["rack_type"],
                        blueprint=entry.get("blueprint"),
                        macro_labels=entry.get("macro_labels"),
                        imported=entry.get("imported", False),
                        existing_entry=entry,
                    )
                )
                refreshed.append(entry["rack_id"])
            else:
                updated_entries.append(entry)
        if refreshed:
            self._memory_rewrite_support_files(updated_entries)
            self._memory_append_session_log(
                "rack_refresh",
                "Updated related rack entries for track {} path {}".format(track_index, changed_path),
            )
        return refreshed

    def _read_memory_bank(self, params):
        self._memory_require_saved_session_path()
        path = self._memory_file_path(params["file_name"])
        if not os.path.exists(path):
            return "File {} does not exist.".format(params["file_name"])
        return self._memory_read_text_file(path)

    def _write_memory_bank(self, params):
        self._memory_require_saved_session_path()
        self._memory_ensure_layout()
        path = self._memory_file_path(params["file_name"])
        self._memory_write_text_file(path, str(params["content"]))
        self._memory_append_session_log("write_memory_bank", params["file_name"])
        return "Memory Bank file saved to {}".format(path)

    def _append_rack_entry(self, params):
        self._memory_require_saved_session_path()
        self._memory_ensure_layout()
        racks_path = self._memory_file_path("racks.md")
        content = self._memory_read_text_file(racks_path)
        if not content:
            content = "# Rack Catalog\n\nLast Updated: {}\n\n".format(self._memory_now_iso())
        content = content.rstrip() + "\n\n---\n\n" + str(params["rack_data"]).strip() + "\n"
        self._memory_write_text_file(racks_path, content)
        self._memory_append_session_log("append_rack_entry", "Manual append to racks.md")
        return "Rack entry saved to {}".format(racks_path)

    def _get_system_owned_racks(self):
        self._memory_require_saved_session_path()
        entries = self._memory_load_rack_entries()
        return {"count": len(entries), "racks": entries}

    def _refresh_rack_memory_entry(self, params):
        self._memory_require_saved_session_path()
        track_index = int(params["track_index"])
        rack_path = str(params["rack_path"]).strip()
        existing_entry = self._memory_find_rack_entry_by_path(track_index, rack_path)
        rack_device = self._get_rack_structure({"track_index": track_index, "rack_path": rack_path})["rack"]
        rack_type = rack_device.get("rack_type", "unknown")
        rack_id = self._memory_register_system_owned_rack(
            track_index,
            rack_path,
            rack_type,
            blueprint=existing_entry.get("blueprint") if existing_entry else None,
            macro_labels=existing_entry.get("macro_labels") if existing_entry else None,
            imported=existing_entry is None,
        )
        self._memory_refresh_related_rack_entries(track_index, rack_path)
        return {"rack_id": rack_id, "track_index": track_index, "rack_path": rack_path}
