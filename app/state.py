import json
import os
from datetime import datetime
from typing import Any, Dict, Optional


VALID_STATUSES = frozenset({"downloaded", "parsed", "calendar_written", "skipped", "failed"})


class StateManager:
    def __init__(self, state_file: str = "data/state.json"):
        self._path = state_file
        self._data: Dict[str, Any] = self._load()

    def _load(self) -> Dict[str, Any]:
        if os.path.exists(self._path):
            try:
                with open(self._path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if "processed" not in data:
                    data["processed"] = {}
                return data
            except (json.JSONDecodeError, OSError):
                return {"processed": {}, "version": "1"}
        os.makedirs(os.path.dirname(os.path.abspath(self._path)), exist_ok=True)
        initial = {"processed": {}, "version": "1"}
        self._write(initial)
        return initial

    def _write(self, data: Dict[str, Any]) -> None:
        os.makedirs(os.path.dirname(os.path.abspath(self._path)), exist_ok=True)
        tmp = self._path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(tmp, self._path)

    def is_processed(self, message_id: str) -> bool:
        return message_id in self._data["processed"]

    def get(self, message_id: str) -> Optional[Dict[str, Any]]:
        return self._data["processed"].get(message_id)

    def record(
        self,
        message_id: str,
        status: str,
        filename: str = "",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        if status not in VALID_STATUSES:
            raise ValueError(f"Invalid status '{status}'. Must be one of {sorted(VALID_STATUSES)}")
        self._data["processed"][message_id] = {
            "status": status,
            "filename": filename,
            "timestamp": datetime.now().isoformat(),
            "details": details or {},
        }
        self._write(self._data)

    def all_entries(self) -> Dict[str, Any]:
        return dict(self._data["processed"])
