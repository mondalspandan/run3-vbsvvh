#!/usr/bin/env python3
"""Convert merged weighted b-tag efficiency histograms into correctionlib JSON.

Exact-sample mode is preliminary/diagnostic-only. Family mode discovers sample
directories, merges raw weighted yields into physics families, and writes one
correction entry per family.
"""

import argparse
import json
import re
from pathlib import Path

import numpy as np
import uproot
import correctionlib.schemav2 as cs

from btag_eff_families import (excluded_source_channels, final_channel,
                               final_group, load_config,
                               retained_source_channels, sample_family)


FLAVORS = ("b", "c", "light")
INCLUSIVE_WPS = ("L", "M", "T", "XT", "XXT")
EXCLUSIVE_CATEGORIES = ("N", "LnotM", "MnotT", "TnotXT", "XTnotXXT", "XXT")
HISTOGRAM_STATES = ("den", *INCLUSIVE_WPS, "LnotM", "MnotT", "TnotXT", "XTnotXXT", "N")


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    inputs = parser.add_mutually_exclusive_group(required=True)
    inputs.add_argument("--input", nargs="+",
                        help="All raw ROOT files for one sample (local paths or root:// URLs)")
    inputs.add_argument("--input-dir", type=Path,
                        help="Directory containing one raw-output directory per exact sample")
    inputs.add_argument("--input-root", type=Path,
                        help="Final mode: root containing CHANNEL/manifest.json and CHANNEL/SAMPLE/output_N.root")
    parser.add_argument("--year", required=True, help="Metadata year, e.g. 2024Prompt")
    parser.add_argument("--channel", help="Preliminary conversion channel, e.g. 0lep_0FJ")
    parser.add_argument("--sample", help="Exact RDataFrame sample name from the input JSON (exact-sample mode)")
    parser.add_argument("--output", type=Path,
                        help="Optional output path (defaults to btag_eff_<year>.json)")
    parser.add_argument("--manifest", type=Path,
                        help="Family membership manifest (defaults beside --output in family mode)")
    parser.add_argument("--job-manifest", type=Path,
                        help="Optional Slurm manifest.json: require exactly its expected sample/job outputs")
    parser.add_argument("--final", action="store_true",
                        help="Build final grouped efficiencies from every retained YAML channel under --input-root")
    return parser.parse_args()


def default_output_path(year, preliminary=False, channel=None):
    directory = (Path(__file__).parents[2] / "preselection" / "corrections" /
                 "scalefactors" / "btagging")
    token = year
    if preliminary and channel:
        return directory / f"btag_eff_{token}_{channel}_prelim.json"
    return directory / f"btag_eff_{token}{'_prelim' if preliminary else ''}.json"


def fold_pt_flow(values, path, hist_name):
    """Fold pT flow into edge bins, matching correctionlib's pT clamp flow."""
    # The producer rejects |eta| >= 2.5, so eta flow would indicate a
    # producer/application mismatch rather than information to clamp.
    if np.any(values[:, 0] != 0) or np.any(values[:, -1] != 0):
        raise ValueError(f"{path}:{hist_name} has unexpected eta under/overflow entries")
    central = values[1:-1, 1:-1].astype(float, copy=True)
    central[0, :] += values[0, 1:-1]
    central[-1, :] += values[-1, 1:-1]
    return central


def btag_max_abs_eta(year):
    """Eta acceptance used by both production and the correction payload."""
    if year in ("2016preVFP", "2016postVFP"):
        return 2.4
    if year in ("2017", "2018", "2024Prompt"):
        return 2.5
    raise ValueError(f"Unsupported b-tag efficiency year: {year}")


def histogram_arrays_in_application_range(hist, path, hist_name, year):
    """Return weighted yields and their Sumw2 variances in application bins."""
    values, pt_edges, eta_edges = hist.to_numpy(flow=True)
    variances = hist.variances(flow=True)
    if variances is None:
        raise ValueError(f"{path}:{hist_name} has no Sumw2 information")
    values = fold_pt_flow(values, path, hist_name)
    variances = fold_pt_flow(variances, path, hist_name)
    # The payload and compatibility diagnostics use one inclusive central-jet
    # eta bin; retain the pT dependence but sum the mutually exclusive eta bins.
    values = np.sum(values, axis=1, keepdims=True)
    variances = np.sum(variances, axis=1, keepdims=True)
    # Eta is merged into one bin.  Its correction-domain boundary must still
    # match the year-dependent jet acceptance used during production.
    eta_max = btag_max_abs_eta(year)
    return values, variances, pt_edges[1:-1], np.asarray([-eta_max, eta_max])


