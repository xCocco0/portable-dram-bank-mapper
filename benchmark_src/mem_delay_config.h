
#ifndef MEM_BENCH_CONFIG_H
#define MEM_BENCH_CONFIG_H

#define CACHE_SIZE (1 << 20)   // 1MB cache
#define CACHE_WAYS (16)        // 16 ways
#define CACHE_LINE_BYTES (64)  // 64 bytes

#define HAS_1GB_HUGEPAGES (0)
#define HAS_2MB_HUGEPAGES (1)
#define HAS_ROOT (0)

#endif
