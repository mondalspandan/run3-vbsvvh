# Note the keys of each dict should correspond to a key in the SKIM_PATH_DICT

xsec_dict = {

    ### Run 3 xsec numbers ###
    "run3" : {

        "data" : {
        },

        # Sig 4f
        "sig": {
            "VBSWWH_OS_c2v1p0_c3_1p0": 7.233e-04,
            "VBSWWH_SS_c2v1p0_c3_1p0": 3.590e-04,
            "VBSWZH_c2v1p0_c3_1p0"   : 4.740e-04,
            "VBSZZH_c2v1p0_c3_1p0"   : 1.250e-04,

            "VBSWWH_OS_c2v1p5_c3_1p0": 1.277e-03,
            "VBSWWH_SS_c2v1p5_c3_1p0": 7.359e-04,
            "VBSWZH_c2v1p5_c3_1p0"   : 8.252e-04,
            "VBSZZH_c2v1p5_c3_1p0"   : 4.378e-04,

            "VBSWWH_OS_c2v1p0_c3_10p0": 1.789e-03,
            "VBSWWH_SS_c2v1p0_c3_10p0": 5.075e-04,
            "VBSWZH_c2v1p0_c3_10p0"   : 7.107e-04,
            "VBSZZH_c2v1p0_c3_10p0"   : 4.690e-04,
        },

        "bkg" : {

            # From XSDB

            "DYto2E_Bin-MLL-10to50_TuneCP5_13p6TeV": 6744.0,
            "DYto2Mu_Bin-MLL-10to50_TuneCP5_13p6TeV": 6744.0,
            "DYto2Tau_Bin-MLL-10to50_TuneCP5_13p6TeV": 6744.0,

            "DYto2Mu-2Jets_Bin-MLL-50_TuneCP5_13p6TeV": 2240.0,
            "DYto2E-2Jets_Bin-MLL-50_TuneCP5_13p6TeV": 2244.0,
            "DYto2Tau-2Jets_Bin-MLL-50_TuneCP5_13p6TeV": 2219.0,

            # new xsec values from HZZ, multiplied by 1.7 (original values in comments)
            # https://github.com/CJLST/ZZAnalysis/blob/Run3/NanoAnalysis/test/prod/samplesNano_2024_MC.csv#L45
            "GluGluToContinto2Zto2E2Mu_TuneCP5_13p6TeV": 0.01061067, # 0.00624157 from HZZ * 1.7
            "GluGlutoContinto2Zto4E_TuneCP5_13p6TeV": 0.00516078, # 0.00303575 from HZZ * 1.7
            "GluGlutoContinto2Zto4Mu_TuneCP5_13p6TeV": 0.00516078, # 0.00303575 from HZZ * 1.7
            "GluGlutoContinto2Zto4Tau_TuneCP5_13p6TeV": 0.00516078, # 0.00303575 from HZZ * 1.7
            "GluGluToContinto2Zto2E2Tau_TuneCP5_13p6TeV": 0.01061067, # 0.00624157 from HZZ * 1.7
            "GluGluToContinto2Zto2Mu2Tau_TuneCP5_13p6TeV": 0.01061067, # 0.00624157 from HZZ * 1.7
            
            # QCD-HT (obtained by Cristina manually with genXsecAnalyzer) - Cristina Mantilla Suarez at Virginia (see comment from Lara in issue #45)
            "QCD-4Jets_Bin-HT-40to70_TuneCP5_13p6TeV": 311600000.0,
            "QCD-4Jets_Bin-HT-70to100_TuneCP5_13p6TeV": 58520000.0,
            "QCD-4Jets_Bin-HT-100to200_TuneCP5_13p6TeV": 25220000.0,
            "QCD-4Jets_Bin-HT-200to400_TuneCP5_13p6TeV": 1963000.0,
            "QCD-4Jets_Bin-HT-400to600_TuneCP5_13p6TeV": 94870.0,
            "QCD-4Jets_Bin-HT-600to800_TuneCP5_13p6TeV": 13420.0,
            "QCD-4Jets_Bin-HT-800to1000_TuneCP5_13p6TeV": 2992.0,
            "QCD-4Jets_Bin-HT-1000to1200_TuneCP5_13p6TeV": 879.1,
            "QCD-4Jets_Bin-HT-1200to1500_TuneCP5_13p6TeV": 384.5,
            "QCD-4Jets_Bin-HT-1500to2000_TuneCP5_13p6TeV": 125.5,
            "QCD-4Jets_Bin-HT-2000_TuneCP5_13p6TeV": 25.78,

            "QCD_Bin-PT-50to80_TuneCP5_13p6TeV": 16730000.0,
            "QCD_Bin-PT-80to120_TuneCP5_13p6TeV": 2506000.0,
            "QCD_Bin-PT-120to170_TuneCP5_13p6TeV": 439800.0,
            "QCD_Bin-PT-170to300_TuneCP5_13p6TeV": 113300.0,
            "QCD_Bin-PT-300to470_TuneCP5_13p6TeV": 7581.0,
            "QCD_Bin-PT-470to600_TuneCP5_13p6TeV": 623.3,
            "QCD_Bin-PT-600to800_TuneCP5_13p6TeV": 178.7,
            "QCD_Bin-PT-800to1000_TuneCP5_13p6TeV": 30.62,
            "QCD_Bin-PT-1000to1500_TuneCP5_13p6TeV": 9.306,
            "QCD_Bin-PT-1500to2000_TuneCP5_13p6TeV": 0.5015,
            "QCD_Bin-PT-2000to2500_TuneCP5_13p6TeV": 0.04264,
            "QCD_Bin-PT-2500to3000_TuneCP5_13p6TeV": 0.004454,
            "QCD_Bin-PT-3000_TuneCP5_13p6TeV": 0.0005539,

            # see Lara's comment on issue #45
            # (https://twiki.cern.ch/twiki/bin/view/LHCPhysics/SingleTopNNLORef#Single_top_quark_t_channel_cross)
            "TbarBto2Q-s-channel_TuneCP5_13p6TeV": 3.057, #4.534*(1-3*0.108535)
            "TbarBtoLNu-s-channel_TuneCP5_13p6TeV": 1.476, #4.534*3*0.108535
            "TbarBtoLminusNuB-s-channel-4FS_TuneCP5_13p6TeV": 1.476, #4.534*3*0.108535
            
            "TBbarto2Q-s-channel_TuneCP5_13p6TeV": 4.8853, # 7.244*(1-3*0.108535)
            "TBbartoLNu-s-channel_TuneCP5_13p6TeV" : 2.359, # 7.244*3*0.108535
            "TBbartoLplusNuBbar-s-channel-4FS_TuneCP5_13p6TeV": 2.359, # 7.244*3*0.108535

            "TbarBQtoLNu-t-channel-4FS_TuneCP5_13p6TeV": 28.392, # 87.2*3*0.108535
            "TbarBQto2Q-t-channel-4FS_TuneCP5_13p6TeV": 58.807, # 87.2*(1-3*0.108535)
            
            "TBbarQto2Q-t-channel-4FS_TuneCP5_13p6TeV": 97.7872,  # 145*(1-3*0.108535)
            "TBbarQtoLNu-t-channel-4FS_TuneCP5_13p6TeV": 47.2127, # 145*3*0.108535


            # see Lara's commend on issue #45
            # inclusive xsec tW = 87.9 (https://twiki.cern.ch/twiki/bin/view/LHCPhysics/SingleTopNNLORef#Single_top_quark_tW_channel_cros)
            "TbarWplusto2L2Nu_TuneCP5_13p6TeV": 4.6595, # 87.9*0.5*(3*0.108535)*(3*0.108535)
            "TbarWplusto4Q_TuneCP5_13p6TeV": 19.9888, # 87.9*0.5*(1-3*0.108535)*(1-3*0.108535)
            "TbarWplustoLNu2Q_TuneCP5_13p6TeV": 19.3016, # 87.9*0.5*(3*0.108535)*(1-3*0.108535)*2

            "TWminusto2L2Nu_TuneCP5_13p6TeV" : 4.6595, # 87.9*0.5*(3*0.108535)*(3*0.108535)
            "TWminusto4Q_TuneCP5_13p6TeV" : 19.9888, # 87.9*0.5*(1-3*0.108535)*(1-3*0.108535)
            "TWminustoLNu2Q_TuneCP5_13p6TeV" : 19.3016, # 87.9*0.5*(3*0.108535)*(1-3*0.108535)*2
          
            #"TTBBto2L2Nu_TuneCP5_13p6TeV" : , # No xsdb number
            #"TTBBto4Q_TuneCP5_13p6TeV" : , # No xsdb number
            #"TTBBtoLNu2Q_TuneCP5_13p6TeV" : , # No xsdb number
            "TTLL_Bin-MLL-4to50_TuneCP5_13p6TeV" : 0.03949,
            "TTLL_Bin-MLL-50_TuneCP5_13p6TeV" : 0.08646,
            "TTLNu-1Jets_TuneCP5_13p6TeV" : 0.2505,

            # See Lara's comment on issue #45 (https://twiki.cern.ch/twiki/bin/view/LHCPhysics/TtbarNNLO)
            "TTto2L2Nu_TuneCP5_13p6TeV" : 97.9188, # 923.6*(3*0.108535)*(3*0.108535)
            "TTto4Q_TuneCP5_13p6TeV"    : 420.0612, # 923.6*(1-3*0.108535)*(1-3*0.108535)
            "TTtoLNu2Q_TuneCP5_13p6TeV" : 405.6199, # 923.6*(3*0.108535)*(1-3*0.108535)*2 
            
            "TTW-WtoQQ-1Jets_TuneCP5_13p6TeV" : 0.4678,
            "TTWW_TuneCP5_13p6TeV" : 0.008203, # XSDB also lists 0.008191
            "TTWZ_TuneCP5_13p6TeV" : 0.002715,
            "TZQB-Zto2L-4FS_Bin-MLL-30_TuneCP5_13p6TeV" : 0.07968,
            "VBS-SSWW-LL_TuneCP5_13p6TeV" : 0.002179,
            "VBS-SSWW-TL_TuneCP5_13p6TeV" : 0.01151,
            #"VBS-SSWW-TT_TuneCP5_13p6TeV" : , # No xsdb number

            "Wto2Q-3Jets_Bin-HT-100to400_TuneCP5_13p6TeV" : 16120.0,
            "Wto2Q-3Jets_Bin-HT-1500to2500_TuneCP5_13p6TeV" : 1.825,
            "Wto2Q-3Jets_Bin-HT-2500_TuneCP5_13p6TeV" : 0.1158,
            "Wto2Q-3Jets_Bin-HT-400to800_TuneCP5_13p6TeV" : 356.9,
            "Wto2Q-3Jets_Bin-HT-800to1500_TuneCP5_13p6TeV" : 29.52,

            "WtoLNu-2Jets_Bin-1J-PTLNu-100to200_TuneCP5_13p6TeV" : 342.3,
            "WtoLNu-2Jets_Bin-1J-PTLNu-200to400_TuneCP5_13p6TeV" : 21.84,
            "WtoLNu-2Jets_Bin-1J-PTLNu-400to600_TuneCP5_13p6TeV" : 0.6845,
            "WtoLNu-2Jets_Bin-1J-PTLNu-40to100_TuneCP5_13p6TeV" : 4211.0,
            "WtoLNu-2Jets_Bin-1J-PTLNu-600_TuneCP5_13p6TeV" : 0.07753,
            "WtoLNu-2Jets_Bin-2J-PTLNu-100to200_TuneCP5_13p6TeV" : 411.1,
            "WtoLNu-2Jets_Bin-2J-PTLNu-200to400_TuneCP5_13p6TeV" : 53.59,
            "WtoLNu-2Jets_Bin-2J-PTLNu-400to600_TuneCP5_13p6TeV" : 3.099,
            "WtoLNu-2Jets_Bin-2J-PTLNu-40to100_TuneCP5_13p6TeV" : 1581.0,
            "WtoLNu-2Jets_Bin-2J-PTLNu-600_TuneCP5_13p6TeV" : 0.5259,
            "WtoLNu-4Jets_Bin-1J_TuneCP5_13p6TeV" : 9141.0,
            "WtoLNu-4Jets_Bin-2J_TuneCP5_13p6TeV" : 2931.0,
            "WtoLNu-4Jets_Bin-3J_TuneCP5_13p6TeV" : 864.6,
            "WtoLNu-4Jets_Bin-4J_TuneCP5_13p6TeV" : 417.8,
            "WWJJto2L2Nu-OS-noTop-EWK_TuneCP5_13p6TeV" : 0.3304,
            "WWJJto2L2Nu-SS-noTop-EWK_TuneCP5_13p6TeV" : 0.02955,
            "WWto2L2Nu_TuneCP5_13p6TeV" : 11.79,
            "WWto4Q_TuneCP5_13p6TeV" : 50.79,
            "WWtoLNu2Q_TuneCP5_13p6TeV" : 48.94,
            "WW_TuneCP5_13p6TeV" : 80.42,
            "WWW-4F_TuneCP5_13p6TeV" : 0.2328,
            "WWZ-4F_TuneCP5_13p6TeV" : 0.1851,
            "WZto2L2Q_TuneCP5_13p6TeV" : 7.568,
            "WZto3LNu_TuneCP5_13p6TeV" : 4.924,
            "WZtoL3Nu_TuneCP5_13p6TeV" : 3.077,
            "WZtoLNu2Q_TuneCP5_13p6TeV" : 15.87,
            "WZ_TuneCP5_13p6TeV" : 29.1,
            "WZZ-5F_TuneCP5_13p6TeV" : 0.06206,
            
            ###### H Decays ######

            "WminusH-HtoNon2B_Par-M-125_TuneCP5_13p6TeV" : 0.6409,
            "WminusH-Wto2Q-Hto2B_Par-M-125_TuneCP5_13p6TeV" : 0.3918,

            "WplusH-HtoNon2B_Par-M-125_TuneCP5_13p6TeV" : 1.024,
            "WplusH-Wto2Q-Hto2B_Par-M-125_TuneCP5_13p6TeV" : 0.6226,

            "ZH-HtoNon2B_Par-M-125_TuneCP5_13p6TeV" : 0.9014,
            "ZH-Zto2Nu-Hto2B_Par-M-125_TuneCP5_13p6TeV" : 0.168,
            "ZH-Zto2Q-Hto2B_Par-M-125_TuneCP5_13p6TeV" : 0.5958,
            
            # from twiki (https://twiki.cern.ch/twiki/bin/view/LHCPhysics/LHCHWG136TeVxsec_extrap)
            "TTH-Hto2B_Par-M-125_TuneCP5_13p6TeV" : 0.3334,
            "TTH-HtoNon2B_Par-M-125_TuneCP5_13p6TeV" : 0.2412,
            "WminusH-WtoLNu-Hto2B_Par-M-125_TuneCP5_13p6TeV" : 0.0638,
            "WplusH-WtoLNu-Hto2B_Par-M-125_TuneCP5_13p6TeV" : 0.09896,
            "ZH-Zto2L-Hto2B_Par-M-125_TuneCP5_13p6TeV" : 0.03174,
            #---------------------------------------------------

            "GluGluH-Hto2Zto4L_Par-M-125_TuneCP5_13p6TeV": 0.01395, # From twiki https://twiki.cern.ch/twiki/bin/view/LHCPhysics/LHCHWGGGF_RUN2 and using BR:0.000267
            "GluGluZH-Zto2L-Hto2B_Par-M-125_TuneCP5_13p6TeV": 0.006838,
            "GluGluZH-Zto2Nu-Hto2B_Par-M-125_TuneCP5_13p6TeV": 0.01351,
            "GluGluZH-Zto2Q-Hto2B_Par-M-125_TuneCP5_13p6TeV": 0.04776,

            ##############

            "Zto2Q-4Jets_Bin-HT-100to400_TuneCP5_13p6TeV" : 6328.0,
            "Zto2Q-4Jets_Bin-HT-400to800_TuneCP5_13p6TeV" : 145.1,
            "Zto2Q-4Jets_Bin-HT-800to1500_TuneCP5_13p6TeV" : 12.9,
            "Zto2Q-4Jets_Bin-HT-1500to2500_TuneCP5_13p6TeV" : 0.8541,
            "Zto2Q-4Jets_Bin-HT-2500_TuneCP5_13p6TeV" : 0.05684,
            "ZZJJto4L-EWK_TuneCP5_13p6TeV" : 0.001144,
            "ZZJJto4L-QCD_TuneCP5_13p6TeV" : 0.02029,
            "ZZto2L2Nu_TuneCP5_13p6TeV" : 1.031,
            "ZZto2L2Q_TuneCP5_13p6TeV" : 6.788,
            "ZZto2Nu2Q_TuneCP5_13p6TeV" : 4.826,
            "ZZto4L_TuneCP5_13p6TeV" : 1.39,
            "ZZto4Q-1Jets_TuneCP5_13p6TeV" : 7.832,
            "ZZ_TuneCP5_13p6TeV" : 12.75, # XSDB Also quotes 12.85
            "ZZZ-5F_TuneCP5_13p6TeV" : 0.01591,
 

            # From the old xsecs_13p6TeV.json in the repo (from XSDB?)
            "DYto2L-2Jets_Bin-1J-MLL-50-PTLL-40to100": 475.3,
            "DYto2L-2Jets_Bin-1J-MLL-50-PTLL-100to200": 45.42,
            "DYto2L-2Jets_Bin-1J-MLL-50-PTLL-200to400": 3.382,
            "DYto2L-2Jets_Bin-1J-MLL-50-PTLL-400to600": 0.1162,
            "DYto2L-2Jets_Bin-1J-MLL-50-PTLL-600": 0.01392,
            "DYto2L-2Jets_Bin-2J-MLL-50-PTLL-40to100": 179.3,
            "DYto2L-2Jets_Bin-2J-MLL-50-PTLL-100to200": 51.68,
            "DYto2L-2Jets_Bin-2J-MLL-50-PTLL-200to400": 7.159,
            "DYto2L-2Jets_Bin-2J-MLL-50-PTLL-400to600": 0.4157,
            "DYto2L-2Jets_Bin-2J-MLL-50-PTLL-600": 0.07019,

        },

    },

    ### Run 2 xsec numbers ###
    "run2" : {

        "data" : {
        },

        "sig" : {
            "VBSWWH_OS_c2v1p0_c3_1p0": 0.000643,
            "VBSWWH_SS_c2v1p0_c3_1p0": 0.000316,
            "VBSWZH_c2v1p0_c3_1p0"   : 0.000418,
            "VBSZZH_c2v1p0_c3_1p0"   : 0.000108,

            "VBSWWH_OS_c2v1p5_c3_1p0": 0.001091,
            "VBSWWH_SS_c2v1p5_c3_1p0": 0.000620,
            "VBSWZH_c2v1p5_c3_1p0"   : 0.000707,
            "VBSZZH_c2v1p5_c3_1p0"   : 0.000368,

            "VBSWWH_OS_c2v1p0_c3_10p0": 0.001587,
            "VBSWWH_SS_c2v1p0_c3_10p0": 0.000445,
            "VBSWZH_c2v1p0_c3_10p0"   : 0.000624,
            "VBSZZH_c2v1p0_c3_10p0"   : 0.000416,
        },

                
        "bkg": {
            #AN-24-183 v9 (https://cms.cern.ch/iCMS/analysisadmin/cadilines?line=HIG-24-003)
            "QCD_HT100to200_TuneCP5_PSWeights_13TeV"                             : 27849880.0,
            "QCD_HT200to300_TuneCP5_PSWeights_13TeV"                             : 1716997.0,
            "QCD_HT300to500_TuneCP5_PSWeights_13TeV"                             : 351302.0,
            "QCD_HT500to700_TuneCP5_PSWeights_13TeV"                             : 31630.0,
            "QCD_HT700to1000_TuneCP5_PSWeights_13TeV"                            : 6802.0,
            "QCD_HT1000to1500_TuneCP5_PSWeights_13TeV"                           : 1206.0,
            "QCD_HT1500to2000_TuneCP5_PSWeights_13TeV"                           : 98.71,
            "QCD_HT2000toInf_TuneCP5_PSWeights_13TeV"                            : 20.2,
            "TTToSemiLeptonic_TuneCP5_13TeV"                           : 365.34,
            "TTToHadronic_TuneCP5_13TeV"                               : 377.96,
            "ST_tW_antitop_5f_inclusiveDecays_TuneCP5_13TeV"           : 19.559,
            "ST_tW_top_5f_inclusiveDecays_TuneCP5_13TeV"               : 19.559,
            "WJetsToQQ_HT-200to400_TuneCP5_13TeV"                      : 2549.0,
            "WJetsToQQ_HT-400to600_TuneCP5_13TeV"                      : 276.5,
            "WJetsToQQ_HT-600to800_TuneCP5_13TeV"                      : 59.25,
            "WJetsToQQ_HT-800toInf_TuneCP5_13TeV"                      : 28.75,
            "EWKWminus2Jets_WToQQ_dipoleRecoilOn_TuneCP5_13TeV"        : 10.67,
            "EWKWplus2Jets_WToQQ_dipoleRecoilOn_TuneCP5_13TeV"         : 10.67,
            "EWKZ2Jets_ZToLL_M-50_TuneCP5_withDipoleRecoil_13TeV"      : 6.22,
            "EWKZ2Jets_ZToNuNu_M-50_TuneCP5_withDipoleRecoil_13TeV"    : 10.72,
            "EWKZ2Jets_ZToQQ_dipoleRecoilOn_TuneCP5_13TeV"             : 10.67,
            "TTWJetsToQQ_TuneCP5_13TeV"                                : 0.4377,
            "TTWW_TuneCP5_13TeV"                                       : 0.0115,
            "TTWZ_TuneCP5_13TeV"                                       : 0.003884,
            "ttHToNonbb_M125_TuneCP5_13TeV"                            : 0.215,
            "ttHTobb_M125_TuneCP5_13TeV"                               : 0.1279,
            "VHToNonbb_M125_TuneCP5_13TeV"                             : 2.207,
            "WWW_4F_TuneCP5_13TeV"                                     : 0.2086,
            "WWZ_4F_TuneCP5_13TeV"                                     : 0.1651,
            "WZJJ_EWK_InclusivePolarization_TuneCP5_13TeV"             : 0.01701,
            "WZTo2Q2L_mllmin4p0_TuneCP5_13TeV"                         : 5.6,
            "WZZ_TuneCP5_13TeV"                                        : 0.05565,
            "ZZTo4Q_5f_TuneCP5_13TeV"                                  : 3.451,
            "ZZTo2Q2L_mllmin4p0_TuneCP5_13TeV"                         : 3.28,
            "ZZZ_TuneCP5_13TeV"                                        : 0.01398,
            "ZJetsToQQ_HT-200to400_TuneCP5_13TeV"                      : 1012.0,
            "ZJetsToQQ_HT-400to600_TuneCP5_13TeV"                      : 114.2,
            "ZJetsToQQ_HT-600to800_TuneCP5_13TeV"                      : 25.34,
            "ZJetsToQQ_HT-800toInf_TuneCP5_13TeV"                      : 12.99,
            "ZZTo2Nu2Q_5f_TuneCP5_13TeV"                               : 4.58725,
            #-----------------------------------------------------------------------------
        
            #AN-23-016 v15 (https://cms.cern.ch/iCMS/analysisadmin/cadilines?line=HIG-24-003)
            "TTTo2L2Nu_TuneCP5_13TeV"                                  : 88.29,
            "ST_t-channel_antitop_4f_InclusiveDecays_TuneCP5_13TeV"    : 80.95,
            "ST_t-channel_top_4f_InclusiveDecays_TuneCP5_13TeV"        : 136.02,
            "DYJetsToLL_M-10to50_TuneCP5_13TeV"                        : 20657.0,
            "DYJetsToLL_M-50_TuneCP5_13TeV"                            : 6198.0,
            "EWKWMinus2Jets_WToLNu_M-50_TuneCP5_withDipoleRecoil_13TeV": 32.26,
            "EWKWPlus2Jets_WToLNu_M-50_TuneCP5_withDipoleRecoil_13TeV" : 39.33,
            "TTWJetsToLNu_TuneCP5_13TeV"                               : 0.2043,
            "TTZToLLNuNu_M-10_TuneCP5_13TeV"                           : 0.2529,
            "TTbb_4f_TTTo2L2Nu"                                        : 0.04,
            "TTbb_4f_TTToSemiLeptonic"                                 : 0.62,
            "VBFWH_HToBB_WToLNu_M-125_dipoleRecoilOn_TuneCP5_13TeV"    : 0.02656,
            "WWJJToLNuLNu_EWK_noTop_TuneCP5_13TeV"                     : 0.284,
            "WWTo1L1Nu2Q_4f_TuneCP5_13TeV"                             : 49.997,
            "WWTo2L2Nu_TuneCP5_13TeV"                                  : 12.178,
            "WZTo1L3Nu_4f_TuneCP5_13TeV"                               : 3.05402,
            "WZTo3LNu_TuneCP5_13TeV"                                   : 4.42965,
            "WminusH_HToBB_WToLNu_M-125_TuneCP5_13TeV"                 : 0.0490124,
            "WplusH_HToBB_WToLNu_M-125_TuneCP5_13TeV"                  : 0.084876,
            "ZH_HToBB_ZToLL_M-125_TuneCP5_13TeV"                       : 0.0262749,
            "ZZJJTo4L_TuneCP5_13TeV"                                   : 0.00884,
            "ZZTo2L2Nu_TuneCP5_13TeV"                                  : 0.564,
            "ggZH_HToBB_ZToLL_M-125_TuneCP5_13TeV"                     : 0.0024614,
            "ZZJJTo4L_EWKnotop_TuneCP5_13TeV"                          : 0.00884, 
            # for numbers below we use averages
            "WJetsToLNu_HT-70To100_TuneCP5_13TeV"                      : 1308.9025,
            "WJetsToLNu_HT-100To200_TuneCP5_13TeV"                     : 1324.85,
            "WJetsToLNu_HT-200To400_TuneCP5_13TeV"                     : 347.935075,
            "WJetsToLNu_HT-400To600_TuneCP5_13TeV"                     : 46.62084375,
            "WJetsToLNu_HT-600To800_TuneCP5_13TeV"                     : 11.23292175,
            "WJetsToLNu_HT-800To1200_TuneCP5_13TeV"                    : 5.07420335,
            "WJetsToLNu_HT-1200To2500_TuneCP5_13TeV"                   : 1.177367725,
            "WJetsToLNu_HT-2500ToInf_TuneCP5_13TeV"                    : 0.02426248275,
            #-----------------------------------------------------------------------------
        
            #AN-22-136 v12 (https://cms.cern.ch/iCMS/analysisadmin/cadilines?line=HIG-24-003)
            "QCD_HT50to100_TuneCP5_PSWeights_13TeV"                    : 187700000.0,
            "ST_s-channel_4f_leptonDecays_TuneCP5_13TeV"               : 3.74,
            "TTbb_4f_TTToHadronic"                                     : 5.5,
            "ttWJets_TuneCP5_13TeV"                                    : 0.4611,
            "ttZJets_TuneCP5_13TeV"                                    : 0.5407,
            "WminusH_HToBB_WToQQ_M-125_TuneCP5_13TeV"                  : 0.3675,
            "WplusH_HToBB_WToQQ_M-125_TuneCP5_13TeV"                   : 0.589,
            "ZH_HToBB_ZToBB_M-125_TuneCP5_13TeV"                       : 0.5612,
            "ZH_HToBB_ZToNuNu_M-125_TuneCP5_13TeV"                     : 0.1573,
            "ZH_HToBB_ZToQQ_M-125_TuneCP5_13TeV"                       : 0.5612,
            "ggZH_HToBB_ZToBB_M-125_TuneCP5_13TeV"                     : 0.04319,
            "ggZH_HToBB_ZToNuNu_M-125_TuneCP5_13TeV"                   : 0.01222,
            "ggZH_HToBB_ZToQQ_M-125_TuneCP5_13TeV"                     : 0.04319,
            "WZ_TuneCP5_13TeV"                                         : 27.59,
            "WW_TuneCP5_13TeV"                                         : 75.95,
            "ZZ_TuneCP5_13TeV"                                         : 12.17,
            #-----------------------------------------------------------------------------

            #AN-19-004(https://cms.cern.ch/iCMS/jsp/db_notes/noteInfo.jsp?cmsnoteid=CMS%20AN-2019/004) (k factor of 1.7 used)
            "GluGluToContinToZZTo2e2mu_TuneCP5_13TeV" : 0.005423,
            "GluGluToContinToZZTo2e2tau_TuneCP5_13TeV" : 0.005423,
            "GluGluToContinToZZTo2mu2tau_TuneCP5_13TeV" : 0.005423,
            "GluGluToContinToZZTo4e_TuneCP5_13TeV" : 0.002703,
            "GluGluToContinToZZTo4mu_TuneCP5_13TeV" : 0.002703,
            "GluGluToContinToZZTo4tau_TuneCP5_13TeV" : 0.002703,
            #-----------------------------------------------------------------------------

            #https://twiki.cern.ch/twiki/bin/view/LHCPhysics/HiggsXSBR#Production_cross_sections_an_AN1
            #Apply branching fractions to production cross sections found above
            "GluGluZH_HToWWTo2L2Nu_TuneCP5_13TeV": 0.00282,
            "GluGluZH_HToWWTo2L2Nu_M-125_TuneCP5_13TeV": 0.00282,
            "HZJ_HToWWTo2L2Nu_ZTo2L_M-125_TuneCP5_13TeV": 0.00177,
            #--------------------------------------------------------------------------
        
            #AN-19-004 (https://cms.cern.ch/iCMS/jsp/db_notes/noteInfo.jsp?cmsnoteid=CMS%20AN-2019/156)
            "tZq_ll_4f_ckm_NLO_TuneCP5_13TeV": 0.0758,
            #----------------------------------------------------------------------------
        
            #from https://github.com/cmstas/VVVNanoLooper/blob/master/weights/xsec.txt
            "SSWW": 0.02794,
            #----------------------------------------------------------------------------
        
            #from TOP-22-008
            "TWZToLL_tlept_Wlept_5f_DR_TuneCP5_13TeV": 0.0015,
            #----------------------------------------------------------------------------
        
            #XSDB
            "WJetsToLNu_TuneCP5_13TeV"                                 : 66680.0,
            "WWTo4Q_4f_TuneCP5_13TeV"                                  : 51.03,
            "WZTo1L1Nu2Q_4f_TuneCP5_13TeV"                             : 9.119,
            "ZZTo4L_M-1toInf_TuneCP5_13TeV"                            : 13.74, # https://xsecdb-xsdb-official.app.cern.ch/xsdb/?columns=50331648&currentPage=0&pageSize=50&searchQuery=process_name%3DZTo4L_M-1toInf_TuneCP5_13TeV%20%2A

            #-----------------------------------------------------------------------------

            # From twiki https://twiki.cern.ch/twiki/bin/view/LHCPhysics/LHCHWGGGF_RUN2 and using BR:0.000267
            "GluGluHToZZTo4L": 0.01297,

            #-----------------------------------------------------------------------------

            # From GenXSecAnalyzer (computed by claude)
            "DYJetsToLL_M-50_HT-70to100_TuneCP5_PSweights_13TeV"   : 139.7,
            "DYJetsToLL_M-50_HT-100to200_TuneCP5_PSweights_13TeV"  : 140.3,
            "DYJetsToLL_M-50_HT-200to400_TuneCP5_PSweights_13TeV"  : 38.51,
            "DYJetsToLL_M-50_HT-400to600_TuneCP5_PSweights_13TeV"  : 5.211,
            "DYJetsToLL_M-50_HT-600to800_TuneCP5_PSweights_13TeV"  : 1.268,
            "DYJetsToLL_M-50_HT-800to1200_TuneCP5_PSweights_13TeV" : 0.5683,
            "DYJetsToLL_M-50_HT-1200to2500_TuneCP5_PSweights_13TeV": 0.1333,
            "DYJetsToLL_M-50_HT-2500toInf_TuneCP5_PSweights_13TeV" : 0.002987,


        }
    },

}
