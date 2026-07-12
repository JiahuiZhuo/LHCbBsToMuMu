#!/usr/bin/env python
"""
Cut-based selection for the Bs -> mu+ mu- analysis.

Reads the input samples from config.yaml (preferring the local path when the
file exists, falling back to the remote xrootd URL otherwise), applies the
preselection of LHCb-ANA-2016-038 (Table 6), the muon-PID requirement of its
Eq.(5) and the per-year tightened topology cuts, and writes the selected
candidates of all samples into a single output ROOT file.

Usage:
    python src/selection.py [--config config.yaml] [--output data/selected_data.root]
"""
import argparse
import os
import subprocess
import tempfile

import yaml
import ROOT

# ---------------------------------------------------------------------------
# selection definition
# ---------------------------------------------------------------------------

# stripping-like preselection (analysis-note Table 6) + muon PID (Eq. 5)
PRESELECTION = " && ".join([
    "muplus_isMuon && muminus_isMuon",
    "muplus_TRACK_CHI2NDOF < 3 && muminus_TRACK_CHI2NDOF < 3",
    "muplus_TRACK_GhostProb < 0.3 && muminus_TRACK_GhostProb < 0.3",
    "muplus_PT > 250 && muplus_PT < 40000 && muminus_PT > 250 && muminus_PT < 40000",
    "muplus_P < 500000 && muminus_P < 500000",
    "muplus_MINIPCHI2 > 25 && muminus_MINIPCHI2 > 25",
    "B_s0_ENDVERTEX_CHI2 < 9",
    "B_s0_FDCHI2_OWNPV > 225",
    "B_s0_IPCHI2_OWNPV < 25",
    "B_s0_PT > 500",
    "PIDmu_p > 0.5 && PIDmu_m > 0.5",
])

# BDT substitute: tightened vertex/pointing/kinematic cuts (tuned on data
# sidebands), common part + per-year part.  Run 2 (2017) needs harder cuts
# and a dimuon trigger to reach the Run 1 background level.
SELECTION_COMMON = " && ".join([
    "B_s0_DIRA_OWNPV > 0.9999975",
    "B_s0_ENDVERTEX_CHI2 < 4",
    "B_s0_IPCHI2_OWNPV < 9",
    "B_s0_PT > 2000",
    "muplus_PT > 1000 && muminus_PT > 1000",
])
SELECTION_PER_YEAR = {
    2012: "B_s0_FDCHI2_OWNPV > 500",
    2017: ("Hlt1DiMuonHighMassDecision != 0 && B_s0_FDCHI2_OWNPV > 1000 && "
           "muplus_MINIPCHI2 > 50 && muminus_MINIPCHI2 > 50"),
}

# branches written to the output (plus the derived PID variables and year)
OUTPUT_COLUMNS = [
    "B_s0_MM", "B_s0_MMERR", "B_s0_PT", "B_s0_P",
    "B_s0_IPCHI2_OWNPV", "B_s0_DIRA_OWNPV", "B_s0_ENDVERTEX_CHI2",
    "B_s0_FDCHI2_OWNPV", "B_s0_FD_OWNPV",
    "muplus_PT", "muminus_PT", "muplus_MINIPCHI2", "muminus_MINIPCHI2",
    "PIDmu_p", "PIDmu_m",
    "runNumber", "eventNumber", "year",
]

OUTPUT_TREE = "DecayTree"


# ---------------------------------------------------------------------------
def resolve_path(sample):
    """Prefer the local file when it exists, else fall back to the remote URL."""
    if os.path.exists(sample["local"]):
        return sample["local"], "local"
    return sample["remote"], "remote"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="config.yaml", help="configuration file")
    parser.add_argument("--output", default="results/selected_data.root", help="output ROOT file")
    parser.add_argument("--threads", type=int, default=16, help="number of threads")
    args = parser.parse_args()

    with open(args.config) as f:
        config = yaml.safe_load(f)

    ROOT.EnableImplicitMT(args.threads)
    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)

    tree = config["input_data"]["tree"]
    partial_files = []
    with tempfile.TemporaryDirectory(dir=os.path.dirname(args.output) or ".") as tmpdir:
        for sample in config["input_data"]["samples"]:
            year = sample["year"]
            if year not in SELECTION_PER_YEAR:
                raise KeyError(f"no per-year selection defined for year {year} "
                               f"(sample {sample['name']}) -- add it to SELECTION_PER_YEAR")
            path, origin = resolve_path(sample)
            print(f"[selection] {sample['name']}: using {origin} file {path}")

            df = ROOT.RDataFrame(tree, path)
            df = (df.Define("PIDmu_p", "muplus_ProbNNmu*(1.-muplus_ProbNNp)*(1.-muplus_ProbNNk)")
                    .Define("PIDmu_m", "muminus_ProbNNmu*(1.-muminus_ProbNNp)*(1.-muminus_ProbNNk)")
                    .Define("year", f"int({year})")
                    .Filter(PRESELECTION, "preselection")
                    .Filter(SELECTION_COMMON, "selection (common)")
                    .Filter(SELECTION_PER_YEAR[year], f"selection ({year})"))
            partial = os.path.join(tmpdir, f"{sample['name']}.root")
            n = df.Snapshot(OUTPUT_TREE, partial, OUTPUT_COLUMNS).Count().GetValue()
            print(f"[selection] {sample['name']}: {n} candidates selected")
            partial_files.append(partial)

        subprocess.run(["hadd", "-f", args.output] + partial_files,
                       check=True, capture_output=True)

    n_total = ROOT.RDataFrame(OUTPUT_TREE, args.output).Count().GetValue()
    print(f"[selection] wrote {n_total} candidates to {args.output}")


if __name__ == "__main__":
    main()
