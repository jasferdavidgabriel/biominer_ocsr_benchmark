"""Score predicted SMILES against the ground truth using RDKit."""

from rdkit import Chem, DataStructs, RDLogger
from rdkit.Chem import rdFingerprintGenerator

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