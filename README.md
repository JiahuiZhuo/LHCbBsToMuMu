# Search for the rare decay $B_s^0 \to \mu^+\mu^-$

A cut-based search for the very rare decay $B_s^0 \to \mu^+\mu^-$ using LHCb
open data. The analysis selects dimuon candidates, applies a cut-based
selection and extracts the $B_s^0$ peak with an unbinned maximum-likelihood
mass fit.

See [docs/analysis.md](docs/analysis.md) for the analysis details.

## Setup

With conda / micromamba:

```bash
conda env create -f environment.yml
conda activate bs2mumu
```

or with pip:

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
snakemake --cores 16
```

This runs the full pipeline:

1. `src/selection.py` — applies the selection to the input samples listed in
   `config.yaml` and writes `results/selected_data.root`;
2. `src/mass_fit.py` — fits the dimuon mass spectrum and writes
   `figures/mass_fit.png`;
3. `notebooks/mass_plot.ipynb` — executed headlessly by snakemake to produce
   `figures/mass_plot.png` (the same notebook can be opened interactively in
   Jupyter).

Input files are taken from the local paths in `config.yaml` when present,
otherwise they are read from the remote (xrootd) URLs — no manual download
is required.
To add more data, append new entries to `config.yaml` and rerun `snakemake`.
