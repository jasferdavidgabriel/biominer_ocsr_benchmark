# BioMiner SMILES Extraction Benchmark

Benchmarking pipeline for evaluating how accurately [BioMiner](https://github.com/jiaxianyan/BioMiner) extracts molecular structures (SMILES) from scientific PDFs.

## What this code does

The pipeline runs in four stages:

1. **Load:** reads the ground truth CSV (one row per molecule, linked to its paper by `paperID`) and locates each paper's PDF.
2. **Predict:** runs BioMiner on each PDF and collects every predicted SMILES. Outputs are cached per paper, so reruns skip completed papers.
3. **Evaluate:** canonicalizes all SMILES with RDKit, then best matches each true molecule against the predictions from the same paper.
4. **Save:** writes a per molecule results CSV and a summary JSON to `results/`.

## Repository structure

```
biominer_ocsr_benchmark/
    run_benchmark.py      # Entry point: runs the full pipeline
    config.yaml           # All paths and column names (no hardcoded paths in code)
    requirements.txt      # Python dependencies
    src/
        load_data.py      # Ground truth loading and PDF lookup
        predict.py        # BioMiner wrapper with per paper caching
        evaluate.py       # Canonicalization, Tanimoto, best match scoring, summary metrics
    data/                 # Dataset goes here (not tracked by Git)
    results/              # Output CSV and JSON files
```

## Metrics

| Metric | Meaning |
|---|---|
| `exact_match_recall` | Fraction of true molecules whose canonical SMILES appears among the paper's predictions |
| `precision` | Fraction of all predictions that exactly match a true molecule in that paper |
| `mean_best_tanimoto` | Average Tanimoto similarity (Morgan fingerprints, radius 2, 2048 bits) between each true molecule and its closest prediction; gives partial credit for near misses |
| `valid_prediction_rate` | Fraction of predictions RDKit can parse as valid chemistry |

## Setup

```bash
git clone <this repo url>
cd biominer_ocsr_benchmark
conda create -n biobench python=3.10 -y
conda activate biobench
pip install -r requirements.txt
```

## Data

Place the dataset in `data/` (it is excluded from Git):

```
data/
    ground_truth.csv      # columns: paperID, name of molecule, canonical_SMILES
    pdfs/
        1.pdf, 2.pdf, ... # one PDF per paperID, named <paperID>.pdf
```

Column names and paths can be changed in `config.yaml` without editing code.

## Running

**Sanity check (no GPU needed).** Scores the ground truth against itself to validate the evaluation code. All metrics should equal 1.0.

```bash
python run_benchmark.py --sanity-check
```

**Full BioMiner benchmark (GPU required).** BioMiner requires NVIDIA GPUs and its own environment. Follow the installation steps in the [BioMiner README](https://github.com/jiaxianyan/BioMiner), clone it next to this repo (or update `biominer.repo_dir` in `config.yaml`), then run:

```bash
python run_benchmark.py
```

## Results

| File | Contents |
|---|---|
| `results/sanity_check_summary.json` | Validation run: ground truth vs. itself (all metrics 1.0, as expected) |
| `results/sanity_check_per_molecule.csv` | Per molecule scores for the validation run |
| `results/biominer_*` | Produced by the full BioMiner run |

**Note:** the sanity check validates the evaluation code only. It does not measure BioMiner's performance.

## Known limitations and next steps

1. The exact name of BioMiner's output file (`biominer.output_filename` in `config.yaml`) should be verified on the first real run.
2. BioMiner's main output lists molecules alongside bioactivity values, so molecules without reported bioactivity may not appear in its predictions, which could lower recall.
3. Full BioMiner results will be generated on a GPU environment.