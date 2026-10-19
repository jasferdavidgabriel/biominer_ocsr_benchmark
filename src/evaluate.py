"""Score predicted SMILES against the ground truth using RDKit."""

from rdkit import Chem, DataStructs, RDLogger
from rdkit.Chem import rdFingerprintGenerator
import pandas as pd

RDLogger.DisableLog("rdApp.*")  # hide RDKit warnings about unparseable SMILES
MORGAN_GENERATOR = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)


def canonicalize(smiles):
    """Return RDKit canonical SMILES, or None if the SMILES is invalid."""
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:                              
        return None
    return Chem.MolToSmiles(mol)


def tanimoto(smiles_a, smiles_b):
    """Tanimoto similarity between Morgan fingerprints of two valid SMILES."""
    fp_a = MORGAN_GENERATOR.GetFingerprint(Chem.MolFromSmiles(smiles_a))
    fp_b = MORGAN_GENERATOR.GetFingerprint(Chem.MolFromSmiles(smiles_b))
    return DataStructs.TanimotoSimilarity(fp_a, fp_b)


def score_paper(true_smiles_list, predicted_smiles_list):
    """Best match every true molecule against all valid predictions from the same paper."""
    valid_preds = [c for c in (canonicalize(s) for s in predicted_smiles_list) if c]
    rows = []
    for true_smiles in true_smiles_list:
        true_canon = canonicalize(true_smiles)
        best_pred, best_score = None, 0.0
        if true_canon is not None:
            for pred in valid_preds:
                score = tanimoto(true_canon, pred)
                if score > best_score:
                    best_pred, best_score = pred, score
        rows.append({
            "true_canonical": true_canon,
            "best_prediction": best_pred,
            "exact_match": true_canon is not None and true_canon in valid_preds,  
            "best_tanimoto": round(best_score, 4),
        })
    return rows, valid_preds

def evaluate_all(ground_truth, predictions, id_col, name_col, smiles_col):
    """Score every paper; return a per molecule table and an overall summary."""
    predictions = predictions.copy()
    predictions["paper_id"] = predictions["paper_id"].astype(str)  # match ground truth ID type

    per_molecule, num_predictions, num_valid, num_correct = [], 0, 0, 0
    for paper_id, paper_truth in ground_truth.groupby(id_col):
        paper_preds = predictions.loc[predictions["paper_id"] == paper_id, "predicted_smiles"].tolist()
        rows, valid_preds = score_paper(paper_truth[smiles_col].tolist(), paper_preds)

        for row, name in zip(rows, paper_truth[name_col]):
            row.update({"paper_id": paper_id, "molecule_name": name})
            per_molecule.append(row)

        true_set = {row["true_canonical"] for row in rows}
        num_predictions += len(paper_preds)
        num_valid += len(valid_preds)
        num_correct += sum(1 for pred in valid_preds if pred in true_set)

    results = pd.DataFrame(per_molecule)
    summary = {
        "num_papers": int(results["paper_id"].nunique()),
        "num_true_molecules": int(len(results)),
        "num_predictions": int(num_predictions),
        "valid_prediction_rate": round(num_valid / num_predictions, 4) if num_predictions else 0.0,
        "exact_match_recall": round(float(results["exact_match"].mean()), 4),
        "precision": round(num_correct / num_predictions, 4) if num_predictions else 0.0,
        "mean_best_tanimoto": round(float(results["best_tanimoto"].mean()), 4),
    }
    return results, summary