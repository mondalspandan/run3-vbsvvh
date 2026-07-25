#include "weights.h"

/*
############################################
GOLDEN JSON
############################################
*/

RNode applyGoldenJSONWeight(const lumiMask& golden, RNode df){
    auto goldenjson = [&golden](unsigned int &run, unsigned int &luminosityBlock){ return golden.accept(run, luminosityBlock); };
    return df.Filter(goldenjson, {"run", "luminosityBlock"});
}

/*
############################################
PILEUP SFs
############################################
*/

RNode applyPileupScaleFactors(std::unordered_map<std::string, correction::CorrectionSet> cset_pileup, std::unordered_map<std::string, std::string> year_map, RNode df) {
    auto eval_correction = [cset_pileup, year_map] (std::string year, float ntrueint) {
        RVec<double> pileup_weights;
        if (cset_pileup.find(year) == cset_pileup.end()) {
            static std::unordered_set<std::string> warned_years;
            if (warned_years.find(year) == warned_years.end()) {
                std::cout << "Warning: Pileup correction set for year " << year << " not found. Setting pileup weights to 1." << std::endl;
                warned_years.insert(year);
            }
            pileup_weights.push_back(1.0);
            pileup_weights.push_back(1.0);
            pileup_weights.push_back(1.0);
            return pileup_weights;
        }
        auto correctionset = cset_pileup.at(year).at(year_map.at(year));
        pileup_weights.push_back(correctionset->evaluate({ntrueint, "nominal"}));
        pileup_weights.push_back(correctionset->evaluate({ntrueint, "up"}));
        pileup_weights.push_back(correctionset->evaluate({ntrueint, "down"}));
        return pileup_weights;
    };
    return df.Define("weightsyst_pileup", eval_correction, {"year", "Pileup_nTrueInt"});
}

/*
############################################
Lepton SFs (putting e and m together)
############################################
*/

// In weights.cpp - update the function:
RNode lepSFWrapper(RNode df,
    bool isData,
    const std::string& ele_sf_name,
    const std::string& muo_sf_name,
    bool include_trigger_sf,
    const std::string& ele_output_name,
    const std::string& muo_output_name)
{
    // Early return for data - no SFs needed
    if (isData) return df;

    std::string final_ele_sf = ele_sf_name;
    std::string final_muo_sf = muo_sf_name;

    // Optionally include trigger SFs
    if (include_trigger_sf) {
        // Apply trigger SFs if not already present
        auto colNames = df.GetColumnNames();
        bool has_ele_trigger = std::find(colNames.begin(), colNames.end(), "_weight_electrontrigger") != colNames.end();
        bool has_mu_trigger = std::find(colNames.begin(), colNames.end(), "_weight_muon_trigger") != colNames.end();
        
        if (!has_ele_trigger) {
            df = applyElectronTriggerScaleFactors(electronTriggerScaleFactors, electronTriggerScaleFactors_yearmap, df);
        }
        if (!has_mu_trigger) {
            df= applyMuonScaleFactors(muonScaleFactors, "_weight_muon_trigger", muonSFConfigs.at("_weight_muon_trigger"), df);
        }
        
        // Multiply base SFs by trigger SFs
        auto multiply_sf = [](const RVec<double>& base_sf, const RVec<double>& trig_sf) {
            return RVec<double>{ base_sf[0]*trig_sf[0], base_sf[1]*trig_sf[1], base_sf[2]*trig_sf[2] };
        };
        df = df.Define("_" + ele_output_name + "_ele_with_trigger", multiply_sf, {ele_sf_name, "_weight_electrontrigger"});
        df = df.Define("_" + muo_output_name + "_muo_with_trigger", multiply_sf, {muo_sf_name, "_weight_muon_trigger"});

        final_ele_sf = "_" + ele_output_name + "_ele_with_trigger";
        final_muo_sf = "_" + muo_output_name + "_muo_with_trigger";
    }

    // Create the separate electron and muon SF outputs with custom names
    df = df.Define(ele_output_name, final_ele_sf);
    df = df.Define(muo_output_name, final_muo_sf);

    // Optionally update main weight
    auto update_weight = [](double current_weight, const RVec<double>& ele_sf, const RVec<double>& muo_sf) {
        return current_weight * ele_sf[0] * muo_sf[0];
    };
    df = df.Redefine("weight", update_weight, {"weight", final_ele_sf, final_muo_sf});

    return df;
}