def read_merged_histograms(paths, expected_year, expected_channel, expected_sample):
    """Return weighted yields, Sumw2 variances, and common pT/eta edges."""
    merged = {}
    merged_variances = {}
    edges = None
    for path in paths:
        with uproot.open(path) as root_file:
            if "btag_eff_format" not in root_file:
                raise ValueError(f"{path} has no b-tag efficiency format metadata")
            output_format = root_file["btag_eff_format"].member("fTitle")
            if not output_format.startswith("signed baseweight"):
                raise ValueError(
                    f"{path} contains obsolete unweighted b-tag histograms; regenerate it with the current --btag_eff workflow"
                )
            expected_metadata = {
                "btag_eff_year": expected_year,
                "btag_eff_channel": expected_channel,
                "btag_eff_sample": expected_sample,
            }
            for key, expected_value in expected_metadata.items():
                if key not in root_file:
                    raise ValueError(f"{path} has no {key} metadata")
                actual_value = root_file[key].member("fTitle")
                if actual_value != expected_value:
                    raise ValueError(f"{path} has {key}={actual_value!r}, expected {expected_value!r}")
            if "btag_eff_schema_version" not in root_file or root_file["btag_eff_schema_version"].member("fTitle") != "2":
                raise ValueError(f"{path} is not a schema-v2 five-working-point b-tag efficiency file")
            if "btag_eff_working_points" not in root_file or root_file["btag_eff_working_points"].member("fTitle") != ",".join(INCLUSIVE_WPS):
                raise ValueError(f"{path} does not declare the canonical working points {','.join(INCLUSIVE_WPS)}")
            for flavor in FLAVORS:
                for state in HISTOGRAM_STATES:
                    hist_name = f"btag_{flavor}_{state}"
                    if hist_name not in root_file:
                        raise ValueError(f"{path} does not contain {hist_name}")
                    values, variances, pt_edges, eta_edges = histogram_arrays_in_application_range(
                        root_file[hist_name], path, hist_name, expected_year)
                    if edges is None:
                        edges = (pt_edges, eta_edges)
                    elif not (np.array_equal(pt_edges, edges[0]) and np.array_equal(eta_edges, edges[1])):
                        raise ValueError(f"Histogram binning in {path} differs from the other inputs")
                    key = (flavor, state)
                    merged[key] = merged.get(key, np.zeros_like(values, dtype=float)) + values
                    merged_variances[key] = merged_variances.get(key, np.zeros_like(variances, dtype=float)) + variances
    return merged, merged_variances, edges


def add_counts(destination, source):
    for key, values in source.items():
        destination[key] = destination.get(key, np.zeros_like(values, dtype=float)) + values


def output_job_index(path):
    match = re.fullmatch(r"output_(\d+)\.root", path.name)
    if not match:
        raise ValueError(f"Unexpected b-tag output filename {path}; expected output_<job index>.root")
    return int(match.group(1))


