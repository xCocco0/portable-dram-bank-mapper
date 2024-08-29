
#ifndef MEM_BENCH_UTILITIES_H
#define MEM_BENCH_UTILITIES_H

#include "mem_delay_config.h"

#if HAS_1GB_HUGEPAGES != 1 && HAS_2MB_HUGEPAGES != 1 && HAS_ROOT != 1
#error Invalid configuration
#endif

#include <time.h>
#include <stdint.h>

#if HAS_1GB_HUGEPAGES
#define MEM_SIZE (1 << 30) // 1GB
#elif HAS_ROOT
#define MEM_SIZE (1 << 30) // 1GB
#elif HAS_2MB_HUGEPAGES
#define MEM_SIZE (1 << 21) // 2MB
#endif

#define CACHE_FILL_SIZE (1 << 21) // use 2MB huge page

#define CACHE_SIZE (1 << 20)   // 1MB cache
#define CACHE_WAYS (16)        // 16 ways
#define CACHE_LINE_BYTES (64)  // 64 bytes

#define NSEC_IN_SEC (1000000000UL)


void printbin(size_t addr, int size);

void diff_timespec(struct timespec *out, const struct timespec *time1, const struct timespec *time0);

void time_to_mem(const char *ptr1, const char *ptr2, struct timespec *delta);

int fill_cache(char *base, char *addr1, char *addr2);

char * get_mem_chunk(void);

#endif