/*
############################################
MUON SFs
############################################
*/

RNode applyMuonScaleFactors(
    std::unordered_map<std::string, MuonCorrectionSet> cset_muon,
    std::string output_name,
    MuonSFConfig config,
    RNode df)
{
    auto eval_correction = [cset_muon, config] (std::string year, const RVec<float> eta, const RVec<float> pt) {
        RVec<double> muon_sf_weights = {1., 1., 1.};
        if (eta.empty()) {
            return muon_sf_weights;
        }
        if (cset_muon.find(year) == cset_muon.end()) {
            static std::unordered_set<std::string> warned_years;
            if (warned_years.find(year) == warned_years.end()) {
                std::cout << "Warning: Muon SF correction set for year " << year << " not found. Setting weights to 1." << std::endl;
                warned_years.insert(year);
            }
            return muon_sf_weights;
        }
        if (config.year_map.find(year) == config.year_map.end()) {
            return muon_sf_weights;
        }

        const auto& entry = cset_muon.at(year);
        const auto& year_config = config.year_map.at(year);
        auto correctionset = entry.cset.at(year_config.correction_key);

        for (size_t i = 0; i < eta.size(); i++) {
            float eta_to_pass = entry.abs_eta ? abs(eta[i]) : eta[i];
            float pt_to_pass = std::max(pt[i], year_config.pt_min);

            muon_sf_weights[0] *= correctionset->evaluate({eta_to_pass, pt_to_pass, "nominal"});
            muon_sf_weights[1] *= correctionset->evaluate({eta_to_pass, pt_to_pass, "systup"});
            muon_sf_weights[2] *= correctionset->evaluate({eta_to_pass, pt_to_pass, "systdown"});
        }
        return muon_sf_weights;
    };

    return df.Define(output_name, eval_correction, {"year", "_muonSel_eta", "_muonSel_pt"});
}

RNode combineScaleFactorWeightsByKey(RNode df, std::string output_name, std::vector<std::string> input_keys)
{
    auto combine = [](const RVec<double>& w0,
                      const RVec<double>& w1,
                      const RVec<double>& w2) {
        return RVec<double>{
            w0[0] * w1[0] * w2[0],
            w0[1] * w1[1] * w2[1],
            w0[2] * w1[2] * w2[2]
        };
    };

    return df.Define(output_name, combine, input_keys);
}


RNode applyMuonWorkingPointSFs(RNode df, bool isData, std::vector<std::string> wp_keys)
{
    if (isData) return df;

    std::unordered_set<std::string> component_keys;

    for (const auto& wp_key : wp_keys) {
        if (muonWorkingPointSFs.find(wp_key) == muonWorkingPointSFs.end()) {
            throw std::runtime_error("applyMuonWorkingPointSFs: unknown WP key '" + wp_key + "'");
        }
        for (const auto& component_key : muonWorkingPointSFs.at(wp_key)) {
            component_keys.insert(component_key);
        }
    }

    for (const auto& component_key : component_keys) {
        if (muonSFConfigs.find(component_key) == muonSFConfigs.end()) {
            throw std::runtime_error("applyMuonWorkingPointSFs: unknown component key '" + component_key + "'");
        }
        df = applyMuonScaleFactors(muonScaleFactors, component_key, muonSFConfigs.at(component_key), df);
    }

    for (const auto& wp_key : wp_keys) {
        df = combineScaleFactorWeightsByKey(df, wp_key, muonWorkingPointSFs.at(wp_key));
    }

    return df;
}


/*
############################################
ELECTRON SFs
############################################
*/

