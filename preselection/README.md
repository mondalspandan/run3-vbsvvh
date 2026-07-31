# Preselection Framework

C++ framework for VBS VVH preselection using RDataFrame. The paths provided in this README assume you are running on the UAF cluster.

## Directory Structure

```
preselection/
├── src/           # C++ source files
├── include/       # Header files
├── etc/           # Config generation scripts and JSON files
├── condor/        # HTCondor batch submission scripts
├── corrections/   # Scale factors and corrections
├── bin/           # Compiled binaries (generated)
└── build/         # Object files (generated)
```

## Quick Start

```bash
# Set up environment
source setup.sh

# Compile
cd preselection/
make -j8

# Run examples in `run_wrapper.sh`, e.g., for running over locally over one signal sample on UAF:
python run_rdf.py -i etc/input_sample_jsons/run2/sig_c2v1p0_c3_1p0/all_events/2017_VBSWZH_c2v1p0_c3_1p0.json --prefix /ceph/cms/ -o some_dir -n test_small -c 1lep_1FJ -m local -r 2
```

## Prerequisites

Included in CMSSW 15_0_4:
- ROOT with RDataFrame
- Python 3.x
- Uproot
- Boost (for GoldenJSON)
- Correctionlib

Environment setup script: `setup.sh`

## Compilation
To set up and compile the preselection framework, navigate to the top level directory and run:

```bash
source setup.sh
cd preselection/
make -j8
```
This will compile the source files and place the binary in the bin/ directory.

## Configuration Files
The inputs for the preselection framework are defined using configuration JSON files. The config files define input samples, cross-sections, and metadata in JSON format for RDataFrame's `FromSpec`. The json files for all of the skim sets are provided in the `preselection/etc/input_sample_jsons` directory.  

**See [`etc/README.md`](etc/README.md) for detailed documentation.**

## Notes on running 
To run the preselection, use the compiled binary and provide the input specification and output file. The `run_rdf.py` serves as a wrapper around the `bin/runAnalysis`. This script will:
* **Prepare the json files**: The scrip will prepend a given prefix to the paths in all of the json files (to accommodate running either with direct file paths on UAF, or with xrd). 
* **Merge the given json files**: The underlying analysis code expects to receive a single json, so this script will merge all jsons into one single json. Note that `bin/runAnalysis` expects all samples to be the same kind (either signal, background, or data), so if running locally do not mix multiple kinds of jsons into a single run. The final json is saved locally to the `merged_jsons` dir for reference. 
* **Run the analysis**: It will either directly run the `bin/runAnalysis` (if the mode is local) or will wrap around the condor submission (if the mode is condor).

There are examples in `run_wrapper.sh` for running `run_rdf.py` either locally over single jsons for tests, or for running the full analysis at scale over all skim selections. 

## B-tag efficiency production

Use the MC-only `--btag-eff` mode to run the normal channel preselection and
write signed nominal-MC-weighted selected-AK4 jet yields (B/C/light denominator,
inclusive L/M/T/XT/XXT states, and exclusive N/LnotM/MnotT/TnotXT/XTnotXXT/XXT
categories).  The all-channel/all-sample batch
command is shown, commented out, in `run_wrapper.sh`:

```bash
# python3 run_rdf.py -p "$PREFIX" -o "$OUT_DIR" -n run3_btag_eff \
#   -c all -m "$MODE" -r 3 -f 1 --btag-eff --year 2024Prompt
```

The shared configuration is
the era-specific canonical map (`btag_eff_families_run2.yaml` for 2016–2018,
or `btag_eff_families_run3.yaml` for 2024Prompt). Its ordered
`preliminary_families` rules define the semantic first-pass grouping used by
conversion and compatibility plots. Its `final_merges` block defines the only
runtime sample/channel keys: update it only after inspecting the plots.

