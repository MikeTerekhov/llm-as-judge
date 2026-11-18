"""Local metadata-only history for synthetic judge experiments."""
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import re

from .model_comparison import ComparisonReport

MODEL = re.compile(r"^[A-Za-z0-9._:/-]{1,100}$")
RUN = re.compile(r"^[A-Za-z0-9_-]{1,64}$")

@dataclass(frozen=True)
class ExperimentRecord:
    run_id: str
    recorded_at: str
    model: str
    total: int
    model_returned: int
    disagreement_count: int
    disagreement_rate: float | None
    outcomes: tuple[dict[str, str | bool | None], ...]

def record_from_report(run_id: str, model: str, report: ComparisonReport,
                       *, recorded_at: datetime | None = None) -> ExperimentRecord:
    if not RUN.fullmatch(run_id) or not MODEL.fullmatch(model):
        raise ValueError("Invalid run or model identifier")
    now = recorded_at or datetime.now(timezone.utc)
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("Timestamp must be timezone aware")
    outcomes = tuple({"example_id": row.example_id, "disposition": row.disposition,
                      "model_verdict": row.model_verdict, "disagreement": row.disagreement}
                     for row in report.rows)
    return ExperimentRecord(run_id, now.isoformat(), model, report.total,
                            report.model_returned, report.disagreement_count,
                            report.disagreement_rate, outcomes)

def append_record(path: str | Path, record: ExperimentRecord) -> None:
    """Append JSONL metadata; local operator must protect file permissions."""
    target = Path(path)
    if target.is_symlink():
        raise ValueError("History path must not be a symlink")
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        with target.open(encoding="utf-8") as stream:
            for line in stream:
                if json.loads(line).get("run_id") == record.run_id:
                    raise ValueError("Duplicate run ID")
    with target.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(asdict(record), sort_keys=True) + "\n")

def read_history(path: str | Path) -> tuple[ExperimentRecord, ...]:
    target = Path(path)
    if target.is_symlink():
        raise ValueError("History path must not be a symlink")
    if not target.exists():
        return ()
    records = []
    with target.open(encoding="utf-8") as stream:
        for line in stream:
            obj = json.loads(line)
            if set(obj) != set(ExperimentRecord.__dataclass_fields__):
                raise ValueError("Unexpected history schema")
            obj["outcomes"] = tuple(obj["outcomes"])
            records.append(ExperimentRecord(**obj))
    return tuple(records)

def summarize_history(records: tuple[ExperimentRecord, ...]) -> tuple[dict, ...]:
    return tuple({"run_id": r.run_id, "recorded_at": r.recorded_at, "model": r.model,
                  "model_returned": r.model_returned,
                  "disagreement_rate": r.disagreement_rate} for r in records)