RNode applyElectronRecoScaleFactors(std::unordered_map<std::string, correction::CorrectionSet> cset_electron, RNode df, std::string output_name) {
    auto eval_correction = [cset_electron] (std::string year, const RVec<float> eta, const RVec<float> pt) {
        RVec<double> electron_sf_weights = {1., 1., 1.};
        if (eta.empty()) {
            return electron_sf_weights;
        }
        if (cset_electron.find(year) == cset_electron.end()) {
            static std::unordered_set<std::string> warned_years;
            if (warned_years.find(year) == warned_years.end()) {
                std::cout << "Warning: Electron Reco correction set for year " << year << " not found. Setting electron reco weights to 1." << std::endl;
                warned_years.insert(year);
            }
            return electron_sf_weights;
        }

        bool is_run2 = (year.find("2016") != std::string::npos ||
                        year.find("2017") != std::string::npos ||
                        year.find("2018") != std::string::npos);

        std::string correction_name = is_run2 ? "UL-Electron-ID-SF" : "Electron-ID-SF";
        auto correctionset = cset_electron.at(year).at(correction_name);

        for (size_t i = 0; i < eta.size(); i++) {
            if (is_run2) {
                if (pt[i] >= 20) {
                    electron_sf_weights[0] *= correctionset->evaluate({year, "sf", "RecoAbove20", eta[i], pt[i]});
                    electron_sf_weights[1] *= correctionset->evaluate({year, "sfup", "RecoAbove20", eta[i], pt[i]});
                    electron_sf_weights[2] *= correctionset->evaluate({year, "sfdown", "RecoAbove20", eta[i], pt[i]});
                } else {
                    electron_sf_weights[0] *= correctionset->evaluate({year, "sf", "RecoBelow20", eta[i], pt[i]});
                    electron_sf_weights[1] *= correctionset->evaluate({year, "sfup", "RecoBelow20", eta[i], pt[i]});
                    electron_sf_weights[2] *= correctionset->evaluate({year, "sfdown", "RecoBelow20", eta[i], pt[i]});
                }
            } else {
                if (pt[i] >= 20 && pt[i] < 75) {
                    electron_sf_weights[0] *= correctionset->evaluate({year, "sf", "Reco20to75", eta[i], pt[i]});
                    electron_sf_weights[1] *= correctionset->evaluate({year, "sfup", "Reco20to75", eta[i], pt[i]});
                    electron_sf_weights[2] *= correctionset->evaluate({year, "sfdown", "Reco20to75", eta[i], pt[i]});
                } else if (pt[i] >= 75) {
                    electron_sf_weights[0] *= correctionset->evaluate({year, "sf", "RecoAbove75", eta[i], pt[i]});
                    electron_sf_weights[1] *= correctionset->evaluate({year, "sfup", "RecoAbove75", eta[i], pt[i]});
                    electron_sf_weights[2] *= correctionset->evaluate({year, "sfdown", "RecoAbove75", eta[i], pt[i]});
                } else {
                    electron_sf_weights[0] *= correctionset->evaluate({year, "sf", "RecoBelow20", eta[i], pt[i]});
                    electron_sf_weights[1] *= correctionset->evaluate({year, "sfup", "RecoBelow20", eta[i], pt[i]});
                    electron_sf_weights[2] *= correctionset->evaluate({year, "sfdown", "RecoBelow20", eta[i], pt[i]});
                }
            }
        }
        return electron_sf_weights;
    };
    return df.Define(output_name, eval_correction, {"year", "_electronSel_SC_eta", "_electronSel_pt"});
}

RNode applyElectronIDScaleFactors(std::unordered_map<std::string, correction::CorrectionSet> cset_electron, ElectronIDConfig config, std::string output_name, RNode df) {
    auto eval_correction = [cset_electron, config] (std::string year, const RVec<float> eta, const RVec<float> pt) {
        RVec<double> electron_sf_weights = {1., 1., 1.};
        if (eta.empty()) {
            return electron_sf_weights;
        }
        if (cset_electron.find(year) == cset_electron.end()) {
            static std::unordered_set<std::string> warned_years;
            if (warned_years.find(year) == warned_years.end()) {
                std::cout << "Warning: Electron ID correction set for year " << year << " not found. Setting electron ID weights to 1." << std::endl;
                warned_years.insert(year);
            }
            return electron_sf_weights;
        }
        if (config.correction_name_map.find(year) == config.correction_name_map.end()) {
            return electron_sf_weights;
        }

        auto correctionset = cset_electron.at(year).at(config.correction_name_map.at(year));
        for (size_t i = 0; i < eta.size(); i++) {
            electron_sf_weights[0] *= correctionset->evaluate({year, "sf", config.working_point, eta[i], pt[i]});
            electron_sf_weights[1] *= correctionset->evaluate({year, "sfup", config.working_point, eta[i], pt[i]});
            electron_sf_weights[2] *= correctionset->evaluate({year, "sfdown", config.working_point, eta[i], pt[i]});
        }
        return electron_sf_weights;
    };
    return df.Define(output_name, eval_correction, {"year", "_electronSel_SC_eta", "_electronSel_pt"});
}

