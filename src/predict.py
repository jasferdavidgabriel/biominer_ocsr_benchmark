"""Run BioMiner on each PDF and collect its predicted SMILES."""

import os
import subprocess
from pathlib import Path
import pandas as pd


def run_biominer_on_pdf(pdf_path, paper_output_dir, biominer_cfg):
    """Launch BioMiner's command line script on a single PDF."""
    repo_dir = Path(biominer_cfg["repo_dir"]).resolve()
    command = [
        "python3", "example_open_source.py",
        f"--config_path={biominer_cfg['config_path']}",
        f"--pdf={Path(pdf_path).resolve()}",
        f"--output_dir={Path(paper_output_dir).resolve()}",
    ]
    # BioMiner expects to run from its own folder with PYTHONPATH set to it
    env = {**os.environ, "PYTHONPATH": str(repo_dir)}
    subprocess.run(command, cwd=repo_dir, env=env, check=True)


def read_biominer_smiles(output_file, smiles_col):
    """Read BioMiner's output table and return its distinct, non empty SMILES."""
    table = pd.read_csv(output_file)
    smiles = table[smiles_col].dropna().astype(str)
    return list(smiles.drop_duplicates())                    


def predict_all(pdf_paths, config):
    """Run BioMiner on every paper (skipping cached ones) and save raw predictions."""
    biominer_cfg = config["biominer"]
    raw_dir = Path(config["output"]["biominer_raw_dir"])
    rows = []

    for paper_id, pdf_path in pdf_paths.items():
        paper_output_dir = raw_dir / paper_id
        output_file = paper_output_dir / biominer_cfg["output_filename"]

        if not output_file.exists():               
            print(f"Running BioMiner on {paper_id}...")
            run_biominer_on_pdf(pdf_path, paper_output_dir, biominer_cfg)

        for smiles in read_biominer_smiles(output_file, biominer_cfg["smiles_column"]):
            rows.append({"paper_id": paper_id, "predicted_smiles": smiles})

    predictions = pd.DataFrame(rows)
    output_path = Path(config["output"]["raw_predictions_csv"])
    output_path.parent.mkdir(parents=True, exist_ok=True)   # create results/ if missing
    predictions.to_csv(output_path, index=False)
    return predictions
    
    return predictions