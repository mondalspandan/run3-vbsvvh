#!/usr/bin/env python3
"""
SLURM job submission script for run3-vbsvvh preselection framework.

Splits input files across multiple jobs and organizes outputs by sample.
Tracks job status in a manifest.json file.

Usage:
    python slurm/submit.py -c merged_jsons/merged_r2_0lep_0FJ.json \
                           -a 0lep_0FJ -r 2 -o output/test --files-per-job 1
"""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from glob import glob
from pathlib import Path
from typing import Dict, List, Any, Optional

import uproot


# Constants
SLURM_OUTPUT_DIR = "jobs"
DEFAULT_FILES_PER_JOB = 10
DEFAULT_NCPUS = 4
DEFAULT_MEMORY = "8gb"
DEFAULT_PARTITION = "hpg-default"
DEFAULT_TIME = "04:00:00"


# ============================================================================
# Job Manifest for Tracking
# ============================================================================

class JobManifest:
    """Tracks job submissions and their status."""

    def __init__(self, task_dir: Path):
        self.task_dir = task_dir
        self.manifest_path = task_dir / "manifest.json"
        self.data = {
            "task_name": task_dir.name,
            "created": datetime.now().isoformat(),
            "scheduler": "slurm",
            "config": "",
            "analysis": "",
            "run_number": 0,
            "output_dir": "",
            "jobs": {}
        }

    def set_metadata(self, config: str, analysis: str, run_number: int, output_dir: str):
        self.data["config"] = config
        self.data["analysis"] = analysis
        self.data["run_number"] = run_number
        self.data["output_dir"] = output_dir

    def add_job(self, job_id: str, sample_name: str, job_idx: int,
                input_files: List[str], job_dir: str):
        self.data["jobs"][job_id] = {
            "sample": sample_name,
            "job_idx": job_idx,
            "input_files": input_files,
            "n_files": len(input_files),
            "job_dir": job_dir,
            "status": "prepared",
            "slurm_job_id": None,
            "submit_time": None,
        }

    def mark_submitted(self, job_id: str, slurm_job_id):
        if job_id in self.data["jobs"]:
            job = self.data["jobs"][job_id]
            job["status"] = "submitted"
            job["slurm_job_id"] = slurm_job_id
            job["submit_time"] = datetime.now().isoformat()

    def save(self):
        with open(self.manifest_path, 'w') as f:
            json.dump(self.data, f, indent=2)

    @classmethod
    def load(cls, task_dir: Path) -> 'JobManifest':
        manifest = cls(task_dir)
        if manifest.manifest_path.exists():
            with open(manifest.manifest_path) as f:
                manifest.data = json.load(f)
        return manifest


# ============================================================================
# Utility Functions
# ============================================================================

