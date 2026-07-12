#!/usr/bin/env python
"""
Unbinned extended maximum-likelihood fit of the selected dimuon candidates,
with four components:

  Bs -> mumu   Gaussian, mean and width floating (resolution ~23 MeV)
  B0 -> mumu   Gaussian, mean tied to m(Bs) - 87.2 MeV (PDG), same width
               (mostly B -> hh double-misID ends up here too)
  part. reco   wide Gaussian with the mean FIXED at the low mass edge --
               inside the fit range only its falling right half is visible
               (B -> h mu nu, Bc -> J/psi mu nu, ... missing a neutrino)
  combinatorial  exponential

The fit boundaries sit exactly on the display bin grid (40 MeV bins centred
on the Bs mass).  The Bs significance is estimated from the likelihood
ratio with respect to the fit with N(Bs) = 0.  Plotting is done with RooFit
(LHCb style and pull panel from roofit_helper.hpp).

Usage:
    python src/mass_fit.py [--input data/selected_data.root] [--output results/mass_fit.png]
"""
import argparse
import os
from math import sqrt

import ROOT

ROOT.gROOT.SetBatch(True)
ROOT.RooMsgService.instance().setGlobalKillBelow(ROOT.RooFit.WARNING)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT.gInterpreter.Declare(f'#include "{HERE}/roofit_helper.hpp"')

MBS, MBD = 5366.9, 5279.7  # PDG masses [MeV]
DM_PDG = MBS - MBD         # 87.2 MeV
BIN_W = 40.0
LO = MBS - 20 - 16 * BIN_W  # 4706.9, on the bin grid
HI = MBS + 20 + 15 * BIN_W  # 5986.9
NBINS = round((HI - LO) / BIN_W)

INPUT_TREE = "DecayTree"


def build_model(mass):
    """Assemble the 4-component extended pdf; return (model, parameter dict)."""
    p = {}
    p["mu_bs"] = ROOT.RooRealVar("mu_bs", "Bs mean", MBS, 5330, 5410)
    p["sigma"] = ROOT.RooRealVar("sigma", "resolution", 23.0, 10.0, 45.0)
    p["mu_bd"] = ROOT.RooFormulaVar("mu_bd", "Bd mean", f"mu_bs - {DM_PDG}",
                                    ROOT.RooArgList(p["mu_bs"]))
    p["sig_bs"] = ROOT.RooGaussian("sig_bs", "Bs signal", mass, p["mu_bs"], p["sigma"])
    p["sig_bd"] = ROOT.RooGaussian("sig_bd", "Bd peak", mass, p["mu_bd"], p["sigma"])

    p["mu_pr"] = ROOT.RooRealVar("mu_pr", "partreco mean", LO)
    p["sigma_pr"] = ROOT.RooRealVar("sigma_pr", "partreco width", 150, 30, 500)
    p["partreco"] = ROOT.RooGaussian("partreco", "partially reconstructed",
                                     mass, p["mu_pr"], p["sigma_pr"])

    p["slope"] = ROOT.RooRealVar("slope", "comb slope", -1e-3, -8e-3, 0.0)
    p["comb"] = ROOT.RooExponential("comb", "combinatorial", mass, p["slope"])

    p["n_bs"] = ROOT.RooRealVar("n_bs", "N(Bs)", 20, 0, 300)
    p["n_bd"] = ROOT.RooRealVar("n_bd", "N(Bd)", 5, 0, 150)
    p["n_pr"] = ROOT.RooRealVar("n_pr", "N(partreco)", 100, 0, 3000)
    p["n_cb"] = ROOT.RooRealVar("n_cb", "N(comb)", 1000, 0, 10000)
    model = ROOT.RooAddPdf(
        "model", "full model",
        ROOT.RooArgList(p["sig_bs"], p["sig_bd"], p["partreco"], p["comb"]),
        ROOT.RooArgList(p["n_bs"], p["n_bd"], p["n_pr"], p["n_cb"]))
    return model, p


