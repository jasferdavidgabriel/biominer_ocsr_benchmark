"""Summarize the ground truth dataset for the benchmark report."""
import yaml
import matplotlib.pyplot as plt
from rdkit import Chem
from src.load_data import load_dataset

config = yaml.safe_load(open("config.yaml"))
ground_truth, _ = load_dataset(config)
id_col, smiles_col = config["data"]["id_column"], config["data"]["smiles_column"]

mols = ground_truth[smiles_col].apply(Chem.MolFromSmiles)
ground_truth["heavy_atoms"] = mols.apply(lambda m: m.GetNumHeavyAtoms() if m else None)
ground_truth["has_stereo"] = ground_truth[smiles_col].str.contains(r"@|/|\\", regex=True)

per_paper = ground_truth.groupby(id_col).agg(
    molecules=(smiles_col, "size"),
    stereo_pct=("has_stereo", "mean"),
    median_heavy_atoms=("heavy_atoms", "median"),
).sort_index(key=lambda s: s.astype(int))
per_paper["stereo_pct"] = (per_paper["stereo_pct"] * 100).round(1)
print(per_paper)
print(f"Overall: {len(ground_truth)} molecules, {ground_truth['has_stereo'].mean()*100:.1f}% with stereochemistry")

fig, axes = plt.subplots(1, 2, figsize=(10, 3.5))
per_paper["molecules"].plot(kind="bar", ax=axes[0], title="Molecules per paper")
axes[0].set_xlabel("Paper ID"); axes[0].set_ylabel("Molecules")
ground_truth["heavy_atoms"].plot(kind="hist", bins=20, ax=axes[1], title="Molecule size")
axes[1].set_xlabel("Heavy atoms"); axes[1].set_ylabel("Count")
plt.tight_layout()
plt.savefig("results/dataset_overview.png", dpi=200)