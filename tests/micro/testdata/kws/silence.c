// SPDX-FileCopyrightText: © 2019-2023 The Apache Software Foundation
//
// SPDX-License-Identifier: Apache-2.0
/*
 * This work is a derivative of "Speech Commands V2" by Google, used under CC BY 4.0.
 */

static const char input_silence[1960] = {
    0x23, 0x17, 0xe0, 0x3,  0x9,  0xe7, 0xe7, 0xdb, 0xcf, 0xc5, 0xe0, 0xdb, 0xc5, 0xcf, 0xef, 0xcf,
    0xcf, 0xdb, 0xef, 0xdb, 0xe7, 0xc5, 0x5,  0x3,  0xfc, 0xe7, 0xf6, 0xdb, 0xcf, 0xe7, 0x9,  0xef,
    0xef, 0xdb, 0xcf, 0xe7, 0xe0, 0xe7, 0xe0, 0xc5, 0xff, 0xe0, 0x4,  0xcf, 0xdb, 0xb4, 0x80, 0xdb,
    0xef, 0x80, 0xc5, 0xe4, 0x9,  0xe4, 0xcf, 0xc5, 0xdb, 0xcf, 0xdb, 0xcf, 0xf5, 0xdb, 0xe7, 0xcf,
    0xef, 0xe4, 0xe7, 0xe4, 0xe7, 0xdb, 0xdb, 0xcf, 0xc5, 0xdb, 0xcf, 0xcf, 0xcf, 0xb4, 0xcf, 0xcf,
    0x13, 0xef, 0xf5, 0x80, 0x80, 0x80, 0xc5, 0xcf, 0xcf, 0x80, 0x80, 0xcf, 0xf5, 0xcf, 0x80, 0x80,
    0x80, 0x80, 0x80, 0xcf, 0xf9, 0xdb, 0xcf, 0x80, 0x80, 0xcf, 0xe7, 0xdb, 0xfb, 0xe4, 0xdb, 0xcf,
    0xe7, 0xcf, 0xe7, 0xb4, 0xdb, 0xe4, 0xcf, 0xb4, 0xfb, 0x0,  0x6,  0xd6, 0xec, 0xb4, 0x80, 0xb4,
    0x80, 0x80, 0x80, 0x80, 0xf3, 0xb4, 0xdb, 0xdb, 0xc5, 0xb4, 0xc5, 0x80, 0xcf, 0xb4, 0xdb, 0xb4,
    0xb4, 0x80, 0xcf, 0x80, 0xdb, 0xb4, 0xb4, 0x80, 0xc5, 0x80, 0xdb, 0xcf, 0xdb, 0xcf, 0xcf, 0xb4,
    0xff, 0xcf, 0xdb, 0x80, 0xb4, 0x80, 0x80, 0xd6, 0xcf, 0xcf, 0x80, 0xcf, 0xcf, 0xcf, 0xe4, 0xcf,
    0xc5, 0x80, 0x80, 0x80, 0xdb, 0x80, 0xb4, 0x80, 0xdb, 0x80, 0xb4, 0x80, 0xb4, 0xb4, 0xdb, 0xcf,
    0xec, 0xe0, 0xcf, 0xe0, 0xe4, 0xd6, 0xdb, 0x80, 0xef, 0xf6, 0xea, 0xd6, 0xb4, 0xd6, 0xec, 0xc5,
    0xec, 0xcf, 0xc5, 0x80, 0xdb, 0x80, 0x80, 0x80, 0x80, 0xb4, 0xdb, 0xcf, 0xdb, 0xd6, 0xe4, 0xc5,
    0xdb, 0xb4, 0xcf, 0xc5, 0xcf, 0xd6, 0xe4, 0xc5, 0xf3, 0xe0, 0xec, 0xe0, 0xfd, 0xe7, 0xcf, 0xb4,
    0x24, 0x1a, 0x0,  0xf1, 0x19, 0xe0, 0xec, 0xe0, 0xb4, 0xcf, 0xdb, 0xd6, 0xb4, 0xb4, 0xb4, 0x80,
    0xdb, 0x80, 0xdb, 0xc5, 0xf1, 0xe7, 0xea, 0xf8, 0xec, 0xc5, 0xe4, 0xe0, 0xec, 0xc5, 0xcf, 0xb4,
    0xe4, 0xd6, 0xe4, 0xdb, 0xf1, 0xdb, 0xdb, 0xc5, 0x22, 0xea, 0xe7, 0x80, 0xea, 0xf3, 0xec, 0xfb,
    0xec, 0xe0, 0xdb, 0xb4, 0xe4, 0xe0, 0xec, 0xd6, 0xf3, 0xb4, 0xb4, 0x80, 0xd6, 0xd6, 0xe4, 0xdb,
    0xcf, 0xb4, 0xdb, 0xdb, 0xf1, 0xe4, 0xcf, 0xb4, 0xe4, 0xcf, 0xe4, 0xea, 0xea, 0xe4, 0xe4, 0xd6,
    0xef, 0xb4, 0xc5, 0xc5, 0xd6, 0xc5, 0xe4, 0x80, 0x80, 0x80, 0xb4, 0x80, 0xcf, 0xc5, 0x0,  0xdb,
    0xb4, 0xb4, 0xdb, 0x80, 0xb4, 0x80, 0x80, 0x80, 0xb4, 0x80, 0x80, 0x80, 0xb4, 0xc5, 0xcf, 0xb4,
    0xcf, 0xcf, 0xe0, 0xcf, 0xcf, 0x80, 0xb4, 0x80, 0xec, 0xd6, 0xe0, 0xc5, 0xb4, 0xb4, 0xcf, 0x80,
    0xcf, 0xb4, 0xcf, 0x80, 0xd6, 0xc5, 0x80, 0x80, 0xdb, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80,
    0xcf, 0x80, 0x80, 0x80, 0xcf, 0xb4, 0xd6, 0xb4, 0xd6, 0xb4, 0xf1, 0xc5, 0xc5, 0x80, 0xb4, 0x80,
    0x11, 0xc5, 0xb4, 0x80, 0x80, 0x80, 0xb4, 0x80, 0xb4, 0x80, 0x80, 0x80, 0xc5, 0xcf, 0xb4, 0x80,
    0xe4, 0xb4, 0x80, 0xb4, 0x80, 0x80, 0x80, 0x80, 0xcf, 0x80, 0xb4, 0x80, 0x80, 0x80, 0xb4, 0xb4,
    0xd6, 0xc5, 0xb4, 0x80, 0xc5, 0x80, 0xb4, 0x80, 0xcf, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80,
    0xb4, 0xc5, 0xe4, 0xc5, 0xb4, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80,
    0x80, 0x80, 0xef, 0x80, 0xc5, 0xb4, 0xc5, 0xc5, 0xc5, 0xcf, 0xd6, 0xc5, 0xf5, 0xb4, 0xcf, 0x80,
    0xe4, 0xc5, 0xb4, 0xe0, 0xd6, 0xb4, 0xcf, 0x80, 0xb4, 0xc5, 0xcf, 0x80, 0xe0, 0xc5, 0xd6, 0x80,
    0x80, 0x80, 0xb4, 0x80, 0x80, 0x80, 0xb4, 0xb4, 0xc5, 0x80, 0xd6, 0xb4, 0xe0, 0xb4, 0xb4, 0xc5,
    0xc5, 0xb4, 0xc5, 0x80, 0xc5, 0xc5, 0xd6, 0x80, 0x80, 0x80, 0xf8, 0x80, 0x80, 0xb4, 0xd6, 0x80,
    0xd6, 0xb4, 0xb4, 0x80, 0xb4, 0x80, 0x80, 0x80, 0x80, 0xb4, 0xcf, 0xcf, 0xe7, 0x80, 0xb4, 0x80,
    0xc5, 0x80, 0xc5, 0x80, 0xb4, 0x80, 0xb4, 0xb4, 0xc5, 0x80, 0xb4, 0x80, 0xc5, 0x80, 0xe0, 0x80,
    0xef, 0x80, 0xcf, 0x80, 0xb4, 0x80, 0x80, 0x80, 0x80, 0x80, 0xb4, 0xb4, 0xfd, 0xb4, 0x80, 0xb4,
    0xe0, 0x80, 0xcf, 0xb4, 0xb4, 0x80, 0xe7, 0xb4, 0xe7, 0xb4, 0xb4, 0xd6, 0xb4, 0x80, 0xe0, 0xc5,
    0x80, 0x80, 0xc5, 0xc5, 0xd6, 0x80, 0xc5, 0x80, 0xdb, 0xc5, 0xea, 0x80, 0x80, 0x80, 0xb4, 0x80,
    0xb4, 0x80, 0xe0, 0x80, 0x80, 0x80, 0xc5, 0xb4, 0x80, 0x80, 0xd6, 0x80, 0xb4, 0x80, 0xb4, 0x80,
    0x80, 0xb4, 0xb4, 0x80, 0x80, 0x80, 0x80, 0x80, 0xb4, 0x80, 0xe7, 0xb4, 0xc5, 0x80, 0xd6, 0x80,
    0xe7, 0xc5, 0xdb, 0x80, 0xdb, 0xcf, 0xe0, 0x80, 0x80, 0x80, 0xc5, 0xb4, 0xdb, 0x80, 0xef, 0xc5,
    0x80, 0x80, 0x80, 0x80, 0xc5, 0xb4, 0x80, 0x80, 0xb4, 0x80, 0x80, 0x80, 0xb4, 0x80, 0xd6, 0x80,
    0xc5, 0xb4, 0xdb, 0x80, 0xb4, 0x80, 0x80, 0x80, 0xe0, 0x80, 0x80, 0xb4, 0xf6, 0xdb, 0xc5, 0x80,
    0x80, 0x80, 0xc5, 0x80, 0x80, 0x80, 0xb4, 0x80, 0xc5, 0x80, 0xb4, 0xb4, 0xd6, 0xb4, 0xd6, 0x80,
    0x80, 0xb4, 0xd6, 0xb4, 0x80, 0x80, 0xdb, 0xb4, 0xf3, 0xb4, 0xdb, 0x80, 0x80, 0x80, 0xc5, 0x80,
    0x1d, 0xcf, 0x16, 0x12, 0x17, 0xc,  0x23, 0x2,  0x1,  0xc5, 0xc5, 0xb4, 0x80, 0x80, 0x80, 0x80,
    0x80, 0xc5, 0xd6, 0xc5, 0xb4, 0xc5, 0xdb, 0x80, 0x80, 0x80, 0x80, 0x80, 0xb4, 0xb4, 0xdb, 0xc5,
    0xe4, 0x80, 0xdb, 0x80, 0xc5, 0xb4, 0x80, 0x80, 0x78, 0x64, 0x7a, 0x64, 0x76, 0x60, 0x67, 0x55,
    0x5a, 0x3a, 0x37, 0x24, 0xf6, 0xc5, 0x14, 0x17, 0x1e, 0x18, 0x31, 0x39, 0x44, 0x43, 0x49, 0x3e,
    0x39, 0x23, 0x18, 0x17, 0x42, 0x41, 0x40, 0x34, 0x39, 0x34, 0x37, 0x30, 0x38, 0x23, 0x22, 0x9,
    0x75, 0x63, 0x73, 0x63, 0x77, 0x58, 0x73, 0x5f, 0x64, 0x4d, 0x57, 0x41, 0x58, 0x46, 0x36, 0x32,
    0x45, 0x51, 0x64, 0x56, 0x72, 0x61, 0x67, 0x57, 0x60, 0x52, 0x49, 0x4e, 0x61, 0x53, 0x62, 0x57,
    0x67, 0x50, 0x66, 0x56, 0x63, 0x52, 0x5e, 0x3d, 0x6b, 0x5a, 0x70, 0x5d, 0x72, 0x50, 0x6c, 0x56,
    0x67, 0x5a, 0x69, 0x49, 0x5a, 0x4f, 0x56, 0x50, 0x61, 0x50, 0x6c, 0x5d, 0x71, 0x5d, 0x6e, 0x56,
    0x6c, 0x58, 0x69, 0x55, 0x6c, 0x57, 0x65, 0x57, 0x6c, 0x56, 0x68, 0x4c, 0x61, 0x58, 0x66, 0x44,
    0x68, 0x52, 0x6b, 0x56, 0x6c, 0x60, 0x6e, 0x52, 0x72, 0x4e, 0x5b, 0x4d, 0x56, 0x4e, 0x68, 0x51,
    0x69, 0x5a, 0x6a, 0x5a, 0x72, 0x54, 0x6f, 0x5d, 0x75, 0x5f, 0x67, 0x57, 0x65, 0x48, 0x5c, 0x4c,
    0x66, 0x52, 0x68, 0x52, 0x63, 0x53, 0x64, 0x44, 0x5f, 0x44, 0x60, 0x49, 0x69, 0x60, 0x71, 0x51,
    0x6c, 0x59, 0x6c, 0x53, 0x62, 0x4b, 0x5c, 0x4e, 0x61, 0x4c, 0x6a, 0x5c, 0x69, 0x4b, 0x6b, 0x56,
    0x6b, 0x40, 0x5d, 0x43, 0x6c, 0x55, 0x60, 0x3f, 0x5f, 0x4d, 0x69, 0x52, 0x64, 0x4d, 0x64, 0x41,
    0x59, 0x3b, 0x55, 0x35, 0x67, 0x55, 0x71, 0x5a, 0x69, 0x58, 0x65, 0x48, 0x5e, 0x4e, 0x6a, 0x55,
    0x69, 0x55, 0x73, 0x5c, 0x68, 0x35, 0x64, 0x57, 0x6a, 0x43, 0x57, 0x42, 0x63, 0x4c, 0x71, 0x57,
    0x60, 0x43, 0x5a, 0x44, 0x5c, 0x3e, 0x5d, 0x3e, 0x57, 0x31, 0x46, 0x7,  0x56, 0x4b, 0x73, 0x52,
    0x64, 0x4b, 0x5b, 0x4a, 0x66, 0x4f, 0x69, 0x4d, 0x69, 0x56, 0x6e, 0x3e, 0x4b, 0x37, 0x5c, 0x44,
    0x56, 0x24, 0x4f, 0x2a, 0x46, 0x3b, 0x61, 0x4e, 0x61, 0x43, 0x5d, 0x45, 0x5e, 0x44, 0x50, 0x3c,
    0x56, 0x2d, 0x45, 0x4,  0x50, 0x40, 0x64, 0x57, 0x69, 0x4d, 0x64, 0x50, 0x62, 0x4e, 0x67, 0x4e,
    0x62, 0x56, 0x67, 0x3c, 0x48, 0x23, 0x58, 0x43, 0x53, 0x28, 0x3b, 0xcf, 0x48, 0x48, 0x5c, 0x40,
    0x4d, 0x37, 0x4e, 0x3c, 0x56, 0x20, 0x3d, 0x11, 0x37, 0xc5, 0x4a, 0xd6, 0x2d, 0x2b, 0x57, 0x4e,
    0x5a, 0x44, 0x60, 0x43, 0x5a, 0x3f, 0x5c, 0x41, 0x67, 0x50, 0x60, 0x2f, 0x36, 0x1c, 0x54, 0x3e,
    0x4f, 0xc,  0x2d, 0x80, 0x36, 0x22, 0x50, 0x41, 0x5f, 0x3e, 0x50, 0x3f, 0x5f, 0x3d, 0x46, 0x19,
    0x41, 0xfd, 0x33, 0xd6, 0x25, 0x2,  0x40, 0x2f, 0x59, 0x3a, 0x4f, 0x3d, 0x47, 0x23, 0x52, 0x32,
    0x5c, 0x3e, 0x45, 0xcf, 0xd,  0xdb, 0x42, 0x2a, 0x3f, 0x80, 0x15, 0x80, 0xe4, 0xb4, 0x36, 0x28,
    0x49, 0x39, 0x52, 0x3a, 0x5a, 0x39, 0x52, 0xb,  0x26, 0x80, 0x27, 0xc5, 0x2f, 0xf6, 0x45, 0x24,
    0x40, 0x29, 0x52, 0x33, 0x43, 0xfc, 0x33, 0x1d, 0x44, 0x17, 0x2e, 0x80, 0x80, 0x80, 0xb4, 0x80,
    0x80, 0x80, 0x24, 0x80, 0xb4, 0x80, 0x34, 0x32, 0x4c, 0x32, 0x4b, 0x30, 0x54, 0x3f, 0x51, 0x30,
    0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0xe4, 0x80, 0x1,  0x80, 0x26, 0x80, 0x80, 0x80,
    0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0xfd, 0x80, 0x80, 0x80, 0xb4, 0x80,
    0x29, 0xe0, 0xe0, 0xc5, 0x27, 0x80, 0x1b, 0x7,  0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80,
    0x80, 0x80, 0x80, 0x80, 0x23, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80,
    0x80, 0x80, 0xf9, 0x80, 0x80, 0x80, 0x80, 0x80, 0xd6, 0x80, 0x80, 0x80, 0xb4, 0x80, 0xf5, 0x80,
    0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80,
    0xe0, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x1d, 0xe4, 0x11, 0xb4, 0x32, 0xa,
    0x6,  0x80, 0x80, 0x80, 0xd6, 0x80, 0x1c, 0xd,  0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80,
    0x80, 0x80, 0x80, 0x80, 0x15, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80,
    0x80, 0x80, 0xf8, 0xcf, 0x10, 0x80, 0x17, 0x80, 0x1e, 0x80, 0xff, 0xec, 0x25, 0x80, 0x1c, 0x23,
    0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80,
    0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x11, 0xb4, 0x2,  0x80, 0x30, 0x8,
    0x15, 0x80, 0x6,  0x20, 0x36, 0xf8, 0x2e, 0x18, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80,
    0x80, 0x80, 0x80, 0x80, 0xf3, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80,
    0x80, 0x80, 0xd,  0x4,  0xa,  0xea, 0x37, 0x24, 0x2a, 0xc,  0x39, 0x26, 0x43, 0x5,  0x2d, 0x1f,
    0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x14, 0x80, 0x80, 0x80,
    0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x7,  0xcf, 0xf,  0xef, 0x32, 0xd,
    0x2a, 0x14, 0x37, 0x1,  0x32, 0x0,  0x38, 0x10, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80,
    0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80,
    0x80, 0x80, 0x1c, 0x80, 0x80, 0x80, 0x28, 0xdb, 0xe4, 0xe0, 0xb4, 0x80, 0x16, 0xcf, 0x1b, 0xb4,
    0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80,
    0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0xb4, 0x80,
    0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80,
    0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80,
    0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80,
    0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80,
    0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80,
    0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80,
    0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80,
    0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80,
    0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80,
    0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80,
    0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80,
    0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80,
    0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80,
    0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80,
    0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80,
    0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80,
    0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80,
    0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80,
    0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80,
    0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80,
    0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80,
    0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80,
    0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80,
    0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80,
    0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80,
    0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80};
