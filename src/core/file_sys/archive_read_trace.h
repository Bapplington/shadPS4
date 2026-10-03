// SPDX-FileCopyrightText: Copyright 2026 Bapplington
// SPDX-License-Identifier: GPL-2.0-or-later
#pragma once
#include <atomic>
#include <cstdint>
#include <string_view>

namespace Core::FileSys {
// Limit diagnostics to top-level game archives; never saves or host paths.
inline bool IsTraceArchive(std::string_view path) {
    if (path.starts_with("/app0/")) {
        path.remove_prefix(6);
    } else if (path.starts_with("/hostapp/")) {
        path.remove_prefix(9);
    } else {
        return false;
    }
    // The game uses /app0//archive.big; accept redundant mount separators only.
    while (path.starts_with("/")) {
        path.remove_prefix(1);
    }
    return path.size() > 4 && path.ends_with(".big") &&
           path.find_first_of("/\\\r\n") == std::string_view::npos;
}

class ArchiveTraceBudget {
public:
    explicit ArchiveTraceBudget(std::uint32_t limit = 20000) : limit{limit} {}
    // Zero means disabled, irrelevant path, or exhausted. IDs are unique across threads.
    std::uint32_t Next(bool enabled, std::string_view path) {
        if (!enabled || !IsTraceArchive(path)) {
            return 0;
        }
        auto value = issued.load(std::memory_order_relaxed);
        while (value < limit) {
            if (issued.compare_exchange_weak(value, value + 1, std::memory_order_relaxed)) {
                return value + 1;
            }
        }
        return 0;
    }
private:
    const std::uint32_t limit;
    std::atomic<std::uint32_t> issued{0};
};
} // namespace Core::FileSys
