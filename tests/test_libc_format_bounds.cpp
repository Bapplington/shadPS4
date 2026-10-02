// SPDX-FileCopyrightText: Copyright 2026 Bapplington
// SPDX-License-Identifier: GPL-2.0-or-later

#include <array>
#include <cassert>
#include <cstring>
#include <string>
#include "core/libraries/libc_internal/printf.h"

using Libraries::LibcInternal::vsnprintf_ctx;

int main() {
    Common::VaRegSave registers{};
    u64 overflow[2]{};
    Common::VaList args{0, 48, overflow, &registers};
    std::array<char, 10> guarded{};
    guarded.fill('!');
    assert(vsnprintf_ctx(guarded.data() + 1, 4, "abcdef", &args) == 6);
    assert(std::strcmp(guarded.data() + 1, "abc") == 0);
    assert(guarded[0] == '!' && guarded[5] == '!');
    assert(vsnprintf_ctx(nullptr, 0, "abcdef", &args) == 6);
    assert(vsnprintf_ctx(guarded.data(), 0, "abc", &args) == 3);
    assert(guarded[0] == '!');
    assert(vsnprintf_ctx(guarded.data(), 1, "abc", &args) == 3);
    assert(guarded[0] == 0 && guarded[1] == 'a');
    const std::string long_string(1024, 'x');
    registers.gp[0] = reinterpret_cast<u64>(long_string.c_str());
    guarded.fill('!');
    assert(vsnprintf_ctx(guarded.data() + 1, 8, "%s", &args) == 1024);
    assert(guarded[0] == '!' && guarded[9] == '!' && guarded[8] == 0);
    registers.gp[0] = 42;
    registers.gp[1] = reinterpret_cast<u64>("court");
    char text[32]{};
    assert(vsnprintf_ctx(text, sizeof(text), "%d %s", &args) == 8);
    assert(std::strcmp(text, "42 court") == 0);
    assert(args.gp_offset == 0);
    args.gp_offset = 48;
    overflow[0] = 123;
    assert(vsnprintf_ctx(text, sizeof(text), "%d", &args) == 3);
    assert(std::strcmp(text, "123") == 0);
    args.gp_offset = 0;
    assert(vsnprintf_ctx(text, 1, "", &args) == 0 && text[0] == 0);
}