def validate_job_manifest(input_dir, manifest_path):
    """Validate that every Slurm task in *manifest_path* produced one ROOT file."""
    manifest = json.loads(manifest_path.read_text())
    samples = manifest.get("samples")
    if not isinstance(samples, dict) or not samples:
        raise ValueError(f"{manifest_path} has no configured-sample completeness metadata")
    jobs = manifest.get("jobs")
    if not isinstance(jobs, dict):
        raise ValueError(f"{manifest_path} has no jobs")
    expected = {}
    for sample, metadata in samples.items():
        if not isinstance(sample, str) or not isinstance(metadata, dict):
            raise ValueError(f"{manifest_path} has invalid configured-sample metadata")
        indices = metadata.get("job_indices")
        if (metadata.get("status") == "skipped_no_files" or not isinstance(indices, list) or
                not indices):
            raise ValueError(
                f"{manifest_path} is incomplete: configured sample {sample!r} has "
                f"status={metadata.get('status')!r}, jobs={indices!r}, reason={metadata.get('reason')!r}")
        if any(not isinstance(index, int) for index in indices) or len(indices) != len(set(indices)):
            raise ValueError(f"{manifest_path} has invalid expected job indices for {sample}")
        expected[sample] = set(indices)
    seen = {}
    for job in jobs.values():
        sample, index = job.get("sample"), job.get("job_idx")
        if not isinstance(sample, str) or not isinstance(index, int):
            raise ValueError(f"{manifest_path} has a job without sample/job_idx metadata")
        if sample not in expected:
            raise ValueError(f"{manifest_path} has a job for unconfigured sample {sample!r}")
        if index not in expected[sample]:
            raise ValueError(f"{manifest_path} has unexpected job index {sample}:{index}")
        # Build independently from the declared sample index list, so each
        # Slurm task is still required exactly once.
        if index in seen.setdefault(sample, set()):
            raise ValueError(f"{manifest_path} has duplicate expected job index {sample}:{index}")
        seen[sample].add(index)
    if set(seen) != set(expected):
        raise ValueError(f"{manifest_path} jobs do not cover every configured sample")
    for sample, indices in expected.items():
        if seen[sample] != indices:
            raise ValueError(f"{manifest_path} jobs do not match declared indices for {sample}")

    discovered = {}
    directories = {path.name for path in input_dir.iterdir() if path.is_dir()}
    unexpected_dirs = directories - set(expected)
    if unexpected_dirs:
        raise ValueError(f"Unexpected sample directories not in {manifest_path}: {sorted(unexpected_dirs)}")
    for sample, indices in expected.items():
        sample_dir = input_dir / sample
        roots = sorted(sample_dir.glob("*.root")) if sample_dir.is_dir() else []
        found = [output_job_index(path) for path in roots]
        if len(found) != len(set(found)):
            raise ValueError(f"Duplicate ROOT outputs for {sample}: {found}")
        found_set = set(found)
        if found_set != indices:
            raise ValueError(f"Incomplete outputs for {sample}: expected {sorted(indices)}, found {sorted(found_set)}")
        discovered[sample] = {"expected_jobs": len(indices), "discovered_jobs": len(found_set)}
    return discovered


def discover_family_histograms(input_dir, year, channel, job_manifest=None, config=None):
    """Read every exact sample directory and return raw yields grouped by family."""
    if not input_dir.is_dir():
        raise ValueError(f"--input-dir is not a directory: {input_dir}")
    completeness = (validate_job_manifest(input_dir, job_manifest) if job_manifest else None)
    if completeness is None:
        print("WARNING: b-tag input completeness was not verified (no --job-manifest supplied)")
    grouped_counts, grouped_variances, grouped_edges, members = {}, {}, {}, {}
    for sample_dir in sorted(path for path in input_dir.iterdir() if path.is_dir()):
        roots = sorted(sample_dir.glob("*.root"))
        if not roots:
            # Allow diagnostics/manifests to live beside the sample directories.
            continue
        sample = sample_dir.name
        family = sample_family(sample, config)
        counts, variances, edges = read_merged_histograms(roots, year, channel, sample)
        if family in grouped_edges and not (
            np.array_equal(edges[0], grouped_edges[family][0]) and
            np.array_equal(edges[1], grouped_edges[family][1])
        ):
            raise ValueError(f"Histogram binning for {sample} differs within family {family}")
        grouped_edges[family] = edges
        grouped_counts.setdefault(family, {})
        grouped_variances.setdefault(family, {})
        add_counts(grouped_counts[family], counts)
        add_counts(grouped_variances[family], variances)
        members.setdefault(family, []).append(sample)
    if not members:
        raise ValueError(f"No sample directories found in {input_dir}")
    return grouped_counts, grouped_variances, grouped_edges, members, completeness