Preliminary conversion writes `btag_eff_<year>_*_prelim.json`; it is diagnostic-only.
Normal MC processing loads the year-scoped final `btag_eff_<year>.json`, whose correction names
and sample/channel keys must exactly match the YAML final groups. There is no
exact-sample or preliminary-family fallback at runtime. The `_met` trigger
subset channels (`0lep_1FJ_met`, `0lep_2FJ_met`) and `all_events` are excluded
from final construction and global diagnostics.
The stored `*_mcstat_unc` efficiency uncertainties are informational diagnostics
only; they are not consumed by the main analysis. (B-tagging SF variation
branches are separate and remain part of the analysis weighting.)

Normal MC b-tag SF application is controlled per analysis channel by
`applybtag.yaml`. A channel set to `True` receives the nominal b-tag factor and
its variation branches; a channel set to `False` receives neither. The
`--skip-btag-sf` option overrides a `True` entry for one invocation. Disabled
channels retain the ordinary uncoupled pileup, PS, muF, and muR variations.

HF calibration SFs are written as `{central,up,down}` vectors.  The canonical
year-decorrelated branches are `weight_btagging_sf_HF_uncorrelated_<year>` and
`weight_btagging_sf_HF_statistic_<year>`; the other source branches use
`weight_btagging_sf_HF_<source>`.  Run 2 provides `statistic`, `pileup`,
`isrdef`, `fsrdef`, `muf`, `mur`, `pdf`, `as`, and `ttbar`; 2024 provides
`statistic`, `pileup`, `isrdef`, `fsrdef`, `muf`, `mur`, `pdfas`, `type3`,
`bfragmentation`, `topmass`, and `hdamp`.  JES and JER are coupled to the
corresponding kinematic variations through `weightsyst_jes` and
`weightsyst_jer`; they are not published as independent b-tag branches.
Unavailable source
vectors are central/central/central.  `weight_pileup`, `weight_PSISR`,
`weight_PSFSR`, `weight_muF`, and `weight_muR` already include their matching
HF source.  There are no public `*_raw` columns or separate public HF
pileup/isrdef/fsrdef/muf/mur branches.  The broad HF correlated branch is
retained only for compatibility/closure and must not be combined with the
fine-source decomposition in a statistical model; uncorrelated and statistic
are intentionally both retained.

<details>
<summary>Full b-tag efficiency derivation tutorial</summary>