RNode combineElectronScaleFactorWeightsByKey(RNode df, std::string output_name, std::vector<std::string> input_keys)
{
    auto combine = [](const RVec<double>& w0,
                      const RVec<double>& w1) {
        return RVec<double>{
            w0[0] * w1[0],
            w0[1] * w1[1],
            w0[2] * w1[2]
        };
    };

    return df.Define(output_name, combine, input_keys);
}

RNode applyElectronWorkingPointSFs(RNode df, bool isData, std::vector<std::string> wp_keys)
{
    if (isData) return df;

    bool need_reco = false;
    bool need_id_loose = false;
    bool need_id_tight = false;

    for (const auto& wp_key : wp_keys) {
        if (wp_key == "_weight_electron_reco_looseid") {
            need_reco = true;
            need_id_loose = true;
        }
        else if (wp_key == "_weight_electron_reco_tightid") {
            need_reco = true;
            need_id_tight = true;
        }
        else {
            throw std::runtime_error("applyElectronWorkingPointSFs: unknown WP key '" + wp_key + "'");
        }
    }

    if (need_reco) {
        df = applyElectronRecoScaleFactors(electronScaleFactors, df, "_weight_electron_reco");
    }
    if (need_id_loose) {
        df = applyElectronIDScaleFactors(electronScaleFactors, electronID_loose, "_weight_electron_id_loose", df);
    }
    if (need_id_tight) {
        df = applyElectronIDScaleFactors(electronScaleFactors, electronID_tight, "_weight_electron_id_tight", df);
    }

    for (const auto& wp_key : wp_keys) {
        df = combineElectronScaleFactorWeightsByKey(df, wp_key, electronWorkingPointSFs.at(wp_key));
    }

    return df;
}

/*
############################################
ELECTRON TRIGGER SFs
############################################
*/

RNode applyElectronTriggerScaleFactors(std::unordered_map<std::string, correction::CorrectionSet> cset_electron, std::unordered_map<std::string, std::string> year_map, RNode df) {
    auto eval_correction = [cset_electron, year_map] (std::string year, const RVec<float> eta, const RVec<float> pt) {
        RVec<double> electron_sf_weights = {1., 1., 1.};
        if (eta.empty()) {
            return electron_sf_weights;
        }
        if (cset_electron.find(year) == cset_electron.end()) {
            static std::unordered_set<std::string> warned_years;
            if (warned_years.find(year) == warned_years.end()) {
                std::cout << "Warning: Electron Trigger correction set for year " << year << " not found. Setting electron trigger weights to 1." << std::endl;
                warned_years.insert(year);
            }
            return electron_sf_weights;
        }
        auto correctionset = cset_electron.at(year).at(year_map.at(year));
        for (size_t i = 0; i < eta.size(); i++) {
            electron_sf_weights[0] *= correctionset->evaluate({year, "sf", "HLT_SF_Ele30_TightID", eta[i], pt[i]});
            electron_sf_weights[1] *= correctionset->evaluate({year, "sfup", "HLT_SF_Ele30_TightID", eta[i], pt[i]});
            electron_sf_weights[2] *= correctionset->evaluate({year, "sfdown", "HLT_SF_Ele30_TightID", eta[i], pt[i]});
        }
        return electron_sf_weights;
    };
    return df.Define("_weight_electrontrigger", eval_correction, {"year", "electron_SC_eta", "electron_pt"});
}

/*
############################################
BTAG SFs
############################################
*/