def invalid_count_bins(counts, variances=None):
    """Return per-flavor masks for bins that cannot form physical efficiencies."""
    masks = {}
    for flavor in FLAVORS:
        denominator = counts[(flavor, "den")]
        inclusive = {wp: counts[(flavor, wp)] for wp in INCLUSIVE_WPS}
        exclusive = {category: counts[(flavor, category)] for category in EXCLUSIVE_CATEGORIES}
        identity_scale = np.maximum.reduce([
            np.ones_like(denominator), np.abs(denominator),
            *(np.abs(values) for values in inclusive.values()),
            *(np.abs(values) for values in exclusive.values()),
        ])
        identity_tolerance = 1e-10 * identity_scale
        identity_invalid = (
            (np.abs(inclusive["L"] - (exclusive["LnotM"] + inclusive["M"])) > identity_tolerance) |
            (np.abs(inclusive["M"] - (exclusive["MnotT"] + inclusive["T"])) > identity_tolerance) |
            (np.abs(inclusive["T"] - (exclusive["TnotXT"] + inclusive["XT"])) > identity_tolerance) |
            (np.abs(inclusive["XT"] - (exclusive["XTnotXXT"] + inclusive["XXT"])) > identity_tolerance) |
            (np.abs(denominator - sum(exclusive.values())) > identity_tolerance)
        )
        tolerance = 1e-10 * identity_scale
        nonempty = np.abs(denominator) > tolerance
        ordered_invalid = (
            (inclusive["XXT"] < -tolerance) |
            (inclusive["XT"] < inclusive["XXT"] - tolerance) |
            (inclusive["T"] < inclusive["XT"] - tolerance) |
            (inclusive["M"] < inclusive["T"] - tolerance) |
            (inclusive["L"] < inclusive["M"] - tolerance) |
            (inclusive["L"] > denominator + tolerance)
        )
        exclusive_invalid = np.logical_or.reduce(
            [values < -tolerance for values in exclusive.values()]
        )
        cancellation_invalid = np.zeros_like(denominator, dtype=bool)
        if variances is not None:
            cancellation_scale = np.maximum(1., identity_scale) ** 2
            for category in EXCLUSIVE_CATEGORIES:
                cancellation_invalid |= (
                    (np.abs(exclusive[category]) <= tolerance) &
                    (variances[(flavor, category)] > 1.e-20 * cancellation_scale)
                )
        invalid = identity_invalid | (
            (nonempty & ((denominator <= 0) | ordered_invalid | exclusive_invalid)) |
            (~nonempty & np.logical_or.reduce([np.abs(values) > tolerance
                                                for values in exclusive.values()])) |
            cancellation_invalid
        )
        masks[flavor] = invalid
    return masks


def validate_counts(counts, variances=None):
    """Validate signed weighted yields before constructing an efficiency map."""
    for flavor, invalid in invalid_count_bins(counts, variances).items():
        if np.any(invalid):
            bad_bins = np.argwhere(invalid).tolist()
            raise ValueError(
                f"Signed-weight b-tag yields are unphysical for flavor {flavor} in bins {bad_bins}; "
                "merge those bins or provide more MC before conversion"
            )


def repair_with_inclusive(counts, variances, inclusive_counts, inclusive_variances):
    """Replace only pathological family bins with the validated all-MC bin."""
    repaired = {key: values.copy() for key, values in counts.items()}
    repaired_variances = {key: values.copy() for key, values in variances.items()}
    replacements = {}
    for flavor, invalid in invalid_count_bins(counts, variances).items():
        if not np.any(invalid):
            continue
        for state in HISTOGRAM_STATES:
            repaired[flavor, state][invalid] = inclusive_counts[flavor, state][invalid]
            repaired_variances[flavor, state][invalid] = inclusive_variances[flavor, state][invalid]
        replacements[flavor] = np.argwhere(invalid).tolist()
    validate_counts(repaired, repaired_variances)
    return repaired, repaired_variances, replacements