def parse_args():
    parser = argparse.ArgumentParser(
        description="Submit SLURM jobs for run3-vbsvvh preselection",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Submit jobs
    python slurm/submit.py -c merged_jsons/merged_r2_0lep_0FJ.json \\
                           -a 0lep_0FJ -r 2 -o output/v26_test --files-per-job 1

    # Dry run
    python slurm/submit.py -c merged_jsons/merged_r2_0lep_0FJ.json \\
                           -a 0lep_0FJ -r 2 -o output/v26_test --dry-run
        """
    )
    parser.add_argument("-c", "--config", required=True,
                        help="Path to config JSON file")
    parser.add_argument("-a", "--analysis", required=True,
                        help="Analysis channel (e.g., 0lep_0FJ)")
    parser.add_argument("-r", "--run_number", required=True, type=int, choices=[2, 3],
                        help="Run number (2 or 3)")
    parser.add_argument("-o", "--output-dir", required=True,
                        help="Output directory on shared filesystem")
    parser.add_argument("-t", "--tag", default="",
                        help="Optional tag for task naming")
    parser.add_argument("-j", "--ncpus", type=int, default=DEFAULT_NCPUS,
                        help=f"CPUs per job (default: {DEFAULT_NCPUS})")
    parser.add_argument("-m", "--memory", default=DEFAULT_MEMORY,
                        help=f"Memory per job (default: {DEFAULT_MEMORY})")
    parser.add_argument("--partition", default=DEFAULT_PARTITION,
                        help=f"SLURM partition (default: {DEFAULT_PARTITION})")
    parser.add_argument("--time", default=DEFAULT_TIME,
                        help=f"Time limit per job (default: {DEFAULT_TIME})")
    parser.add_argument("--files-per-job", type=int, default=DEFAULT_FILES_PER_JOB,
                        help=f"Number of input files per job (default: {DEFAULT_FILES_PER_JOB})")
    parser.add_argument("--events-per-job", type=int, default=None,
                        help="Max events per job (takes priority over --files-per-job)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Prepare jobs but don't submit")
    parser.add_argument("--sample", default=None,
                        help="Only submit jobs for samples matching this regex")
    parser.add_argument("--spanet-training", action="store_true",
                        help="Generate SPANet training data (--spanet_training flag)")
    parser.add_argument("--spanet-infer", action="store_true",
                        help="Run SPANet inference (--spanet_infer flag)")
    parser.add_argument("--store_hlt", action="store_true",
                        help="Store HLT trigger branches in output")
    parser.add_argument("--account", default=None,
                        help="SLURM account (e.g., avery)")
    parser.add_argument("--qos", default=None,
                        help="SLURM QoS (e.g., avery-b)")

    return parser.parse_args()


def split_into_chunks(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def get_event_count(file_path: str) -> int:
    try:
        with uproot.open(file_path) as f:
            return f["Events"].num_entries
    except Exception as e:
        print(f"  WARNING: Could not read {file_path}: {e}")
        return 0


def estimate_events_per_file(files: List[str]) -> int:
    if not files:
        return 0
    files_to_check = files[:2]
    counts = [get_event_count(f) for f in files_to_check]
    return max(counts) if counts else 0


def split_by_events(files: List[str], events_per_file: int,
                    max_events_per_job: int) -> List[List[str]]:
    if events_per_file <= 0:
        return [[f] for f in files]
    files_per_job = max(1, max_events_per_job // events_per_file)
    return split_into_chunks(files, files_per_job)


def expand_file_glob(file_pattern: str) -> List[str]:
    if not any(c in file_pattern for c in ('*', '?', '[')):
        return [file_pattern]
    return sorted(glob(file_pattern))


def create_job_config(sample_name: str, sample_config: Dict,
                      file_list: List[str], job_idx: int) -> Dict:
    return {
        "samples": {
            sample_name: {
                "trees": sample_config["trees"],
                "files": file_list,
                "metadata": sample_config["metadata"].copy()
            }
        }
    }


def generate_slurm_script(task_dir: Path, job_dir: Path, job_name: str,
                          args: argparse.Namespace,
                          sample_name: str, job_idx: int) -> Path:
    """Generate a SLURM .sbatch script for a job."""
    script_path = job_dir / "job.sbatch"
    config_path = job_dir / "config.json"

    # Build extra flags
    extra_flags = ""
    if args.spanet_training:
        extra_flags += " --spanet_training"
    if args.spanet_infer:
        extra_flags += " --spanet_infer"
    if args.store_hlt:
        extra_flags += " --store_hlt"

    # Add optional account and qos lines
    acct_line = f"#SBATCH --account={args.account}\n" if args.account else ""
    qos_line  = f"#SBATCH --qos={args.qos}\n" if args.qos else ""

    # Arguments for executable.sh:
    # TASK_DIR N_CPUS CONFIG_PATH OUTPUT_DIR ANALYSIS RUN_NUMBER SAMPLE_NAME JOB_IDX [EXTRA_FLAGS]
    exe_args = (f"{task_dir} {args.ncpus} {config_path} {args.output_dir} "
                f"{args.analysis} {args.run_number} {sample_name} {job_idx}{extra_flags}")

    script_content = f"""#!/bin/bash
#SBATCH --job-name={sample_name}_{job_idx}
#SBATCH --output={job_dir}/slurm_%j.out
#SBATCH --error={job_dir}/slurm_%j.err
#SBATCH --mem={args.memory}
#SBATCH --time={args.time}
#SBATCH --cpus-per-task={args.ncpus}
#SBATCH --partition={args.partition}
{acct_line}{qos_line}
bash {task_dir}/executable.sh {exe_args}
"""

    with open(script_path, "w") as f:
        f.write(script_content)

    return script_path


def generate_array_sbatch(task_dir: Path, job_entries: List[dict],
                          args: argparse.Namespace) -> Path:
    """
    Generate a SLURM array .sbatch script and job_list.txt for the entire task.

    job_entries is a list of dicts with keys: job_dir_name, sample_name, job_idx.
    Returns path to array.sbatch.
    """
    n_jobs = len(job_entries)

    # Write job_list.txt: one line per array task, indexed from 0
    # Format: job_dir_name sample_name job_idx
    list_path = task_dir / "job_list.txt"
    with open(list_path, "w") as f:
        for entry in job_entries:
            f.write(f"{entry['job_dir_name']} {entry['sample_name']} {entry['job_idx']}\n")

    # Build extra flags
    extra_flags = ""
    if args.spanet_training:
        extra_flags += " --spanet_training"
    if args.spanet_infer:
        extra_flags += " --spanet_infer"
    if args.store_hlt:
        extra_flags += " --store_hlt"

    # Add optional account and qos lines
    acct_line = f"#SBATCH --account={args.account}\n" if args.account else ""
    qos_line  = f"#SBATCH --qos={args.qos}\n" if args.qos else ""

    script_path = task_dir / "array.sbatch"
    script_content = f"""#!/bin/bash
#SBATCH --job-name={task_dir.name}
#SBATCH --mem={args.memory}
#SBATCH --time={args.time}
#SBATCH --cpus-per-task={args.ncpus}
#SBATCH --partition={args.partition}
{acct_line}{qos_line}
#SBATCH --array=0-{n_jobs - 1}
#SBATCH --output={task_dir}/slurm_default_%A_%a.out
#SBATCH --error={task_dir}/slurm_default_%A_%a.err

# Read job parameters from job_list.txt
LINE=$(sed -n "$((SLURM_ARRAY_TASK_ID + 1))p" {list_path})
JOB_DIR_NAME=$(echo "$LINE" | awk '{{print $1}}')
SAMPLE_NAME=$(echo "$LINE" | awk '{{print $2}}')
JOB_IDX=$(echo "$LINE" | awk '{{print $3}}')

JOB_DIR="{task_dir}/$JOB_DIR_NAME"

# Redirect output to per-job directory
exec > "$JOB_DIR/slurm_${{SLURM_ARRAY_JOB_ID}}_${{SLURM_ARRAY_TASK_ID}}.out" 2>"$JOB_DIR/slurm_${{SLURM_ARRAY_JOB_ID}}_${{SLURM_ARRAY_TASK_ID}}.err"

bash {task_dir}/executable.sh {task_dir} {args.ncpus} $JOB_DIR/config.json {args.output_dir} {args.analysis} {args.run_number} $SAMPLE_NAME $JOB_IDX{extra_flags}
"""

    with open(script_path, "w") as f:
        f.write(script_content)

    return script_path


def extract_slurm_job_id(sbatch_output: str) -> Optional[int]:
    """Extract job ID from sbatch output (e.g., 'Submitted batch job 12345')."""
    match = re.search(r'Submitted batch job (\d+)', sbatch_output)
    if match:
        return int(match.group(1))
    return None


def create_tarball(preselection_dir: Path) -> Path:
    """Create tarball of the analysis code for shipping to compute nodes."""
    tarball_path = preselection_dir / "slurm" / "package.tar.gz"

    spanet_run2_dir = "spanet/run2/v31/"
    spanet_run3_dir = "spanet/v2/"
    # Items to include in tarball (from preselection dir)
    preselection_items = [
        "Makefile", "src", "include", "corrections", "bdt",
        spanet_run2_dir, spanet_run3_dir
    ]

    # Build tar command, only include items that exist
    tar_items = []
    for item in preselection_items:
        if (preselection_dir / item).exists():
            tar_items.append(item)

    cmd = ["tar", "-czf", str(tarball_path)] + tar_items
    print(f"Creating tarball: {' '.join(cmd)}")
    subprocess.run(cmd, cwd=preselection_dir, check=True)

    return tarball_path


# ============================================================================
# Main
# ============================================================================

def main():
    args = parse_args()

    # Determine paths
    script_dir = Path(__file__).parent.resolve()
    preselection_dir = script_dir.parent
    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = preselection_dir / config_path

    if not config_path.exists():
        print(f"ERROR: Config file not found: {config_path}")
        sys.exit(1)

    # Create tarball of analysis code
    print("Creating tarball...")
    create_tarball(preselection_dir)

    # Load config
    with open(config_path) as f:
        config = json.load(f)

    samples = config.get("samples", {})
    if not samples:
        print("ERROR: No samples found in config")
        sys.exit(1)

    # Filter samples if --sample specified
    if args.sample:
        pattern = re.compile(args.sample)
        samples = {k: v for k, v in samples.items() if pattern.search(k)}
        if not samples:
            print(f"ERROR: No samples match pattern '{args.sample}'")
            sys.exit(1)

    # Generate task name
    config_basename = config_path.stem
    job_name = f"{config_basename}_{args.analysis}"
    if args.tag:
        job_name = f"{job_name}_{args.tag}"

    # Create task directory
    task_dir = preselection_dir / "slurm" / SLURM_OUTPUT_DIR / job_name
    if task_dir.exists():
        print(f"ERROR: Task directory already exists: {task_dir}")
        print("Please remove it or use a different --tag")
        sys.exit(1)

    task_dir.mkdir(parents=True)

    # Copy executable and tarball to task dir
    subprocess.run(["cp", str(script_dir / "executable.sh"),
                    str(task_dir / "executable.sh")], check=True)
    subprocess.run(["cp", str(script_dir / "package.tar.gz"),
                    str(task_dir / "package.tar.gz")], check=True)

    # Initialize manifest
    manifest = JobManifest(task_dir)
    manifest.set_metadata(args.config, args.analysis, args.run_number, args.output_dir)

    # Create output directory
    output_path = Path(args.output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*60}")
    print(f"SLURM Job Submission for run3-vbsvvh")
    print(f"{'='*60}")
    print(f"Config:       {args.config}")
    print(f"Analysis:     {args.analysis}")
    print(f"Run number:   {args.run_number}")
    print(f"Output dir:   {args.output_dir}")
    print(f"Tag:          {args.tag or '(none)'}")
    if args.events_per_job:
        print(f"Events/job:   {args.events_per_job}")
    else:
        print(f"Files/job:    {args.files_per_job}")
    print(f"CPUs/job:     {args.ncpus}")
    print(f"Memory/job:   {args.memory}")
    print(f"Partition:    {args.partition}")
    print(f"Time limit:   {args.time}")
    print(f"Task dir:     {task_dir}")
    print(f"{'='*60}\n")

    # Process each sample
    job_entries = []  # For array sbatch: list of {job_dir_name, sample_name, job_idx}
    total_jobs = 0

    for sample_name, sample_config in samples.items():
        # Expand file globs
        all_files = []
        for file_pattern in sample_config["files"]:
            expanded = expand_file_glob(file_pattern)
            if not expanded:
                print(f"  WARNING: No files found for pattern: {file_pattern}")
            all_files.extend(expanded)

        if not all_files:
            print(f"  Skipping {sample_name}: no files found")
            continue

        # Split files into chunks
        if args.events_per_job:
            events_per_file = estimate_events_per_file(all_files)
            file_chunks = split_by_events(all_files, events_per_file, args.events_per_job)
            n_jobs = len(file_chunks)
            print(f"  {sample_name}: {len(all_files)} files, ~{events_per_file} evts/file -> {n_jobs} job(s)")
        else:
            file_chunks = split_into_chunks(all_files, args.files_per_job)
            n_jobs = len(file_chunks)
            print(f"  {sample_name}: {len(all_files)} files -> {n_jobs} job(s)")

        # Create job configs and per-job sbatch scripts
        for job_idx, file_chunk in enumerate(file_chunks):
            job_dir_name = f"{sample_name}_{job_idx}" if n_jobs > 1 else sample_name
            job_dir = task_dir / job_dir_name
            job_dir.mkdir(parents=True)

            # Write job-specific config
            job_config = create_job_config(sample_name, sample_config, file_chunk, job_idx)
            with open(job_dir / "config.json", "w") as f:
                json.dump(job_config, f, indent=2)

            # Generate per-job SLURM script (used for resubmission)
            generate_slurm_script(
                task_dir, job_dir, job_name, args,
                sample_name, job_idx
            )

            job_entries.append({
                "job_dir_name": job_dir_name,
                "sample_name": sample_name,
                "job_idx": job_idx,
            })

            # Track in manifest
            manifest.add_job(
                job_id=job_dir_name,
                sample_name=sample_name,
                job_idx=job_idx,
                input_files=file_chunk,
                job_dir=str(job_dir)
            )
            total_jobs += 1

    if not job_entries:
        print("ERROR: No jobs to submit (all samples had no files)")
        sys.exit(1)

    # Generate array sbatch and job list
    array_sbatch = generate_array_sbatch(task_dir, job_entries, args)

    # Save manifest
    manifest.save()

    print(f"\n{'='*60}")
    print(f"Total jobs to submit: {total_jobs}")
    print(f"{'='*60}\n")

    if args.dry_run:
        print("DRY RUN: Jobs prepared but not submitted")
        print(f"Job directories are in: {task_dir}")
        print(f"Manifest saved to: {task_dir}/manifest.json")
        print(f"Array sbatch: {array_sbatch}")
        print(f"Job list: {task_dir / 'job_list.txt'}")
        print("\nTo submit manually:")
        print(f"  sbatch {array_sbatch}")
        print("\nTo submit a single job:")
        print(f"  sbatch {task_dir}/<sample_name>/job.sbatch")
        print("\nTo check status:")
        print(f"  squeue -u $USER")
        return

    # Submit as a single array job
    print("Submitting job array...")
    result = subprocess.run(["sbatch", str(array_sbatch)],
                           capture_output=True, text=True)

    if result.returncode != 0:
        print(f"  ERROR submitting array: {result.stderr.strip()}")
        print(f"\nTo retry manually:")
        print(f"  sbatch {array_sbatch}")
        sys.exit(1)

    array_base_id = extract_slurm_job_id(result.stdout)
    if array_base_id:
        print(f"  Array job submitted: {array_base_id} ({total_jobs} tasks)")
        # Mark all jobs as submitted with composite array IDs
        for i, entry in enumerate(job_entries):
            manifest.mark_submitted(entry["job_dir_name"], f"{array_base_id}_{i}")
    else:
        print(f"  Array job submitted (couldn't parse job ID)")

    # Save manifest with job IDs
    manifest.save()

    print(f"\nManifest saved to: {task_dir}/manifest.json")
    print(f"Output will appear in: {args.output_dir}/")
    print(f"\nTo check status:")
    print(f"  squeue -u $USER")


if __name__ == "__main__":
    main()
