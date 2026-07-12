# Analysis description

## 1. Physics motivation

$`B_s^0 \to \mu^+\mu^-`$ is a flavour-changing neutral-current decay: it is
forbidden at tree level in the Standard Model (SM) and proceeds only through
loop diagrams, with an additional helicity suppression of the dimuon final
state. The SM prediction for the time-integrated branching fraction is

$$\mathcal{B}(B_s^0 \to \mu^+\mu^-)_{\rm SM} = (3.66 \pm 0.14) \times 10^{-9},$$

i.e. about four decays per billion $`B_s^0`$ mesons. Measurements by LHCb, CMS
and ATLAS are consistent with this expectation; the current measured value is
$`\mathcal{B}(B_s^0 \to \mu^+\mu^-) \simeq 3.1 \times 10^{-9}`$ with a
precision of about 10%. Because new heavy particles (e.g. extended Higgs
sectors) could enhance or suppress this rate significantly, the decay is one
of the most powerful indirect probes of physics beyond the SM. Such new
physics could also supply the extra CP violation needed to explain the cosmic
excess of matter over antimatter.

The partner decay $`B^0 \to \mu^+\mu^-`$ is further CKM-suppressed,
$`\mathcal{B}_{\rm SM} \approx 1.0 \times 10^{-10}`$, and has not been observed
to date; only upper limits exist. With the branching fractions this small,
the expected signal yield in any subsample of data is modest — the analysis
is therefore designed around background suppression, and the pipeline is
meant to be rerun as more data is added to `config.yaml`.

## 2. Input data

The analysis uses LHCb open data: ntuples of dimuon candidates (tree
`BsMuMu/DecayTree`), listed in `config.yaml` together with their data-taking
year and magnet polarity. Candidates are formed from two oppositely charged
muon tracks fitted to a common vertex; the invariant-mass window is wide
enough to cover the signal region and extended sidebands.

## 3. Selection

The published LHCb analyses combine a loose preselection with a multivariate
classifier (BDT) built from vertex, pointing and isolation information.
Without simulated signal to train such a classifier, this analysis replaces
the BDT with tightened cuts on the most discriminating variables, tuned on
the data sidebands.

### 3.1 Preselection

Following the stripping/preselection of the published analysis:

| Variable | Requirement |
| --- | --- |
| muon identification | isMuon for both tracks |
| track quality | $`\chi^2_{\rm track}/\mathrm{ndf} < 3`$, ghost probability $`< 0.3`$ |
| muon momentum | $`p_T(\mu) \in (0.25, 40)`$ GeV/$`c`$, $`p(\mu) < 500`$ GeV/$`c`$ |
| muon impact parameter | $`\chi^2_{\rm IP}(\mu) > 25`$ (both muons) |
| secondary vertex | $`\chi^2_{\rm vtx} < 9`$ |
| flight distance | $`\chi^2_{\rm FD} > 225`$ |
| $`B`$ pointing | $`\chi^2_{\rm IP}(B) < 25`$ |
| $`B`$ momentum | $`p_T(B) > 0.5`$ GeV/$`c`$ |

### 3.2 Muon identification

Hadron misidentification (in particular $`B \to h^+h^{\prime-}`$ with both
hadrons misidentified as muons, which peaks in the signal region) is
suppressed with the combined neural-net PID requirement

$$\mathrm{PID}_\mu \equiv \mathrm{ProbNN}_\mu \times (1-\mathrm{ProbNN}_p) \times (1-\mathrm{ProbNN}_K) > 0.5$$

applied to both muons. The $`\mathrm{ProbNN}_K`$ factor rejects
$`B \to h^+h^{\prime-}`$, while $`\mathrm{ProbNN}_p`$ targets
$`\Lambda_b^0 \to p\mu^-\bar{\nu}_\mu`$.

### 3.3 Topology cuts (BDT substitute)

Common to all years:

| Variable | Requirement |
| --- | --- |
| pointing angle | $`\mathrm{DIRA} > 0.9999975`$ |
| secondary vertex | $`\chi^2_{\rm vtx} < 4`$ |
| $`B`$ impact parameter | $`\chi^2_{\rm IP}(B) < 9`$ |
| $`B`$ momentum | $`p_T(B) > 2`$ GeV/$`c`$ |
| muon momentum | $`p_T(\mu) > 1`$ GeV/$`c`$ |

