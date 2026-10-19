"""Load the ground truth CSV and locate the PDF for each paper."""

from pathlib import Path
import pandas as pd


def load_ground_truth(csv_path, id_col, smiles_col):
    """Read the answer key and drop rows that have no SMILES."""
    df = pd.read_csv(csv_path)                       
    df = df.dropna(subset=[smiles_col])
    df[id_col] = df[id_col].astype(str)
    return df


def find_pdfs(pdf_dir, paper_ids):
    """Map each paper ID to its PDF file, warning about any missing ones."""
    pdf_dir = Path(pdf_dir)
    pdf_paths = {}
    for paper_id in paper_ids:
        pdf_path = pdf_dir / f"{paper_id}.pdf"       
        if pdf_path.exists():
            pdf_paths[paper_id] = pdf_path
        else:
            print(f"Warning: no PDF found for paper {paper_id}")
    return pdf_paths


def load_dataset(config):
    """Return the ground truth table and the paper ID to PDF mapping."""
    data_cfg = config["data"]
    ground_truth = load_ground_truth(
        data_cfg["ground_truth_csv"], data_cfg["id_column"], data_cfg["smiles_column"]
    )
    paper_ids = ground_truth[data_cfg["id_column"]].unique()
    pdf_paths = find_pdfs(data_cfg["pdf_dir"], paper_ids)
    return ground_truth, pdf_paths