def plot(mass, data, model, p, signif, output):
    ROOT.roofit_helper.lhcbStyle()

    frame = mass.frame(ROOT.RooFit.Bins(NBINS))
    data.plotOn(frame, ROOT.RooFit.Name("data"))
    model.plotOn(frame, ROOT.RooFit.Components("partreco"), ROOT.RooFit.Name("c_pr"),
                 ROOT.RooFit.LineColor(ROOT.kOrange + 1), ROOT.RooFit.LineStyle(ROOT.kDashed))
    model.plotOn(frame, ROOT.RooFit.Components("comb"), ROOT.RooFit.Name("c_cb"),
                 ROOT.RooFit.LineColor(ROOT.kBlue + 2), ROOT.RooFit.LineStyle(ROOT.kDotted))
    model.plotOn(frame, ROOT.RooFit.Components("sig_bd"), ROOT.RooFit.Name("c_bd"),
                 ROOT.RooFit.LineColor(ROOT.kGreen + 2), ROOT.RooFit.LineStyle(ROOT.kDashDotted))
    model.plotOn(frame, ROOT.RooFit.Components("sig_bs"), ROOT.RooFit.Name("c_bs"),
                 ROOT.RooFit.LineColor(ROOT.kRed), ROOT.RooFit.LineStyle(ROOT.kDashed))
    # the TOTAL curve is plotted last: pullHist() uses the last curve added
    model.plotOn(frame, ROOT.RooFit.Name("c_tot"), ROOT.RooFit.LineColor(ROOT.kAzure + 1))
    frame.GetXaxis().SetTitle("m(#mu^{+}#mu^{-}) [MeV/c^{2}]")
    frame.GetYaxis().SetTitle(f"Candidates / ({int(BIN_W)} MeV/c^{{2}})")
    # headroom above the data so the legend and fit summary do not overlap
    frame.SetMaximum(1.45 * frame.GetMaximum())
    frame.SetMinimum(0.0)

    canvas = ROOT.TCanvas("canvas", "", 900, 800)
    ROOT.roofit_helper.plot_with_pulls(frame, 0.25)

    # enlarge the axis fonts (plot_with_pulls sets 0.05)
    for axis in (frame.GetXaxis(), frame.GetYaxis()):
        axis.SetTitleSize(0.065)
        axis.SetLabelSize(0.06)
    frame.GetYaxis().SetTitleOffset(1.05)
    frame.GetXaxis().SetTitleOffset(1.0)

    # legend and fit summary (plot_with_pulls leaves the main pad current)
    leg = ROOT.TLegend(0.55, 0.55, 0.88, 0.92)
    leg.SetFillStyle(0)
    leg.AddEntry(frame.findObject("data"), "LHCb data", "ep")
    leg.AddEntry(frame.findObject("c_tot"), "Total fit", "l")
    leg.AddEntry(frame.findObject("c_bs"), "B_{s}^{0}#rightarrow#mu^{+}#mu^{-}", "l")
    leg.AddEntry(frame.findObject("c_bd"), "B^{0}#rightarrow#mu^{+}#mu^{-}", "l")
    leg.AddEntry(frame.findObject("c_pr"), "Partially reconstructed", "l")
    leg.AddEntry(frame.findObject("c_cb"), "Combinatorial", "l")
    leg.Draw()

    latex = ROOT.TLatex()
    latex.SetNDC()
    latex.SetTextSize(0.045)
    latex.DrawLatex(0.19, 0.86, f"N(B_{{s}}^{{0}}) = {p['n_bs'].getVal():.0f} #pm {p['n_bs'].getError():.0f}  ({signif:.1f}#sigma)")
    latex.DrawLatex(0.19, 0.79, f"m(B_{{s}}^{{0}}) = {p['mu_bs'].getVal():.1f} #pm {p['mu_bs'].getError():.1f} MeV/c^{{2}}")
    latex.DrawLatex(0.19, 0.72, f"#sigma = {p['sigma'].getVal():.1f} #pm {p['sigma'].getError():.1f} MeV/c^{{2}}")

    canvas.SaveAs(output)
    print(f"[mass_fit] saved {output}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="results/selected_data.root", help="selected candidates")
    parser.add_argument("--output", default="figures/mass_fit.png", help="output figure")
    args = parser.parse_args()

    infile = ROOT.TFile.Open(args.input)
    tree = infile.Get(INPUT_TREE)
    # the variable is named after the branch; entries outside [LO, HI] are
    # dropped on import
    mass = ROOT.RooRealVar("B_s0_MM", "m(#mu^{+}#mu^{-})", LO, HI, "MeV/c^{2}")
    data = ROOT.RooDataSet("data", "", ROOT.RooArgSet(mass), ROOT.RooFit.Import(tree))
    print(f"[mass_fit] {data.numEntries()} candidates in [{LO:.1f}, {HI:.1f}] MeV")

    model, p = build_model(mass)
    res = model.fitTo(data, ROOT.RooFit.Extended(True), ROOT.RooFit.Save(True),
                      ROOT.RooFit.PrintLevel(-1))
    nll = res.minNll()

    # likelihood-ratio significance vs the background-only hypothesis
    floated = ["mu_bs", "sigma", "sigma_pr", "slope", "n_bs", "n_bd", "n_pr", "n_cb"]
    snapshot = {k: (res.floatParsFinal().find(k).getVal(),
                    res.floatParsFinal().find(k).getError()) for k in floated}
    p["n_bs"].setVal(0); p["n_bs"].setConstant(True)
    p["mu_bs"].setConstant(True); p["sigma"].setConstant(True)
    res0 = model.fitTo(data, ROOT.RooFit.Extended(True), ROOT.RooFit.Save(True),
                       ROOT.RooFit.PrintLevel(-1))
    signif = sqrt(max(0.0, 2.0 * (res0.minNll() - nll)))

    # restore the signal-fit values and errors for printing/plotting
    for k, (val, err) in snapshot.items():
        p[k].setVal(val)
        p[k].setError(err)
    p["n_bs"].setConstant(False)
    p["mu_bs"].setConstant(False); p["sigma"].setConstant(False)

    print(f"[mass_fit] N(Bs)   = {p['n_bs'].getVal():6.1f} +- {p['n_bs'].getError():.1f}")
    print(f"[mass_fit] N(Bd)   = {p['n_bd'].getVal():6.1f} +- {p['n_bd'].getError():.1f}")
    print(f"[mass_fit] N(pr)   = {p['n_pr'].getVal():6.1f} +- {p['n_pr'].getError():.1f}")
    print(f"[mass_fit] N(comb) = {p['n_cb'].getVal():6.1f} +- {p['n_cb'].getError():.1f}")
    print(f"[mass_fit] m(Bs)   = {p['mu_bs'].getVal():7.1f} +- {p['mu_bs'].getError():.1f} MeV (PDG {MBS})")
    print(f"[mass_fit] sigma   = {p['sigma'].getVal():6.1f} +- {p['sigma'].getError():.1f} MeV")
    print(f"[mass_fit] Bs significance = {signif:.1f} sigma (likelihood ratio, stat. only)")

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    plot(mass, data, model, p, signif, args.output)


if __name__ == "__main__":
    main()