def merge_invalid_bins_downward(counts, variances):
    """Merge pathological pT bins into the immediately lower bin.

    The merged yield is copied back into the original upper bin so both bins
    receive the same efficiency.  This preserves the published pT schema while
    avoiding signed-weight pathologies in sparse high-pT bins.
    """
    merged = {key: values.copy() for key, values in counts.items()}
    merged_variances = {key: values.copy() for key, values in variances.items()}
    merged_bins = {}
    invalid = invalid_count_bins(merged, merged_variances)
    for flavor in FLAVORS:
        indices = [int(index[0]) for index in np.argwhere(invalid[flavor]) if int(index[0]) > 0]
        if not indices:
            continue
        merged_bins[flavor] = []
        groups = []
        for index in indices:
            if not groups or index != groups[-1][-1] + 1:
                groups.append([index])
            else:
                groups[-1].append(index)
        for group in groups:
            lower = group[0] - 1
            for index in group:
                for state in HISTOGRAM_STATES:
                    merged[flavor, state][lower, :] += merged[flavor, state][index, :]
                    merged_variances[flavor, state][lower, :] += merged_variances[flavor, state][index, :]
            for index in group:
                for state in HISTOGRAM_STATES:
                    merged[flavor, state][index, :] = merged[flavor, state][lower, :]
                    merged_variances[flavor, state][index, :] = merged_variances[flavor, state][lower, :]
            merged_bins[flavor].extend([ [index, lower] for index in group ])
    return merged, merged_variances, merged_bins


def efficiency(values, denominator):
    output = np.zeros_like(values, dtype=float)
    np.divide(values, denominator, out=output, where=denominator > 0)
    return output


def mcstat_efficiency_uncertainty(numerator, denominator, numerator_variance, denominator_variance):
    """Weighted-binomial/delta-method uncertainty for a category fraction X/D."""
    output = np.full_like(denominator, np.nan, dtype=float)
    valid = denominator > 0
    empty = ((denominator == 0) & (numerator == 0) &
             (numerator_variance == 0) & (denominator_variance == 0))
    output[empty] = 0.
    epsilon = np.divide(numerator, denominator, out=np.zeros_like(denominator, dtype=float), where=valid)
    raw_variance = np.divide((1. - 2. * epsilon) * numerator_variance + epsilon ** 2 * denominator_variance,
                             denominator ** 2, out=np.full_like(denominator, np.nan, dtype=float), where=valid)
    scale = np.divide(np.abs((1. - 2. * epsilon) * numerator_variance) +
                      np.abs(epsilon ** 2 * denominator_variance), denominator ** 2,
                      out=np.zeros_like(denominator, dtype=float), where=valid)
    tiny_negative = (raw_variance < 0.) & (raw_variance >= -1.e-12 * np.maximum(1., scale))
    raw_variance[tiny_negative] = 0.
    valid &= np.isfinite(raw_variance) & (raw_variance >= 0.)
    output[valid] = np.sqrt(raw_variance[valid])
    return output


def compute_mcstat_uncertainties(counts, variances):
    output = {(flavor, wp): mcstat_efficiency_uncertainty(
        counts[(flavor, wp)], counts[(flavor, "den")], variances[(flavor, wp)], variances[(flavor, "den")])
              for flavor in FLAVORS for wp in INCLUSIVE_WPS}
    for (flavor, wp), values in output.items():
        if not np.all(np.isfinite(values)):
            raise ValueError(f"Invalid weighted-binomial MC-statistical variance for {flavor}/{wp}")
    return output


def multibinning(values, pt_edges, eta_edges):
    return {
        "nodetype": "multibinning",
        "inputs": ["pt", "eta"],
        "edges": [pt_edges.tolist(), eta_edges.tolist()],
        "content": values.reshape(-1).tolist(),
        "flow": "clamp",
    }


def sample_category(sample, values, edges):
    pt_edges, eta_edges = edges
    flavor_entries = []
    for flavor in FLAVORS:
        wp_entries = []
        for wp in INCLUSIVE_WPS:
            wp_entries.append({
                "key": wp,
                "value": multibinning(values[(flavor, wp)], pt_edges, eta_edges),
            })
        flavor_entries.append({
            "key": {"b": "B", "c": "C", "light": "L"}[flavor],
            "value": {"nodetype": "category", "input": "WP", "content": wp_entries},
        })
    return {
        "key": sample,
        "value": {"nodetype": "category", "input": "flavor", "content": flavor_entries},
    }