RNode applyBTaggingScaleFactors(std::unordered_map<std::string, correction::CorrectionSet> cset_btag, 
                                 std::unordered_map<std::string, std::string> corrname_map_HF,
                                 std::unordered_map<std::string, std::string> corrname_map_LF,
                                 RNode df) {
    
    auto calc_btag_sf = [cset_btag] (const std::string& year, const RVec<float>& eta, const RVec<float>& pt, 
                                     const RVec<int>& jetflavor, const std::string& correction_name, bool is_heavy_flavor) {
        RVec<double> btag_sf_weights = {1., 1., 1.};
        if (eta.empty()) {
            return btag_sf_weights;
        }

        auto cset_it = cset_btag.find(year);
        if (cset_it == cset_btag.end()) {
            static std::unordered_set<std::string> warned_years;
            if (warned_years.find(year) == warned_years.end()) {
                std::cout << "Warning: B-tagging correction set for year " << year << " not found. Setting b-tagging weights to 1." << std::endl;
                warned_years.insert(year);
            }
            return btag_sf_weights;
        }
        const auto& cset_btag_year = cset_it->second;
        
        auto cset_eff_it = cset_btag.find("eff");
        if (cset_eff_it == cset_btag.end()) {
            static bool warned = false;
            if (!warned) {
                std::cout << "Warning: B-tagging efficiency correction set not found. Setting b-tagging weights to 1." << std::endl;
                warned = true;
            }
            return btag_sf_weights;
        }
        const auto& cset_btag_eff = cset_eff_it->second;
        
        const std::string btag_year_key = "btag_" + year;

        float num = 1.;
        float num_up = 1.;
        float num_down = 1.;
        float den = 1.;

        for (size_t i = 0; i < eta.size(); i++) {
            bool process_jet = false;
            const char* flavor_label = nullptr;
            
            if (is_heavy_flavor) {
                if (jetflavor[i] == 5) {
                    process_jet = true;
                    flavor_label = "B";
                } else if (jetflavor[i] == 4) {
                    process_jet = true;
                    flavor_label = "C";
                }
            } else {
                if (jetflavor[i] == 0) {
                    process_jet = true;
                    flavor_label = "L";
                }
            }
            
            if (!process_jet) {
                continue;
            }

            const float abs_eta = std::abs(eta[i]);

            const float btag_sf_tight = cset_btag_year.at(correction_name)->evaluate({"central", "T", jetflavor[i], abs_eta, pt[i]});
            const float btag_sf_loose = cset_btag_year.at(correction_name)->evaluate({"central", "L", jetflavor[i], abs_eta, pt[i]});
            const float btag_sf_tight_up = cset_btag_year.at(correction_name)->evaluate({"up_uncorrelated", "T", jetflavor[i], abs_eta, pt[i]});
            const float btag_sf_loose_up = cset_btag_year.at(correction_name)->evaluate({"up_uncorrelated", "L", jetflavor[i], abs_eta, pt[i]});
            const float btag_sf_tight_down = cset_btag_year.at(correction_name)->evaluate({"down_uncorrelated", "T", jetflavor[i], abs_eta, pt[i]});
            const float btag_sf_loose_down = cset_btag_year.at(correction_name)->evaluate({"down_uncorrelated", "L", jetflavor[i], abs_eta, pt[i]});
            
            const float btag_eff_tight = cset_btag_eff.at(btag_year_key)->evaluate({flavor_label, "T", pt[i], eta[i]});
            const float btag_eff_loose = cset_btag_eff.at(btag_year_key)->evaluate({flavor_label, "L", pt[i], eta[i]});

            // Accumulate weights
            num *= (btag_sf_tight * btag_eff_tight) * (btag_sf_loose * btag_eff_loose - btag_sf_tight * btag_eff_tight) * (1. - btag_sf_loose * btag_eff_loose);
            num_up *= (btag_sf_tight_up * btag_eff_tight) * (btag_sf_loose_up * btag_eff_loose - btag_sf_tight_up * btag_eff_tight) * (1. - btag_sf_loose_up * btag_eff_loose);
            num_down *= (btag_sf_tight_down * btag_eff_tight) * (btag_sf_loose_down * btag_eff_loose - btag_sf_tight_down * btag_eff_tight) * (1. - btag_sf_loose_down * btag_eff_loose);
            den *= (btag_eff_tight) * (btag_eff_loose - btag_eff_tight) * (1. - btag_eff_loose);
        }

        if (den != 0.) {
            btag_sf_weights[0] = num / den;
            btag_sf_weights[1] = num_up / den;
            btag_sf_weights[2] = num_down / den;
        }

        return btag_sf_weights;
    };

    auto eval_HF = [cset_btag, corrname_map_HF, calc_btag_sf] (const std::string& year, const RVec<float>& eta, 
                                                                 const RVec<float>& pt, const RVec<int>& jetflavor) {
        auto corrname_it = corrname_map_HF.find(year);
        if (corrname_it == corrname_map_HF.end()) {
            static std::unordered_set<std::string> warned_years;
            if (warned_years.find(year) == warned_years.end()) {
                std::cout << "Warning: B-tagging HF correction name for year " << year << " not found. Setting b-tagging HF weights to 1." << std::endl;
                warned_years.insert(year);
            }
            return RVec<double>{1., 1., 1.};
        }
        return calc_btag_sf(year, eta, pt, jetflavor, corrname_it->second, true);
    };

    auto eval_LF = [cset_btag, corrname_map_LF, calc_btag_sf] (const std::string& year, const RVec<float>& eta, 
                                                                 const RVec<float>& pt, const RVec<int>& jetflavor) {
        auto corrname_it = corrname_map_LF.find(year);
        if (corrname_it == corrname_map_LF.end()) {
            static std::unordered_set<std::string> warned_years;
            if (warned_years.find(year) == warned_years.end()) {
                std::cout << "Warning: B-tagging LF correction name for year " << year << " not found. Setting b-tagging LF weights to 1." << std::endl;
                warned_years.insert(year);
            }
            return RVec<double>{1., 1., 1.};
        }
        return calc_btag_sf(year, eta, pt, jetflavor, corrname_it->second, false);
    };

    // return df.Define("weightsyst_btagging_sf_HF", eval_HF, {"year", "GnTBJet_eta", "GnTBJet_pt", "GnTBJet_hadronFlavour"})
            //  .Define("weightsyst_btagging_sf_LF", eval_LF, {"year", "GnTBJet_eta", "GnTBJet_pt", "GnTBJet_hadronFlavour"});
    return df;
}

