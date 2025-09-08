#!/usr/bin/env python3
"""
Evaluation runner for the drowsy_detection algorithm.

Flow:
 1) Enumerate target core-lib outputs from ../DataWareHouse (02_core_lib_output).
 2) For each video/core output: read core CSV, map required columns, run DrowsyDetector per frame.
 3) Write algorithm outputs to ../DataWareHouse/03_algorithm_output/{algorithm_version}/{video_name}_result.csv
    and register in DataWareHouse (algorithm version and algorithm output).
 4) Evaluate predictions against tag intervals (ground_truth=1 for all intervals),
    export per-video results and overall summary under results/{run_id}/.

Notes:
 - Uses only Python stdlib to avoid extra dependencies.
 - Paths recorded in DataWareHouse must be relative to its DB root.
 - FPS is fixed at 30.0.
"""

from __future__ import annotations

import csv
import os
import sys
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Locate sibling projects (DataWareHouse, drowsy_detection)
# ---------------------------------------------------------------------------
THIS_FILE = Path(__file__).resolve()
PROJECT_ROOT = THIS_FILE.parents[1]
REPO_ROOT = PROJECT_ROOT.parent
DATA_WAREHOUSE_ROOT = (REPO_ROOT / "DataWareHouse").resolve()
DROWSY_DETECTION_ROOT = (REPO_ROOT / "drowsy_detection").resolve()

if str(DATA_WAREHOUSE_ROOT) not in sys.path:
    sys.path.insert(0, str(DATA_WAREHOUSE_ROOT))
if (DROWSY_DETECTION_ROOT / "src") and str(DROWSY_DETECTION_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(DROWSY_DETECTION_ROOT / "src"))

# Lazy imports after sys.path setup
try:
    import datawarehouse as dwh
except Exception as e:  # pragma: no cover
    raise RuntimeError(f"Failed to import DataWareHouse package: {e}\nSearched: {DATA_WAREHOUSE_ROOT}")

try:
    import drowsy_detection as dd
    from drowsy_detection.config.config import Config
    from drowsy_detection.config.validators import InputData, OutputData
    from drowsy_detection.core.drowsy_detector import DrowsyDetector
except Exception as e:  # pragma: no cover
    raise RuntimeError(f"Failed to import drowsy_detection package: {e}\nSearched: {DROWSY_DETECTION_ROOT}")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
FPS: float = 30.0
ALGO_OUTPUT_DIR_BASE = Path("03_algorithm_output")
CORE_OUTPUT_DIR_BASE = Path("02_core_lib_output")
RESULTS_DIR_BASE = PROJECT_ROOT / "results"

# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------
@dataclass
class CoreRow:
    frame_num: int
    left_eye_open: float
    right_eye_open: float
    face_confidence: float


@dataclass
class AlgoFrameResult:
    frame_num: int
    is_drowsy: int
    left_eye_closed: bool
    right_eye_closed: bool
    continuous_time: float
    error_code: Optional[str]


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def get_algorithm_version_and_hash() -> Tuple[str, str]:
    """Return (version, git_commit_hash) for drowsy_detection.

    - version: from drowsy_detection.__version__
    - commit hash: git rev-parse HEAD executed in drowsy_detection repo
    """
    version = getattr(dd, "__version__", "0.0.0")
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(DROWSY_DETECTION_ROOT),
            capture_output=True,
            text=True,
            check=True,
        )
        commit_hash = result.stdout.strip()
    except Exception:
        commit_hash = ""  # If not a git repo or git not available
    return version, commit_hash


def ensure_parent_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def find_core_csv(core_output_path_rel: str) -> Optional[Path]:
    """Given a core_lib_output path (recorded as relative), find the CSV file.

    The DB field name is *_dir but real value may be a file path. This resolves both cases.
    Returns absolute Path within DataWareHouse repo, or None if not found.
    """
    abs_path = (DATA_WAREHOUSE_ROOT / core_output_path_rel).resolve()
    if abs_path.is_file() and abs_path.suffix.lower() == ".csv":
        return abs_path
    if abs_path.is_dir():
        # Prefer files containing 'analysis' else first CSV
        csv_files = sorted(abs_path.rglob("*.csv"))
        if not csv_files:
            return None
        for p in csv_files:
            if "analysis" in p.name.lower():
                return p
        return csv_files[0]
    return None