def make_correction(name, sample_entry, description, output_name, output_description):
    return {
        "name": name,
        "description": description,
        "version": 1,
        "inputs": [
            {"name": "sample", "type": "string", "description": "sample category key (final YAML family in production payload)"},
            {"name": "flavor", "type": "string", "description": "B/C/L"},
            {"name": "WP", "type": "string", "description": "L/M/T/XT/XXT"},
            {"name": "pt", "type": "real", "description": "selected AK4 jet pT"},
            {"name": "eta", "type": "real", "description": "selected AK4 jet eta"},
        ],
        "output": {"name": output_name, "type": "real", "description": output_description},
        "data": {"nodetype": "category", "input": "sample", "content": [sample_entry]},
    }


def update_output(path, correction_specs, replace_entries=False, replace_correction_prefix=None):
    if path.exists():
        payload = json.loads(path.read_text())
    else:
        payload = {"schema_version": 2, "description": "VBS VVH b-tag efficiencies", "corrections": [], "compound_corrections": []}

    expected_inputs = ["sample", "flavor", "WP", "pt", "eta"]
    if replace_correction_prefix is not None:
        expected_names = {spec[0] for spec in correction_specs}
        payload["corrections"] = [
            item for item in payload["corrections"]
            if not (item["name"].startswith(replace_correction_prefix) and item["name"] not in expected_names)
        ]
    replaced = set()
    for correction_name, sample_entry, description, output_name, output_description in correction_specs:
        correction = next((item for item in payload["corrections"] if item["name"] == correction_name), None)
        if correction is None:
            payload["corrections"].append(
                make_correction(correction_name, sample_entry, description, output_name, output_description))
            correction = payload["corrections"][-1]
        if ([item["name"] for item in correction["inputs"]] != expected_inputs or
                correction["output"]["name"] != output_name):
            raise ValueError(f"Existing {correction_name} has an incompatible schema; write a new output file")
        correction["description"] = description
        correction["output"]["description"] = output_description
        entries = correction["data"]["content"]
        if replace_entries and correction_name not in replaced:
            correction["data"]["content"] = []
            replaced.add(correction_name)
        if replace_entries:
            correction["data"]["content"].append(sample_entry)
        else:
            correction["data"]["content"] = [entry for entry in entries if entry["key"] != sample_entry["key"]]
            correction["data"]["content"].append(sample_entry)

    # Validate with correctionlib before touching the output file.
    cs.CorrectionSet.model_validate(payload)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n")


def grouped_specs(prefix, grouped_counts, grouped_variances, grouped_edges, members):
    inclusive_counts, inclusive_variances = {}, {}
    for group in members:
        add_counts(inclusive_counts, grouped_counts[group])
        add_counts(inclusive_variances, grouped_variances[group])
    inclusive_counts, inclusive_variances, inclusive_merged_bins = merge_invalid_bins_downward(
        inclusive_counts, inclusive_variances)
    if inclusive_merged_bins:
        print(f"inclusive: merged pathological pT bins into their lower neighbors: {inclusive_merged_bins}")
    validate_counts(inclusive_counts, inclusive_variances)
    specs, fallbacks = [], {}
    for group in sorted(members):
        counts, variances, merged_bins = merge_invalid_bins_downward(
            grouped_counts[group], grouped_variances[group])
        if merged_bins:
            print(f"{group}: merged pathological pT bins into their lower neighbors: {merged_bins}")
        counts, variances, fallback_bins = repair_with_inclusive(
            counts, variances, inclusive_counts, inclusive_variances)
        if fallback_bins:
            fallbacks[group] = fallback_bins
            print(f"{group}: replaced {sum(len(bins) for bins in fallback_bins.values())} pathological bins with all-MC yields")
        efficiency_values = {(flavor, wp): efficiency(counts[(flavor, wp)], counts[(flavor, "den")])
                             for flavor in FLAVORS for wp in INCLUSIVE_WPS}
        mcstat_uncertainties = compute_mcstat_uncertainties(counts, variances)
        specs.extend([
            (prefix, sample_category(group, efficiency_values, grouped_edges[group]),
             "Selected-AK4 UParTAK4 b-tag efficiency", "efficiency", "MC tagging efficiency"),
            (f"{prefix}_mcstat_unc", sample_category(group, mcstat_uncertainties, grouped_edges[group]),
             "Weighted-binomial MC-statistical uncertainty of selected-AK4 UParTAK4 b-tag efficiency", "uncertainty",
             "Weighted-binomial MC tagging-efficiency uncertainty"),
        ])
    return specs, fallbacks