/*
############################################
OTHER SFs
############################################
*/

// See https://github.com/cmstas/run3-vbsvvh/pull/28#issuecomment-3820814039
RNode applyEWKCorrections(correction::CorrectionSet cset_ewk, RNode df){
    auto eval_correction = [cset_ewk] (RVec<float> LHEPart_pt, RVec<float> LHEPart_eta, RVec<float> LHEPart_phi, RVec<float> LHEPart_mass, RVec<int> LHEPart_pdgId, int do_ewk_corr) {
        if(do_ewk_corr == 0) return 1.;
        else{
            TLorentzVector TEWKq1, TEWKq2, TEWKlep, TEWKnu;
            TEWKq1.SetPtEtaPhiM(LHEPart_pt[4],LHEPart_eta[4],LHEPart_phi[4],LHEPart_mass[4]);
            TEWKq2.SetPtEtaPhiM(LHEPart_pt[5],LHEPart_eta[5],LHEPart_phi[5],LHEPart_mass[5]);
            TEWKlep.SetPtEtaPhiM(LHEPart_pt[2],LHEPart_eta[2],LHEPart_phi[2],LHEPart_mass[2]);
            TEWKnu.SetPtEtaPhiM(LHEPart_pt[3],LHEPart_eta[3],LHEPart_phi[3],LHEPart_mass[3]);
            int chargequark[7] = {0,-1,2,-1,2,-1,2};
            int EWKpdgq1 = LHEPart_pdgId[4];
            int EWKpdgq2 = LHEPart_pdgId[5];
            int EWKsignq1 = (EWKpdgq1 > 0) - (EWKpdgq1 < 0);
            int EWKsignq2 = (EWKpdgq2 > 0) - (EWKpdgq2 < 0);
            double EWKMass_q12 = (TEWKq1 + TEWKq2).M();
            double EWKMass_lnu = (TEWKlep + TEWKnu).M();
            double fabscharge=(fabs((double)(EWKsignq1 * chargequark[abs(EWKpdgq1)] + (EWKsignq2 * chargequark[abs(EWKpdgq2)]))))/3;
            double EWKbjet_pt = -999;
            if(fabscharge ==1){
                if( EWKMass_q12 >= 70 && EWKMass_q12 < 90  && 
                    EWKMass_lnu >= 70 && EWKMass_lnu < 90){
                    return 0.;
                }
            }
            if(EWKMass_q12 >= 95){
                if( abs(EWKpdgq1) == 5 && abs(EWKpdgq2) == 5){
                    if(TEWKq1.Pt() > TEWKq2.Pt())  EWKbjet_pt = TEWKq1.Pt();
                    else                           EWKbjet_pt = TEWKq2.Pt();
                }else if(abs(EWKpdgq1) == 5){
                    EWKbjet_pt = TEWKq1.Pt();
                }else if(abs(EWKpdgq2) == 5){
                    EWKbjet_pt = TEWKq2.Pt();
                }
            }
            if(EWKbjet_pt > -998){
                return cset_ewk.at("EWK")->evaluate({EWKbjet_pt});
            }
            else return 1.;
        }
    };
    return df.Define("ewkweight", eval_correction, {"LHEPart_pt", "LHEPart_eta", "LHEPart_phi", "LHEPart_mass", "LHEPart_pdgId", "do_ewk_corr"});
}