def read_core_csv_rows(path: Path) -> Iterable[CoreRow]:
    """Yield CoreRow from the core lib CSV."""
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        # Column mapping (case-insensitive keys)
        for row in reader:
            key = {k.strip().lower(): v for k, v in row.items()}
            try:
                frame_num = int(float(key.get("frame", "0")))
                left_open = float(key.get("leye_openness", 0.0))
                right_open = float(key.get("reye_openness", 0.0))
                face_conf = float(key.get("confidence", 0.0))
            except Exception:
                continue
            yield CoreRow(
                frame_num=frame_num,
                left_eye_open=left_open,
                right_eye_open=right_open,
                face_confidence=face_conf,
            )


def write_algorithm_output_csv(path: Path, results: List[AlgoFrameResult]) -> None:
    """Write per-frame algorithm outputs to CSV."""
    ensure_parent_dir(path)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "frame_num",
            "is_drowsy",
            "left_eye_closed",
            "right_eye_closed",
            "continuous_time",
            "error_code",
        ])
        for r in results:
            writer.writerow([
                r.frame_num,
                r.is_drowsy,
                1 if r.left_eye_closed else 0,
                1 if r.right_eye_closed else 0,
                f"{r.continuous_time:.6f}",
                r.error_code or "",
            ])


def get_video_name_from_video_dir(video_dir_rel: str) -> str:
    p = Path(video_dir_rel)
    name = p.name
    if p.suffix:
        return p.stem
    return name


def evaluate_video(
    algo_csv_path: Path,
    video_id: int,
    run_dir: Path,
    data_name: str,
) -> Tuple[int, int]:
    """Evaluate per tags for one video and write data_name.csv.

    Returns (num_correct, num_tasks).
    """
    # Load algorithm outputs
    frame_to_pred: Dict[int, int] = {}
    with algo_csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                frame = int(float(row.get("frame_num", "0")))
                is_drowsy = int(float(row.get("is_drowsy", "-1")))
            except Exception:
                continue
            frame_to_pred[frame] = is_drowsy

    # Fetch tags from DataWareHouse
    tags = dwh.get_video_tags(video_id)

    # Evaluate: ground_truth is always 1
    out_path = run_dir / f"{data_name}.csv"
    ensure_parent_dir(out_path)

    num_correct = 0
    num_tasks = 0

    with out_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["task_id", "predicted", "ground_truth", "correct", "notes"])
        for tag in tags:
            task_id = int(tag["task_ID"]) if "task_ID" in tag else int(tag.get("task_id", -1))
            start = int(tag["start"]) if "start" in tag else 0
            end = int(tag["end"]) if "end" in tag else start

            # Collect predictions within [start, end)
            preds: List[int] = []
            for frame in range(start, end):
                v = frame_to_pred.get(frame)
                if v in (0, 1):
                    preds.append(v)
            if not preds:
                writer.writerow([task_id, "", 1, "", "no valid frames in interval"])
                continue

            predicted = 1 if any(v == 1 for v in preds) else 0
            correct = 1 if predicted == 1 else 0

            writer.writerow([task_id, predicted, 1, correct, ""])
            num_tasks += 1
            if correct:
                num_correct += 1

    return num_correct, num_tasks


