"""Run the full benchmark: load data, predict with BioMiner, score, and save results.

Usage:
    python run_benchmark.py                  # full run (needs a GPU machine with BioMiner)
    python run_benchmark.py --sanity-check   # validate evaluation code, no BioMiner needed
"""

import argparse
import json
from pathlib import Path

import pandas as pd
import yaml

from src.evaluate import evaluate_all
from src.load_data import load_dataset
from src.predict import predict_all


def parse_args():
    parser = argparse.ArgumentParser(description="Benchmark BioMiner SMILES extraction.")
    parser.add_argument("--config", default="config.yaml", help="Path to the config file")
    parser.add_argument(
        "--sanity-check",
        action="store_true",
        help="Score the ground truth against itself (expected: 100%% match) to validate the metrics",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    with open(args.config) as f:
        config = yaml.safe_load(f)
    data_cfg = config["data"]

    # 1. Load the answer key and locate PDFs
    ground_truth, pdf_paths = load_dataset(config)

    # 2. Get predictions (either from BioMiner or, for validation, the ground truth itself)
    if args.sanity_check:
        run_name = "sanity_check"
        predictions = pd.DataFrame({
            "paper_id": ground_truth[data_cfg["id_column"]],
            "predicted_smiles": ground_truth[data_cfg["smiles_column"]],
        })
    else:
        run_name = "biominer"
        predictions = predict_all(pdf_paths, config)

    # 3. Score
    per_molecule, summary = evaluate_all(
        ground_truth, predictions,
        data_cfg["id_column"], data_cfg["name_column"], data_cfg["smiles_column"],
    )

    # 4. Save results
    results_dir = Path(config["output"]["results_dir"])
    results_dir.mkdir(parents=True, exist_ok=True)
    per_molecule.to_csv(results_dir / f"{run_name}_per_molecule.csv", index=False)
    with open(results_dir / f"{run_name}_summary.json", "w") as f:
        json.dump(summary, f, indent=2)                    # Blank: write a dict to a file

    print(f"Saved results to {results_dir}/")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()