def discover_final_inputs(input_root, year, config=None):
    """Return every required final source channel and its colocated manifest."""
    config = load_config(year) if config is None else config
    if not input_root.is_dir():
        raise ValueError(f"--input-root is not a directory: {input_root}")
    retained = retained_source_channels(config)
    excluded = excluded_source_channels(config)
    children = {path.name for path in input_root.iterdir() if path.is_dir()}
    missing = set(retained) - children
    unexpected = children - set(retained) - set(excluded)
    if missing or unexpected:
        raise ValueError(f"Final input root channel mismatch: missing={sorted(missing)}, unexpected={sorted(unexpected)}")
    ignored = sorted(set(excluded) & children)
    if ignored:
        print(f"Ignoring excluded b-tag source channels: {ignored}")
    inputs = {}
    manifests = {}
    for channel in retained:
        directory = input_root / channel
        manifest = directory / "manifest.json"
        if not manifest.is_file():
            raise ValueError(f"Final input channel {channel} is missing required manifest {manifest}")
        inputs[channel] = directory
        manifests[channel] = manifest
    return inputs, manifests, ignored


def discover_source_histograms(input_root, year, config=None):
    """Load complete retained source channels before final YAML merging."""
    config = load_config(year) if config is None else config
    channel_inputs, channel_manifests, ignored = discover_final_inputs(input_root, year, config)
    source_counts, source_variances, source_edges, members, completeness = {}, {}, {}, {}, {}
    for channel, input_dir in channel_inputs.items():
        counts, variances, edges, preliminary_members, checked = discover_family_histograms(
            input_dir, year, channel, channel_manifests[channel], config)
        completeness[channel] = checked
        for family, samples in preliminary_members.items():
            key = (channel, family)
            source_counts[key] = counts[family]
            source_variances[key] = variances[family]
            source_edges[key] = edges[family]
            members[key] = samples
    return source_counts, source_variances, source_edges, members, completeness, ignored


def discover_final_histograms(input_root, year, config=None):
    """Merge all YAML-retained raw outputs into final channel/sample groups."""
    config = load_config(year) if config is None else config
    source_counts, source_variances, source_edges, source_members, completeness, ignored = discover_source_histograms(
        input_root, year, config)
    grouped_counts, grouped_variances, grouped_edges, members = {}, {}, {}, {}
    for (channel, preliminary_family), counts in source_counts.items():
        target_channel = final_channel(channel, config)
        target_sample = final_group("samples", preliminary_family, config)
        target = (target_channel, target_sample)
        if target in grouped_edges and not (
            np.array_equal(source_edges[channel, preliminary_family][0], grouped_edges[target][0]) and
            np.array_equal(source_edges[channel, preliminary_family][1], grouped_edges[target][1])
        ):
            raise ValueError(f"Histogram binning differs within final group {target}")
        grouped_edges[target] = source_edges[channel, preliminary_family]
        grouped_counts.setdefault(target, {})
        grouped_variances.setdefault(target, {})
        add_counts(grouped_counts[target], counts)
        add_counts(grouped_variances[target], source_variances[channel, preliminary_family])
        members.setdefault(target_channel, {}).setdefault(target_sample, []).extend(
            [f"{channel}:{sample}" for sample in source_members[channel, preliminary_family]])
    return grouped_counts, grouped_variances, grouped_edges, members, completeness, ignored


