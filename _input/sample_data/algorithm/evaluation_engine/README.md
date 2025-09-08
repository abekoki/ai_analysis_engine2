# Evaluation Engine

This module evaluates the drowsy_detection algorithm using core library outputs stored in ../DataWareHouse.

- Input scope: ../DataWareHouse/02_core_lib_output
- Per-video algorithm outputs: ../DataWareHouse/03_algorithm_output/{algorithm_version}/{video_name}_result.csv
- Per-run evaluation results: results/{run_id}/summary.csv and results/{run_id}/{data_name}.csv

Run:
```powershell
uv run python evaluation_engine/run_evaluation.py
```