RNode applyL1PreFiringReweighting(RNode df){
    // L1PreFiringWeight_* branches are only present in Run 2 NanoAOD; the
    // correction does not apply to Run 3, so emit a unit weight there.
    auto colNames = df.GetColumnNames();
    bool hasL1Prefire = std::find(colNames.begin(), colNames.end(), std::string("L1PreFiringWeight_Nom")) != colNames.end();
    if (!hasL1Prefire) {
        return df.Define("weightsyst_l1prefiring", [] () { return RVec<float>{1.f, 1.f, 1.f}; }, {});
    }
    auto eval_correction = [] (float L1prefire, float L1prefireup, float L1prefiredown) {
        return RVec<float>{L1prefire, L1prefireup, L1prefiredown};
    };
    return df.Define("weightsyst_l1prefiring", eval_correction, {"L1PreFiringWeight_Nom", "L1PreFiringWeight_Up", "L1PreFiringWeight_Dn"});
}

RNode applyPSWeight_FSR(RNode df) {
    auto eval_correction = [] (const RVec<float> PSWeight) {
        return RVec<float>{1., PSWeight[1], PSWeight[3]};
    };
    return df.Define("weightsyst_PSFSR", eval_correction, {"PSWeight"});
}

RNode applyPSWeight_ISR(RNode df) {
    auto eval_correction = [] (const RVec<float> PSWeight) {
        return RVec<float>{1., PSWeight[0], PSWeight[2]};
    };
    return df.Define("weightsyst_PSISR", eval_correction, {"PSWeight"});
}

RNode applyLHEScaleWeight_muF(RNode df) {
    auto eval_correction = [] (const RVec<float> LHEScaleWeight) {
        return RVec<float>{1., LHEScaleWeight[5], LHEScaleWeight[3]};
    };
    return df.Define("weightsyst_muF", eval_correction, {"LHEScaleWeight"});
}

RNode applyLHEScaleWeight_muR(RNode df) {
    auto eval_correction = [] (const RVec<float> LHEScaleWeight) {
        return RVec<float>{1., LHEScaleWeight[7], LHEScaleWeight[1]};
    };
    return df.Define("weightsyst_muR", eval_correction, {"LHEScaleWeight"});
}

RNode applyDataWeights(RNode df_) {
    return applyGoldenJSONWeight(LumiMask, df_);
}

RNode applyMCWeights(RNode df_) {
    // Check for LHE branches (not present in all samples, e.g. QCD)
    auto colNames = df_.GetColumnNames();
    auto hasColumn = [&colNames](const std::string& name) {
        return std::find(colNames.begin(), colNames.end(), name) != colNames.end();
    };
    bool hasLHEScale = hasColumn("LHEScaleWeight");
    bool hasLHEPart = hasColumn("LHEPart_pt");

    auto df = applyPileupScaleFactors(pileupScaleFactors, pileupScaleFactors_yearmap, df_);

    df = applyBTaggingScaleFactors(bTaggingScaleFactors, bTaggingScaleFactors_HF_corrname, bTaggingScaleFactors_LF_corrname,  df);

    if (hasLHEPart) {
        df = applyEWKCorrections(cset_ewk, df);
    } else {
        df = df.Define("ewkweight", [] () { return 1.; }, {});
    }

    df = applyL1PreFiringReweighting(df);
    df = applyPSWeight_FSR(df);
    df = applyPSWeight_ISR(df);

    if (hasLHEScale) {
        df = applyLHEScaleWeight_muF(df);
        df = applyLHEScaleWeight_muR(df);
    } else {
        df = df.Define("weightsyst_muF", [] () { return RVec<float>{1.f, 1.f, 1.f}; }, {});
        df = df.Define("weightsyst_muR", [] () { return RVec<float>{1.f, 1.f, 1.f}; }, {});
    }

    return df.Redefine("weight",
        "weight *"
        "weightsyst_pileup[0] * "
        // "weightsyst_btagging_sf_HF[0] * "
        // "weightsyst_btagging_sf_LF[0] * "
        "ewkweight * "
        "weightsyst_l1prefiring[0] * "
        "weightsyst_PSISR[0] * "
        "weightsyst_PSFSR[0] * "
        "weightsyst_muF[0] * "
        "weightsyst_muR[0]");
}
