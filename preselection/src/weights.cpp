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
MUON SFs
############################################
*/

RNode applyMuonIDScaleFactors(std::unordered_map<std::string, correction::CorrectionSet> cset_muon, std::unordered_map<std::string, std::string> year_map, RNode df) {
    auto eval_correction = [cset_muon, year_map] (std::string year, const RVec<float> eta, const RVec<float> pt) {
        RVec<double> muon_sf_weights = {1., 1., 1.};
        if (eta.empty()) {
            return muon_sf_weights;
        }
        if (cset_muon.find(year) == cset_muon.end()) {
            static std::unordered_set<std::string> warned_years;
            if (warned_years.find(year) == warned_years.end()) {
                std::cout << "Warning: Muon ID correction set for year " << year << " not found. Setting muon ID weights to 1." << std::endl;
                warned_years.insert(year);
            }
            return muon_sf_weights;
        }
        auto correctionset = cset_muon.at(year).at(year_map.at(year));
        for (size_t i = 0; i < eta.size(); i++) {
            float pt_min = 15.1;
            float pt_to_pass = std::max(pt[i],pt_min);
            muon_sf_weights[0] *= correctionset->evaluate({abs(eta[i]), pt_to_pass, "nominal"});
            muon_sf_weights[1] *= correctionset->evaluate({abs(eta[i]), pt_to_pass, "systup"});
            muon_sf_weights[2] *= correctionset->evaluate({abs(eta[i]), pt_to_pass, "systdown"});
        }
        return muon_sf_weights;
    };
    return df.Define("weightsyst_muonid", eval_correction, {"year", "muon_eta", "muon_pt"});
}

RNode applyMuonRecoScaleFactors(std::unordered_map<std::string, correction::CorrectionSet> cset_muon, std::unordered_map<std::string, std::string> year_map, RNode df) {
    auto eval_correction = [cset_muon, year_map] (std::string year, const RVec<float> eta, const RVec<float> pt) {
        RVec<double> muon_sf_weights = {1., 1., 1.};
        if (eta.empty()) {
            return muon_sf_weights;
        }
        if (cset_muon.find(year) == cset_muon.end()) {
            static std::unordered_set<std::string> warned_years;
            if (warned_years.find(year) == warned_years.end()) {
                std::cout << "Warning: Muon Reco correction set for year " << year << " not found. Setting muon reco weights to 1." << std::endl;
                warned_years.insert(year);
            }
            return muon_sf_weights;
        }
        auto correctionset = cset_muon.at(year).at(year_map.at(year));
        for (size_t i = 0; i < eta.size(); i++) {
            float pt_max = 15.1;
            float pt_to_pass = std::max(pt[i],pt_max);
            muon_sf_weights[0] *= correctionset->evaluate({abs(eta[i]), pt_to_pass, "nominal"});
            muon_sf_weights[1] *= correctionset->evaluate({abs(eta[i]), pt_to_pass, "systup"});
            muon_sf_weights[2] *= correctionset->evaluate({abs(eta[i]), pt_to_pass, "systdown"});
        }
        return muon_sf_weights;
    };
    return df.Define("weightsyst_muonreco", eval_correction, {"year", "muon_eta", "muon_pt"});
}

RNode applyMuonTriggerScaleFactors(std::unordered_map<std::string, correction::CorrectionSet> cset_muon, std::unordered_map<std::string, std::string> year_map, RNode df) {
    auto eval_correction = [cset_muon, year_map] (std::string year, const RVec<float> eta, const RVec<float> pt) {
        RVec<double> muon_sf_weights = {1., 1., 1.};
        if (eta.empty()) {
            return muon_sf_weights;
        }
        if (cset_muon.find(year) == cset_muon.end()) {
            static std::unordered_set<std::string> warned_years;
            if (warned_years.find(year) == warned_years.end()) {
                std::cout << "Warning: Muon Trigger correction set for year " << year << " not found. Setting muon trigger weights to 1." << std::endl;
                warned_years.insert(year);
            }
            return muon_sf_weights;
        }
        auto correctionset = cset_muon.at(year).at(year_map.at(year));
        for (size_t i = 0; i < eta.size(); i++) {
            float pt_min = 29.1;
            float pt_to_pass = std::max(pt[i],pt_min);
            muon_sf_weights[0] *= correctionset->evaluate({abs(eta[i]), pt_to_pass, "nominal"});
            muon_sf_weights[1] *= correctionset->evaluate({abs(eta[i]), pt_to_pass, "systup"});
            muon_sf_weights[2] *= correctionset->evaluate({abs(eta[i]), pt_to_pass, "systdown"});
        }
        return muon_sf_weights;
    };
    return df.Define("weightsyst_muontrigger", eval_correction, {"year", "muon_eta", "muon_pt"});
}