```bash
# 1. Produce raw weighted yields on MC with Slurm.  This directly creates
#    $OUT_DIR/2024Prompt/<channel>/{manifest.json,<exact-sample>/output_<job-index>.root}.
#    Use a new/empty $OUT_DIR for each submission; mixed reruns are rejected.
python3 run_rdf.py -p "$PREFIX" -o "$OUT_DIR" -n run3_btag_eff \
  -c all -m slurm -r 3 -f 1 --btag-eff --year 2024Prompt

# The later commands consume the year root directly.  Every configured
# sample, including a no-file skip, is recorded in each manifest; final steps
# reject incomplete manifests and validate every expected job exactly once.
INPUT_ROOT="$OUT_DIR/2024Prompt"

# 2. Produce preliminary payloads, once per retained channel.  The ROOT dump
#    directory and metadata year are explicit; the output name is automatic:
#    corrections/scalefactors/btagging/btag_eff_2024Prompt_1lep_1FJ_prelim.json
python3 ../misc/sf-utils/bEff-convert-to-correction.py \
  --input-dir "$INPUT_ROOT/1lep_1FJ" --job-manifest "$INPUT_ROOT/1lep_1FJ/manifest.json" \
  --year 2024Prompt --channel 1lep_1FJ

# 3. Inspect preliminary compatibility.  The first command compares families
#    within one source channel; the next two compare retained source channels
#    before final YAML channel merges.  all_events and the _met subsets are excluded.
python3 ../misc/sf-utils/plot-btag-eff-families.py \
  --input-dir "$INPUT_ROOT/1lep_1FJ" --job-manifest "$INPUT_ROOT/1lep_1FJ/manifest.json" \
  --year 2024Prompt --channel 1lep_1FJ
# Manually update final_merges in the selected era YAML after this review.
# defaults to diagnostics/diagnostic_2024Prompt_prelim_all_channels_families
python3 ../misc/sf-utils/plot-btag-eff-global.py --skip-matrices \
  --mode families --input-root "$INPUT_ROOT" --year 2024Prompt
# defaults to diagnostics/diagnostic_2024Prompt_prelim_all_samples_channels
python3 ../misc/sf-utils/plot-btag-eff-global.py --skip-matrices \
  --mode channels --input-root "$INPUT_ROOT" --year 2024Prompt

# 4. Build the final payload.  All retained YAML channels are discovered
# automatically; missing channels, manifests, jobs, duplicate outputs, or
# unexpected samples are fatal.  The excluded _met subset channels are ignored.
python3 ../misc/sf-utils/bEff-convert-to-correction.py --final --year 2024Prompt \
  --input-root "$INPUT_ROOT"

# 5. Recheck the two money plots after applying final sample/channel merges.
# defaults to diagnostics/diagnostic_2024Prompt_final_all_channels_families
python3 ../misc/sf-utils/plot-btag-eff-global.py --final --skip-matrices \
  --mode families --input-root "$INPUT_ROOT" --year 2024Prompt
python3 ../misc/sf-utils/plot-btag-eff-global.py --final --skip-matrices \
  --mode channels --input-root "$INPUT_ROOT" --year 2024Prompt

# Optional: compare the all-channel/all-sample weighted efficiencies between
# every complete era layout discovered under the common output directory.
python3 ../misc/sf-utils/plot-btag-eff-years.py \
  --input-base /path/to/preselection/slurm/outputs

# The final conversion writes btag_eff_2024Prompt.json.  The analysis selects
# this file from each sample's metadata year; keep the year suffix.
```

The event reweighting uses the ordered adjacent-WP formula: XXT jets use
SF_XXT; a jet passing WP i but failing the next tighter WP uses
`(SF_i*eps_i - SF_(i+1)*eps_(i+1))/(eps_i-eps_(i+1))`; jets failing L use
`(1-SF_L*eps_L)/(1-eps_L)`.  Systematic sources evaluate all five WPs
coherently, with the existing public nuisance-branch count and central/up/down
ordering unchanged. Compatibility uses the six mutually exclusive categories
N/LnotM/MnotT/TnotXT/XTnotXXT/XXT and weighted-binomial MC-statistical
uncertainties; it is a diagnostic, not a formal hypothesis test. New raw
schema-v2 outputs must be produced before final payloads can contain M, XT, and
XXT; old L/T-only ROOT files are rejected by the converter.
During conversion, a pathological signed-weight pT bin is merged with its
immediately lower neighbor and the merged efficiency is assigned to both bins;
an irreparable first-bin pathology still uses the validated all-MC fallback.
The converter sums the four producer eta bins into one central-jet payload bin;
its edges are `[-2.4, 2.4]` for 2016 pre/post-VFP and `[-2.5, 2.5]` otherwise.
pT binning is unchanged.
The 2016 pre/post-VFP UParTAK4 fixed-WP payloads use |eta| < 2.4; 2017,
2018, and 2024Prompt use |eta| < 2.5.  Efficiency production and SF
application use the same year-dependent boundary.

</details>

---
## Details on the condor batch submission

For large-scale processing, the HTCondor submission should be used. Some overview information is provided here, with more details in the condor README. 

```bash
# Submit jobs
python condor/submit.py -c <config.json> -a <channel> -r <run_number>

# Check status
python condor/status.py --task <task_name>

# Resubmit failed jobs
python condor/resubmit.py --task <task_name> --failed
```

For automatic monitoring and resubmission:
```bash
screen -S condor_monitor
python condor/submit.py -c <config.json> -a <channel> -r <run_number> --monitor --timeout 12
# Ctrl+A, D to detach
```

**See [`condor/README.md`](condor/README.md) for detailed documentation.**
