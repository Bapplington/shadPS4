// SPDX-FileCopyrightText: Copyright 2026 Bapplington
// SPDX-License-Identifier: GPL-2.0-or-later
#include "core/file_sys/archive_read_trace.h"
#include <algorithm>
#include <cassert>
#include <mutex>
#include <thread>
#include <vector>
int main() {
    using namespace Core::FileSys;
    assert(IsTraceArchive("/app0/graphics_fix.big"));
    assert(IsTraceArchive("/app0//graphics_fix.big"));
    assert(IsTraceArchive("/hostapp///patch.big"));
    assert(IsTraceArchive("/hostapp/patch_post_fix_b.big"));
    for (auto path : {"/savedata0/private.big", "/app0/data/name.big", "/app0//data/name.big", "/app0/../save.big",
                      "/app0/asset.bin", "/app0/x.big\n", "C:/secret.big", "/app0/.big"}) {
        assert(!IsTraceArchive(path));
    }
    ArchiveTraceBudget gate{4000};
    assert(gate.Next(false, "/app0/patch.big") == 0);
    assert(gate.Next(true, "/savedata0/patch.big") == 0);
    std::vector<unsigned> ids;
    std::mutex lock;
    std::vector<std::thread> threads;
    for (int n = 0; n != 8; ++n) {
        threads.emplace_back([&] {
            for (int i = 0; i != 1000; ++i) {
                if (auto id = gate.Next(true, "/app0/patch.big")) {
                    std::scoped_lock guard{lock};
                    ids.push_back(id);
                }
            }
        });
    }
    for (auto& thread : threads) thread.join();
    std::sort(ids.begin(), ids.end());
    assert(ids.size() == 4000);
    for (unsigned i = 0; i != ids.size(); ++i) assert(ids[i] == i + 1);
    assert(gate.Next(true, "/app0/patch.big") == 0);
}