/*
############################################
ELECTRON SFs
############################################
*/

RNode applyElectronIDScaleFactors(std::unordered_map<std::string, correction::CorrectionSet> cset_electron, std::unordered_map<std::string, std::string> year_map, RNode df) {
    auto eval_correction = [cset_electron, year_map] (std::string year, const RVec<float> eta, const RVec<float> pt) {
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
        auto correctionset = cset_electron.at(year).at(year_map.at(year));
        for (size_t i = 0; i < eta.size(); i++) {
            electron_sf_weights[0] *= correctionset->evaluate({year, "sf", "Tight", eta[i], pt[i]});
            electron_sf_weights[1] *= correctionset->evaluate({year, "sfup", "Tight", eta[i], pt[i]});
            electron_sf_weights[2] *= correctionset->evaluate({year, "sfdown", "Tight", eta[i], pt[i]});
        }
        return electron_sf_weights;
    };
    return df.Define("weightsyst_electronid", eval_correction, {"year", "electron_SC_eta", "electron_pt"});
}

RNode applyElectronRecoScaleFactors(std::unordered_map<std::string, correction::CorrectionSet> cset_electron, std::unordered_map<std::string, std::string> year_map, RNode df) {
    auto eval_correction = [cset_electron, year_map] (std::string year, const RVec<float> eta, const RVec<float> pt) {
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
        auto correctionset = cset_electron.at(year).at(year_map.at(year));

        // Simple way to check if the year refers to Run 2
        bool is_run2 = (year.find("2016") != std::string::npos ||
                        year.find("2017") != std::string::npos ||
                        year.find("2018") != std::string::npos);

        for (size_t i = 0; i < eta.size(); i++) {
            if (is_run2) {
                // Run 2 Scale Factors
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
                // Run 3 Scale Factors
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
    return df.Define("weightsyst_electronreco", eval_correction, {"year", "electron_SC_eta", "electron_pt"});
}

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
    return df.Define("weightsyst_electrontrigger", eval_correction, {"year", "electron_SC_eta", "electron_pt"});
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
    df = applyMuonIDScaleFactors(muonScaleFactors, muonIDScaleFactors_yearmap, df);
    df = applyMuonRecoScaleFactors(muonScaleFactors, muonRecoScaleFactors_yearmap, df);
    df = applyMuonTriggerScaleFactors(muonScaleFactors, muonTriggerScaleFactors_yearmap, df);

    df = applyElectronIDScaleFactors(electronScaleFactors, electronScaleFactors_yearmap, df);
    df = applyElectronRecoScaleFactors(electronScaleFactors, electronScaleFactors_yearmap, df);
    df = applyElectronTriggerScaleFactors(electronTriggerScaleFactors, electronTriggerScaleFactors_yearmap, df);

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
        "weightsyst_muonid[0] * "
        "weightsyst_muonreco[0] * "
        "weightsyst_muontrigger[0] * "
        "weightsyst_electronid[0] * "
        "weightsyst_electronreco[0] * "
        "weightsyst_electrontrigger[0] * "
        // "weightsyst_btagging_sf_HF[0] * "
        // "weightsyst_btagging_sf_LF[0] * "
        "ewkweight * "
        "weightsyst_l1prefiring[0] * "
        "weightsyst_PSISR[0] * "
        "weightsyst_PSFSR[0] * "
        "weightsyst_muF[0] * "
        "weightsyst_muR[0]");
}
