import argparse
import json
import os
from datetime import datetime
import subprocess

# The known analysis channels (key) and which skim they use (value)
ANA_CHANNELS = {
        "0lep_0FJ"     : "0lep_0FJ",
        "0lep_1FJ"     : "0lep_1FJ",
        "0lep_1FJ_met" : "0lep_1FJ",
        "0lep_2FJ"     : "0lep_2FJ",
        "0lep_2FJ_met" : "0lep_2FJ",
        "0lep_3FJ"     : "0lep_3FJ",
        "1lep_1FJ"     : "1lep_1FJ",
        "1lep_2FJ"     : "1lep_1FJ",
        #"2lepSS"       : "2lepSS", # DNE yet
        "2lep_1FJ"     : "2lep_1FJ", # Analysis channel shared between SF and OF
        "2lep_2FJ"     : "2lep_2FJ",
        "3lep"         : "3lep",
        "4lep"         : "4lep",
}
# MET-trigger subsets may have their own efficiency payloads.  They remain
# excluded from final channel merging by the b-tag YAML, but are valid raw
# production channels here.
B_TAG_EFF_EXCLUDED_CHANNELS = {"all_events"}
SUPPORTED_BTAG_EFF_YEARS = {"2016preVFP", "2016postVFP", "2017", "2018", "2024Prompt"}

# Merge the input jsons into one dictionary
def merge_jsons(input_paths_lst):
    out_dict = {"samples": {}}

    def _append_info_to_dict(the_dict,path_to_json):
        # Modify the dict in place with the info from a given json
        with open(path_to_json, 'r') as file:
            data = json.load(file)["samples"]
            for k,v in data.items():
                if k in the_dict: raise Exception(f"ERROR: key \"{k}\" already exsists in the output dict")
                the_dict["samples"][k] = v

    # Loop over paths
    for path in input_paths_lst:

        # This isn't a path! It's a json file
        if path.endswith(".json"):
            _append_info_to_dict(out_dict,path)

        # This is a dir
        elif os.path.isdir(path):

            # Loop over files in this path
            for filename in os.listdir(path):

                # Skip any non json files
                if not filename.endswith('.json'): continue

                # Append the info from this json into the out dict
                _append_info_to_dict(out_dict,os.path.join(path,filename))

        # It's not a json or a dir, what are you trying to pass?
        else:
            raise Exception("Unknown input type, please pass json files or a directory with json files in it.")

    return out_dict


# Apply prefixes to samples in the input jsons
def apply_prefix(in_dict,prefix):
    for dataset_name in in_dict["samples"]:
        flst_with_prefixes = []
        for fname in in_dict["samples"][dataset_name]["files"]:
            flst_with_prefixes.append(os.path.join(prefix+fname))
            flst_with_prefixes.sort()
        in_dict["samples"][dataset_name]["files"] = flst_with_prefixes


# Do a check of the merged json to make sure it does not have more than one kind (if we're in local mode)
# This is because the runAnalysis assumes all inputs are of the same kind
def check_inputs(merged_json_dict, mode, btag_eff=False):
    if len(merged_json_dict["samples"]) == 0:
        raise Exception("Error, no samples specified")
    # Local mode is split into one runAnalysis invocation per sample below.


def select_btag_year(merged_json_dict, year):
    """Retain exactly one metadata year for a b-tag efficiency production."""
    samples = merged_json_dict["samples"]
    selected = {name: info for name, info in samples.items()
                if info["metadata"].get("year") == year}
    if not selected:
        raise Exception(f"No samples with metadata.year={year!r} were found for --btag-eff")
    merged_json_dict["samples"] = selected


def output_dir_for_channel(outpath, outname, channel, mode, btag_eff, year=None):
    """Return the stable output location for one channel/backend invocation."""
    if btag_eff and mode == "slurm":
        return os.path.join(outpath, year, channel)
    return os.path.join(outpath, f"{channel}_{outname}")