def main():
    args = parse_args()
    if args.output is None:
        args.output = default_output_path(args.year, preliminary=not args.final, channel=args.channel)
    expected_final_name = f"btag_eff_{args.year}.json"
    if args.final and args.output.name != expected_final_name:
        raise ValueError(f"Final output must be named {expected_final_name}; year-scoped payloads are required")
    if args.final:
        if not args.input_root:
            raise ValueError("--final requires --input-root")
        if args.input or args.input_dir or args.sample or args.channel or args.job_manifest:
            raise ValueError("--final accepts only --input-root, --year, --output, and optional --manifest")
        config = load_config(year=args.year)
        counts, variances, edges, members, completeness, ignored = discover_final_histograms(
            args.input_root, args.year, config)
        specs, fallbacks = [], {}
        for channel, final_members in sorted(members.items()):
            keys = {(channel, sample) for sample in final_members}
            channel_counts = {sample: counts[channel, sample] for _, sample in keys}
            channel_variances = {sample: variances[channel, sample] for _, sample in keys}
            channel_edges = {sample: edges[channel, sample] for _, sample in keys}
            channel_specs, channel_fallbacks = grouped_specs(
                f"btag_{args.year}_{channel}", channel_counts, channel_variances, channel_edges, final_members)
            specs.extend(channel_specs)
            fallbacks[channel] = channel_fallbacks
        update_output(args.output, specs, replace_entries=True,
                      replace_correction_prefix=f"btag_{args.year}_")
        manifest = args.manifest or args.output.with_name(
            f"btag_eff_{args.year}_final_families.json")
        manifest.write_text(json.dumps({
            "mode": "final", "year": args.year, "input_root": str(args.input_root),
            "retained_source_channels": list(retained_source_channels(config)),
            "ignored_source_channels": ignored,
            "final_members": members, "inclusive_fallback_bins": fallbacks,
            "input_completeness_verified": True,
            "job_counts": completeness,
        }, indent=2) + "\n")
        print(f"Wrote final efficiencies for {len(members)} channel groups and manifest {manifest}")
        return

    if not args.channel:
        raise ValueError("--channel is required unless --final is used")
    if "_prelim" not in args.output.stem:
        raise ValueError("Preliminary conversion output must be named *_prelim.json; reserve btag_eff_<year>.json for --final")
    prefix = f"btag_{args.year}_{args.channel}"
    if args.input_dir:
        grouped_counts, grouped_variances, grouped_edges, members, completeness = discover_family_histograms(
            args.input_dir, args.year, args.channel, args.job_manifest, load_config(year=args.year))
        specs, fallbacks = grouped_specs(prefix, grouped_counts, grouped_variances, grouped_edges, members)
        update_output(args.output, specs, replace_entries=True)
        manifest = args.manifest or args.output.with_name(
            f"btag_eff_{args.year}_{args.channel}_families.json")
        manifest.write_text(json.dumps({
            "year": args.year, "channel": args.channel,
            "mode": "preliminary",
            "input_dir": str(args.input_dir), "families": members,
            "inclusive_fallback_bins": fallbacks,
            "input_completeness_verified": completeness is not None,
            "job_counts": completeness or {},
        }, indent=2) + "\n")
        print(f"Wrote {len(members)} family entries and manifest {manifest}")
        return

    if not args.sample:
        raise ValueError("--sample is required with --input")
    # Exact-sample payloads are useful for local diagnostics only.  Runtime
    # lookup intentionally accepts final family keys only.
    counts, variances, edges = read_merged_histograms(args.input, args.year, args.channel, args.sample)
    validate_counts(counts, variances)
    efficiency_values = {(flavor, wp): efficiency(counts[(flavor, wp)], counts[(flavor, "den")])
                         for flavor in FLAVORS for wp in INCLUSIVE_WPS}
    mcstat_uncertainties = compute_mcstat_uncertainties(counts, variances)
    update_output(args.output, [
        (prefix, sample_category(args.sample, efficiency_values, edges),
         "Selected-AK4 UParTAK4 b-tag efficiency", "efficiency", "MC tagging efficiency"),
        (f"{prefix}_mcstat_unc", sample_category(args.sample, mcstat_uncertainties, edges),
         "Weighted-binomial MC-statistical uncertainty of selected-AK4 UParTAK4 b-tag efficiency", "uncertainty",
         "Weighted-binomial MC tagging-efficiency uncertainty"),
    ])


if __name__ == "__main__":
    main()
