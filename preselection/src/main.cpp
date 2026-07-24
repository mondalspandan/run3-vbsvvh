#include "ROOT/RDataFrame.hxx"
#include "ROOT/RDFHelpers.hxx"
#include "ROOT/RLogger.hxx"

#include "weights.h"
#include "corrections.h"
#include "selections.h"
#include "utils.h"
#include "genSelections.h"

#include "argparser.hpp"
#include "cutflow.h"

#include "spanet.h"
#include "spanet_run2.h"



struct MyArgs : public argparse::Args {
    std::string &spec       = kwarg("i,input", "spec.json path");
    std::string &ana        = kwarg("a,ana", "Which skim selection channel for event selection");
    std::string &name       = kwarg("n,name", "Naming tag for the output").set_default("rdf_output");
    std::string &outdir     = kwarg("o,outdir", "Path to output").set_default(".");
    std::string &run_number = kwarg("r,run_number", "Run number (2 or 3)");
    
    int &batch_size = kwarg("b,batch_size", "batch size for spanet inference").set_default(64);
    int &nthread    = kwarg("j,nthread", "number of threads for ROOT").set_default(0);

    bool &progress = flag("progress", "Show progress bar").set_default(false);
    bool &dumpInput              = flag("dump_input", "Dump all input branches to output ROOT file").set_default(false);
    bool &makeSpanetTrainingdata = flag("spanet_training", "Only make training data for SPANet").set_default(false);
    bool &runSPANetInference     = flag("spanet_infer", "Run SPANet inference").set_default(false);
    bool &storeHLT = flag("store_hlt", "Store HLT trigger branches in output").set_default(false);
    bool &cutflow = flag("cutflow", "Print cutflow").set_default(false);
    bool &no_systs = flag("no_systs", "Skip all JES/JER variation branches (nominal only)").set_default(false);
};

RNode runAnalysis(RNode df, std::string ana, std::string run_number, bool isSignal, SPANet::SPANetInference *spanet_inference, SPANetRun2::SPANetInference *spanet_inference_run2, bool runSPANetInference = false, bool makeSpanetTrainingdata = false)
{
    std::cout << " -> Run " << ana << "::runAnalysis()" << std::endl;

    df = runPreselection(df, ana, makeSpanetTrainingdata);
    
    if (isSignal) {
        df = GenSelections(df);
    }

    if (!makeSpanetTrainingdata && runSPANetInference) {
        std::cout << "Running spanet" << std::endl;
        if (run_number == "2"){
            df = spanet_inference_run2->RunSPANetInference(df);
            df = spanet_inference_run2->ParseSpanetInference(df);
        }
        else {
            df = spanet_inference->RunSPANetInference(df);
            df = spanet_inference->ParseSpanetInference(df);
        }
    }
    return df;
}