################### Main function ###################
def main():

    # Set up the command line parser
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--jsons', nargs='+',    help = 'Input json file(s) containing files and metadata')
    parser.add_argument('-c', '--channels', nargs='+', help = 'Which analysis selection channels to run')
    parser.add_argument('-m', '--mode',                help = 'Which mode to run in (local, condor, or slurm)', choices=['local','condor','slurm'])
    parser.add_argument('-o', '--outpath',             help = 'Output directory', default=".")
    parser.add_argument('-n', '--outname',             help = 'Output name', default="rdf_output")
    parser.add_argument('-r', '--run',                 help = 'Which run (2 or 3)', choices=['2','3'])
    parser.add_argument('-p', '--prefix',              help = 'Prefix to append to the file paths', default="/ceph/cms/")
    parser.add_argument('-j', '--n-cores',             help = 'Number of cores (local) or CPUs per job (slurm/condor)', type=int, default=None)
    parser.add_argument('-f', '--files-per-job',       help = 'Number of input files per job (default: 10)', default=10, type=int)
    parser.add_argument('-d', '--dry-run',             help = 'Do not actually execute the run command', action='store_true')
    parser.add_argument('--store-hlt',                 help = 'Store HLT trigger branches in output', action='store_true')
    parser.add_argument('--memory',                    help = 'Memory per job for slurm submission (default: 8gb)', default=None)
    parser.add_argument('--time',                      help = 'Time limit per job for slurm submission (default: 04:00:00)', default=None)
    parser.add_argument('--sample',                    help = 'Regex to filter which samples to submit (slurm/condor only)', default=None)
    parser.add_argument('--btag-eff',                  help = 'Write raw selected-AK4 b-tag efficiency histograms (MC only)', action='store_true')
    parser.add_argument('--year',                      help = 'Required metadata year for --btag-eff production')
    parser.add_argument('--skip-btag-sf',              help = 'Skip b-tag SF application (normally enabled)', action='store_true')
    parser.add_argument('--qos',                       help = 'qos for slurm submission (slurm only)', default='avery')
    args = parser.parse_args()
    if args.btag_eff and not args.year:
        parser.error("--btag-eff requires --year (for example, --year 2024Prompt)")
    if args.btag_eff and args.year not in SUPPORTED_BTAG_EFF_YEARS:
        parser.error(f"--btag-eff is unsupported for {args.year}")
    if args.btag_eff and args.sample:
        parser.error("--sample cannot be used with --btag-eff because the final payload requires every configured sample.")

    # Get the list of channels to run over (if we ask for "all", use known analysis channels)
    if args.channels == ["all"]:
        channels_to_run = [channel for channel in ANA_CHANNELS
                           if not args.btag_eff or channel not in B_TAG_EFF_EXCLUDED_CHANNELS]
    else: channels_to_run = args.channels

    # Run RDF once for each specified channel
    for chan_name in channels_to_run:
        print(f"\nRunning for channel {chan_name}\n")

        # Make sure this is a channel RDF knows about
        if (chan_name not in ANA_CHANNELS.keys()) and (chan_name != "all_events"):
            raise Exception(f"Error unknown channel: {chan_name}")
        if args.btag_eff and chan_name in B_TAG_EFF_EXCLUDED_CHANNELS:
            raise Exception(f"--btag-eff production is excluded for {chan_name}")

        # Merge the input jsons
        if args.jsons is not None:
            merged_json_dict = merge_jsons(args.jsons)
        else:
            # If no input jsons specified, look them up based on analysis channel
            # Normal production includes signal, background, and data.  The
            # b-tag efficiency mode is MC-only, so do not create data jobs.
            run_base = f"etc/input_sample_jsons/run{args.run}"
            if chan_name == "all_events":
                jsons = [f"{run_base}/sig/all_events/"]
            else:
                jsons = [
                    f"{run_base}/sig/all_events/",
                    f"{run_base}/bkg/{ANA_CHANNELS[chan_name]}",
                ]
                if not args.btag_eff:
                    jsons.append(f"{run_base}/data/{ANA_CHANNELS[chan_name]}")
            merged_json_dict = merge_jsons(jsons)

        # Prepend the appropriate prefix to all files in the input json
        if args.prefix is not None:
            apply_prefix(merged_json_dict,args.prefix)

        if args.btag_eff:
            select_btag_year(merged_json_dict, args.year)

        # Validate before creating output artifacts or invoking a backend.
        check_inputs(merged_json_dict, args.mode, args.btag_eff)

        # B-tag Slurm production writes the converter's documented layout
        # directly: INPUT_ROOT/CHANNEL/{manifest.json,SAMPLE/output_N.root}.
        # The submitter creates it only after checking that it cannot mix with
        # a previous submission.  Keep the historical outname layout for all
        # other workflows.
        # A local invocation cannot mix samples/years in one RDataFrame.  The
        # batch backends already split samples themselves.
        jobs = [(None, merged_json_dict)]
        if args.mode == "local":
            jobs = [(sample, {"samples": {sample: info}})
                    for sample, info in merged_json_dict["samples"].items()]

        for sample_name, job_config in jobs:
            outname = f"{chan_name}_{args.outname}"
            suffix = f"_{sample_name}" if sample_name else ""
            if not os.path.exists("merged_jsons"): os.mkdir("merged_jsons")
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
            merged_json_name = os.path.join("merged_jsons", f"merged_{outname}{suffix}_{timestamp}.json")
            print(f"  -> Writing merged file \"{merged_json_name}\"")
            with open(merged_json_name, 'w') as outfile:
                json.dump(job_config, outfile, indent=4)

            outdir = output_dir_for_channel(args.outpath, args.outname, chan_name, args.mode,
                                            args.btag_eff, args.year)
            if sample_name:
                outdir = os.path.join(outdir, sample_name)
            if not (args.btag_eff and args.mode == "slurm") and not os.path.isdir(outdir):
                os.makedirs(outdir)
            print(f"  -> RDF output will be located in: {outdir}")

            # Construct the backend command.
            hlt_flag = " --store_hlt" if args.store_hlt else ""
            btag_eff_flag = " --btag-eff" if args.btag_eff else ""
            skip_btag_sf_flag = " --skip-btag-sf" if args.skip_btag_sf else ""
            sample_flag = f" --sample '{args.sample}'" if args.sample else ""
            if args.mode == "local":
                local_name = f"{args.outname}_{sample_name}" if sample_name else args.outname
                command = f"bin/runAnalysis -i {merged_json_name} -o {outdir} -n {local_name} -a {chan_name} -j {args.n_cores or 64} --run_number {args.run} --progress{hlt_flag}{' --btag_eff' if args.btag_eff else ''}{' --skip-btag-sf' if args.skip_btag_sf else ''}"
                print(f"  -> Now running command \"{command}\"...\n")
                if not args.dry_run:
                    subprocess.run(command, shell=True, check=True)
            elif args.mode == "condor":
                dry_run_flag = " --dry-run" if args.dry_run else ""
                ncores_flag = f" -j {args.n_cores}" if args.n_cores else ""
                command = f"python3 condor/submit.py -c {merged_json_name} -a {chan_name} --run_number {args.run} --files-per-job {args.files_per_job}{ncores_flag}{hlt_flag}{btag_eff_flag}{skip_btag_sf_flag}{sample_flag}{dry_run_flag}"
                print(f"  -> Running command \"{command}\"...\n")
                subprocess.run(command, shell=True, check=True)
            elif args.mode == "slurm":
                dry_run_flag = " --dry-run" if args.dry_run else ""
                memory_flag = f" --memory {args.memory}" if args.memory else ""
                time_flag = f" --time {args.time}" if args.time else ""
                ncores_flag = f" -j {args.n_cores}" if args.n_cores else ""
                year_flag = f" --year {args.year}" if args.btag_eff else ""
                qos_flag = f" --qos {args.qos}" if args.qos else ""
                command = f"python3 slurm/submit.py -c {merged_json_name} -a {chan_name} --run_number {args.run} --files-per-job {args.files_per_job} --account avery{qos_flag} -o {outdir}{year_flag}{hlt_flag}{btag_eff_flag}{skip_btag_sf_flag}{dry_run_flag}{memory_flag}{time_flag}{ncores_flag}{sample_flag}"
                print(f"  -> Running command \"{command}\"...\n")
                subprocess.run(command, shell=True, check=True)

            print("Done!")

if __name__ == "__main__":
    main()