The selection is tuned **per data-taking year**: at 13 TeV the higher pile-up
and the roughly doubled $`b\bar{b}`$ cross-section give a substantially larger
combinatorial background than at 7–8 TeV, so Run 2 samples require harder
cuts and a dimuon trigger:

| Variable | Run 1 (2011–2012) | Run 2 (2015–2018) |
| --- | --- | --- |
| trigger | — | Hlt1DiMuonHighMass |
| flight distance | $`\chi^2_{\rm FD} > 500`$ | $`\chi^2_{\rm FD} > 1000`$ |
| muon impact parameter | $`\chi^2_{\rm IP}(\mu) > 25`$ | $`\chi^2_{\rm IP}(\mu) > 50`$ |

The per-year cuts live in `SELECTION_PER_YEAR` in `src/selection.py`; adding
a sample from a new year requires adding the corresponding entry there.

## 4. Mass fit

The dimuon invariant-mass spectrum is fitted with an unbinned extended
maximum-likelihood fit over a range from about 4.7 to 6.0 GeV/$`c^2`$, with
four components:

| Component | Shape | Parameters |
| --- | --- | --- |
| $`B_s^0 \to \mu^+\mu^-`$ | Gaussian | mean and width floating |
| $`B^0 \to \mu^+\mu^-`$ | Gaussian | mean tied to $`m(B_s^0) - 87.2`$ MeV (PDG $`\Delta m`$), width shared with the $`B_s^0`$ |
| partially reconstructed | right half of a wide Gaussian | mean fixed at the low edge of the fit range, width floating |
| combinatorial | exponential | slope floating |

**Signal peaks.** The expected peak positions are the PDG masses
$`m(B_s^0) = 5366.9`$ MeV/$`c^2`$ and $`m(B^0) = 5279.7`$ MeV/$`c^2`$;
the LHCb dimuon mass resolution at these masses is
$`\sigma \approx 23`$ MeV/$`c^2`$, so the two peaks
(separated by $`87.2`$ MeV/$`c^2`$,
i.e. $`\sim 4\sigma`$) are partially resolved. A fitted mean and width
compatible with these values is a useful closure check. The $`B^0`$ component
is included so that its possible contribution does not bias the $`B_s^0`$
peak; given the tiny branching fraction, candidates in the $`B^0`$ window are
expected to be dominated by residual $`B \to h^+h^{\prime-}`$
double-misidentification and combinatorial background.

**Partially reconstructed background.** Semileptonic decays such as
$`B^0 \to \pi^- \mu^+ \nu_\mu`$, $`B_s^0 \to K^- \mu^+ \nu_\mu`$ and
$`B_c^+ \to J/\psi \mu^+ \nu_\mu`$ enter the spectrum when a neutrino (or
another particle) is not reconstructed, populating the region below
$`\sim 5.2`$ GeV/$`c^2`$ with a falling shoulder. It is modelled by the right
half of a wide Gaussian whose mean is *fixed* at the lower fit boundary:
inside the range only the convex falling tail is visible. Fixing the mean is
required for identifiability — with both mean and width floating, a very
wide Gaussian becomes degenerate with the smooth combinatorial shape.

**Combinatorial background.** Random combinations of two real muons
(dominantly $`b\bar{b} \to \mu^+\mu^- X`$) produce a smoothly falling spectrum
across the whole range, modelled by an exponential.

The $`B_s^0`$ significance is estimated from the likelihood ratio between the
nominal fit and a fit with the signal yield fixed to zero,
$`\sqrt{2\,\Delta \ln \mathcal{L}}`$ (statistical only).

## 5. Outputs

- `results/selected_data.root` — selected candidates (per-candidate mass,
  kinematics, vertex quality, PID and the `year` tag);
- `figures/mass_fit.png` — mass spectrum with the fit overlaid and the
  per-bin pulls.

## 6. References

The analysis strategy used here is inspired by the following published LHCb
measurements of $`B_s^0 \to \mu^+\mu^-`$:

1. LHCb collaboration, "First Evidence for the Decay $`B_s^0 \to \mu^+\mu^-`$",
   Phys. Rev. Lett. 110 (2013) 021801,
   [arXiv:1211.2674](https://arxiv.org/abs/1211.2674),
   [INSPIRE](https://inspirehep.net/literature/1202279).
2. LHCb collaboration, "Analysis of Neutral $`B`$-Meson Decays into Two Muons",
   Phys. Rev. Lett. 128 (2022) 041801,
   [arXiv:2108.09284](https://arxiv.org/abs/2108.09284),
   [INSPIRE](https://inspirehep.net/literature/1908214).
