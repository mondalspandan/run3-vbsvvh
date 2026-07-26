#include "btag_settings.h"

#include <fstream>
#include <map>
#include <stdexcept>

namespace {

std::string trim(std::string value) {
    const auto begin = value.find_first_not_of(" \t");
    if (begin == std::string::npos) return "";
    const auto end = value.find_last_not_of(" \t");
    return value.substr(begin, end - begin + 1);
}

const std::map<std::string, bool> &applyBTagConfig() {
    static const auto config = [] {
        constexpr const char *path = "applybtag.yaml";
        std::ifstream input(path);
        if (!input) throw std::runtime_error("Cannot read b-tag application configuration " + std::string(path));

        std::map<std::string, bool> parsed;
        std::string line;
        while (std::getline(input, line)) {
            const auto comment = line.find('#');
            if (comment != std::string::npos) line.erase(comment);
            line = trim(line);
            if (line.empty()) continue;

            const auto separator = line.find(':');
            if (separator == std::string::npos || line.find(':', separator + 1) != std::string::npos)
                throw std::runtime_error("Invalid applybtag.yaml entry: " + line);
            const auto channel = trim(line.substr(0, separator));
            const auto value = trim(line.substr(separator + 1));
            if (channel.empty() || (value != "True" && value != "False"))
                throw std::runtime_error("Invalid applybtag.yaml entry: " + line);
            if (!parsed.emplace(channel, value == "True").second)
                throw std::runtime_error("Duplicate channel in applybtag.yaml: " + channel);
        }
        if (parsed.empty()) throw std::runtime_error("applybtag.yaml contains no channels");
        return parsed;
    }();
    return config;
}

} // namespace

bool bTagScaleFactorsEnabled(const std::string &channel) {
    const auto &config = applyBTagConfig();
    const auto entry = config.find(channel);
    if (entry == config.end())
        throw std::runtime_error("Channel " + channel + " is missing from applybtag.yaml");
    return entry->second;
}
