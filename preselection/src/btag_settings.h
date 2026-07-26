#ifndef BTAG_SETTINGS_H
#define BTAG_SETTINGS_H

#pragma once

#include <string>
#include <cmath>
#include <algorithm>

inline double bTagMaxAbsEta(const std::string &year) {
    return (year == "2016preVFP" || year == "2016postVFP") ? 2.4 : 2.5;
}

// The Run-2 UParTAK4 SF payloads are tabulated below |eta|=2.4, while the
// selected-jet acceptance remains |eta|<2.5 for 2017/2018.  Clamp only the
// SF lookup coordinate to the valid payload domain; do not discard those jets.
inline double bTagSFAbsEta(const std::string &year, double eta) {
    const double payload_max = year == "2024Prompt" ? 2.5 : 2.4;
    return std::min(std::abs(eta), std::nextafter(payload_max, 0.0));
}

inline std::string bTagSafeYearToken(std::string year) {
    if (year == "2022Re-recoBCD") return "2022Re_recoBCD";
    if (year == "2022Re-recoE+PromptFG") return "2022Re_recoE_PromptFG";
    return year;
}

bool bTagScaleFactorsEnabled(const std::string &channel);

#endif