def write_summary(
    run_dir: Path,
    overall_accuracy: float,
    total_correct: int,
    total_tasks: int,
    per_dataset: Dict[str, Dict[str, int]],
    algorithm_version: str,
    algorithm_commit_hash: str,
) -> None:
    path = run_dir / "summary.csv"
    ensure_parent_dir(path)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "overall_accuracy",
            "total_num_correct",
            "total_num_tasks",
            "run_id",
            "created_at",
            "algorithm_version",
            "algorithm_commit_hash",
            "per_dataset",
        ])
        created_at = datetime.now().astimezone().isoformat()
        run_id = run_dir.name
        # per_dataset as JSON-like string (simple)
        per_dataset_str = str(per_dataset).replace("'", '"')
        writer.writerow([
            f"{overall_accuracy:.4f}",
            total_correct,
            total_tasks,
            run_id,
            created_at,
            algorithm_version,
            algorithm_commit_hash,
            per_dataset_str,
        ])


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    # Timestamped run directory
    run_id = datetime.now().strftime("%Y%m%d-%H%M%S")
    run_dir = RESULTS_DIR_BASE / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    # Algorithm meta
    algorithm_version, algorithm_commit_hash = get_algorithm_version_and_hash()

    # Ensure algorithm version exists in DWH
    algo_rec = dwh.find_algorithm_by_version(algorithm_version)
    if algo_rec is None:
        update_info = f"auto-registered by evaluation_engine at {datetime.now().isoformat()}"
        algo_id = dwh.create_algorithm_version(
            version=algorithm_version,
            update_info=update_info,
            commit_hash=algorithm_commit_hash or "0" * 40,
        )
    else:
        algo_id = int(algo_rec["algorithm_ID"]) if "algorithm_ID" in algo_rec else int(algo_rec.get("algorithm_id"))

    # Enumerate core lib outputs (scope: all available)
    core_outputs = dwh.list_core_lib_outputs()
    if not core_outputs:
        print("No core_lib_outputs found in DataWareHouse.")
        return 0

    total_correct = 0
    total_tasks = 0
    per_dataset: Dict[str, Dict[str, int]] = {}

    # Create detector
    config = Config()
    detector = DrowsyDetector(config)
    detector.set_frame_rate(FPS)

    for rec in core_outputs:
        core_output_id = int(rec["core_lib_output_ID"]) if "core_lib_output_ID" in rec else int(rec.get("core_lib_output_id"))
        video_id = int(rec["video_ID"]) if "video_ID" in rec else int(rec.get("video_id"))
        core_dir_rel = rec["core_lib_output_dir"]
        video_dir_rel = rec["video_dir"]

        # Resolve core CSV
        core_csv_abs = find_core_csv(core_dir_rel)
        if core_csv_abs is None:
            print(f"Skip: core CSV not found for core_lib_output_ID={core_output_id}")
            continue

        # Prepare algorithm output path
        video_name = get_video_name_from_video_dir(video_dir_rel)
        algo_rel_path = ALGO_OUTPUT_DIR_BASE / algorithm_version / f"{video_name}_result.csv"
        algo_abs_path = (DATA_WAREHOUSE_ROOT / algo_rel_path).resolve()

        # Run detection per frame
        results: List[AlgoFrameResult] = []
        detector.reset()
        for row in read_core_csv_rows(core_csv_abs):
            # Build InputData and update
            try:
                inp = InputData(
                    frame_num=row.frame_num,
                    left_eye_open=row.left_eye_open,
                    right_eye_open=row.right_eye_open,
                    face_confidence=row.face_confidence,
                )
                out: OutputData = detector.update(inp)
            except Exception:
                # Create error-like output for traceability
                results.append(
                    AlgoFrameResult(
                        frame_num=row.frame_num,
                        is_drowsy=-1,
                        left_eye_closed=False,
                        right_eye_closed=False,
                        continuous_time=0.0,
                        error_code="INPUT_ERROR",
                    )
                )
                continue

            results.append(
                AlgoFrameResult(
                    frame_num=out.frame_num,
                    is_drowsy=out.is_drowsy,
                    left_eye_closed=out.left_eye_closed,
                    right_eye_closed=out.right_eye_closed,
                    continuous_time=out.continuous_time,
                    error_code=out.error_code,
                )
            )

        # Write algorithm output CSV
        write_algorithm_output_csv(algo_abs_path, results)

        # Register algorithm output in DWH
        try:
            dwh.create_algorithm_output(
                algorithm_id=algo_id,
                core_lib_output_id=core_output_id,
                output_dir=str(algo_rel_path).replace("\\", "/"),
            )
        except Exception as e:
            print(f"Warning: failed to register algorithm output for video_id={video_id}: {e}")

        # Evaluate per tags
        num_correct, num_tasks = evaluate_video(
            algo_csv_path=algo_abs_path,
            video_id=video_id,
            run_dir=run_dir,
            data_name=video_name,
        )

        per_dataset[video_name] = {"num_correct": num_correct, "num_tasks": num_tasks}
        total_correct += num_correct
        total_tasks += num_tasks

    overall_accuracy = (total_correct / total_tasks) if total_tasks > 0 else 0.0
    write_summary(
        run_dir=run_dir,
        overall_accuracy=overall_accuracy,
        total_correct=total_correct,
        total_tasks=total_tasks,
        per_dataset=per_dataset,
        algorithm_version=algorithm_version,
        algorithm_commit_hash=algorithm_commit_hash,
    )

    print(
        f"Done. overall_accuracy={overall_accuracy:.4f}, total_correct={total_correct}, total_tasks={total_tasks}\n"
        f"Results: {run_dir}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