int main(int argc, char** argv) {
    // Read input args
    auto args = argparse::parse<MyArgs>(argc, argv);
    std::string input_spec = args.spec;
    std::string output_file = args.name;

    setStoreSysts(!args.no_systs);

    if (args.nthread > 64) {
        std::cerr << "Error: nthread cannot exceed 64 (requested: " << args.nthread << ")" << std::endl;
        std::exit(EXIT_FAILURE);
    }

    std::vector<std::string> channels = {
        "all_events",
        "0lep_0FJ",
        "0lep_1FJ",
        "0lep_1FJ_met",
        "0lep_2FJ",
        "0lep_2FJ_met",
        "0lep_3FJ",
        "1lep_1FJ",
        "1lep_2FJ",
        "2lep_1FJ", // Currently shared between SF and OF
        "2lepSS",
        "2lep_2FJ",
        "3lep",
        "4lep",
    };
    if (std::find(channels.begin(), channels.end(), args.ana) == channels.end()) {
        if (!args.makeSpanetTrainingdata) {
            std::cerr << "Did not recognize analysis tag: " << args.ana << std::endl;
            std::exit(EXIT_FAILURE);
        }
    }

    // Create output directory
    std::string output_dir = setOutputDirectory(args.outdir, args.makeSpanetTrainingdata);
    
    if (args.run_number != "2" && args.run_number != "3") {
        throw std::runtime_error("Invalid run_number: must be 2 or 3");
    }
    std::cout << " -> Running analysis for Run " << args.run_number << std::endl;
    
    std::unique_ptr<SPANet::SPANetInference> spanet_inference;
    std::unique_ptr<SPANetRun2::SPANetInference> spanet_inference_run2;

    if (args.runSPANetInference) {
        std::string  model_path;

        model_path = "spanet/run2/v31/model.onnx";
        std::cout << " -> Loading Run 2 ONNX model from: " << model_path << std::endl;
        spanet_inference_run2 = std::make_unique<SPANetRun2::SPANetInference>(model_path, args.batch_size);
        std::cout << "    ONNX session loaded successfully." << std::endl;
        
        model_path = "spanet/v2/model.onnx";
        std::cout << " -> Loading Run 3 ONNX model from: " << model_path << std::endl;
        spanet_inference = std::make_unique<SPANet::SPANetInference>(model_path, args.batch_size);
        std::cout << "    ONNX session loaded successfully." << std::endl;
    }

    if (args.runSPANetInference && args.nthread > 1) {
        std::cout << " -> SPANet inference requires single-threaded execution, setting nthread=1" << std::endl;
        args.nthread = 1;
    }

    if (args.nthread > 1) {
        ROOT::EnableImplicitMT(args.nthread);
        ROOT::EnableThreadSafety();
    }

    // Load df
    ROOT::RDataFrame df_ = ROOT::RDF::Experimental::FromSpec(input_spec);
    if (args.progress) { // progress bar isn't needed if using condor so turn off by default
        ROOT::RDF::Experimental::AddProgressBar(df_);
    }

    // Get sample category from config file
    std::string kind = getCategoryFromConfig(input_spec);
    std::cout << " -> Sample kind from config: " << kind << std::endl;

    // Set output file name and input type based on kind
    bool isData = false;
    bool isSignal = false;
    if (kind.find("data") != std::string::npos) {
        isData = true;
        if (output_file.empty()) {
            output_file = "data";
        }
    }
    else if (kind.find("sig") != std::string::npos) {
        // Handle categories like "sig", "sig_c2v_1p5_c3_1p0", etc.
        isSignal = true;
        if (output_file.empty()) {
            output_file = "sig";
        }
    }
    else if (kind.find("bkg") != std::string::npos) {
        // Handle categories like "bkg", "bkg_QCD", "bkg_ttbar", etc.
        if (output_file.empty()) {
            output_file = "bkg";
        }
    }
    else {
        std::cerr << "Unknown kind in config: " << kind << std::endl;
        std::cerr << "Expected: data, sig, or bkg*" << std::endl;
        std::exit(EXIT_FAILURE);
    }

    bool makeSpanetTrainingdata = args.makeSpanetTrainingdata;
    if (!isSignal) {
        makeSpanetTrainingdata = false; // do not make training data for non-signal samples
    }

    // Define metadata
    auto df = defineMetadata(df_, isData);

    Cutflow::SetWeightCol(isData ? "1" : "weight");

    if (args.cutflow) Cutflow::Enable();

    // Run analysis
    if (isData) {
        std::cout << " -> Running data analysis" << std::endl;
        df = applyDataCorrections(df);
        df = runAnalysis(df, args.ana, args.run_number, isSignal, spanet_inference.get(), spanet_inference_run2.get(), args.runSPANetInference);
        df = applyDataWeights(df);
        //df = removeDuplicates(df);
    } else {
        std::cout << " -> Running MC analysis" << std::endl;
        df = applyMCCorrections(df);
        df = runAnalysis(df, args.ana, args.run_number, isSignal, spanet_inference.get(), spanet_inference_run2.get(), args.runSPANetInference, makeSpanetTrainingdata);
        df = applyMCWeights(df);
    }

    Cutflow::Add(df, "After SFs and corrections");

    if (isSignal && makeSpanetTrainingdata) {
        std::cout << " -> Saving SPANet training data" << std::endl;
        saveSpanetSnapshot(df, output_dir, output_file);
        Cutflow::Print();
        return 0; // Exit after saving training data
    }

    saveSnapshot(df, output_dir, output_file, isSignal, args.dumpInput, args.storeHLT);
    Cutflow::Print();

    return 0;
}
