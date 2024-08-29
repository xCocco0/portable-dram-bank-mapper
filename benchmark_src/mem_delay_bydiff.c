
#include <stdio.h>
#include <stdint.h>
#include <time.h>
#include <stdlib.h>
#include <errno.h>
#include <sys/mman.h>
#include <unistd.h>
#include <sched.h>
#include <limits.h>

#include "mem_delay_utilities.h"

int main(int argc, char* argv[])
{
	
#if HAS_1GB_HUGEPAGES != 1 && HAS_2MB_HUGEPAGES != 1
	fprintf(stderr, "Cannot use without huge pages support\n");
	exit(1);
#endif

	if(argc < 2) {
		fprintf(stderr, "Usage: %20s <diff>\n", argv[0]);
		exit(1);
	}

	unsigned long long diff = strtoull(argv[1], NULL, 0);
	if(diff == ULLONG_MAX) {
		perror("strtoull");
		exit(1);
	}
	struct timespec t;
	
	char *addr = get_mem_chunk();

	mlockall(MCL_CURRENT | MCL_FUTURE);

	clock_gettime(CLOCK_MONOTONIC, &t);

	srand(t.tv_nsec + t.tv_sec);
	int offset = rand();
	
	register char *a1 = addr + (offset % MEM_SIZE), *a2 = addr + ((offset ^ diff) % MEM_SIZE);
	char dummy;

	if(fill_cache(addr, a1, a2) != 0) {
		perror("Error fill cache");
		exit(1);
	}
	
	t.tv_sec = 0; t.tv_nsec = 0;

	sched_yield();

	time_to_mem(&dummy, &dummy, &t);

	time_to_mem(a1, a2, &t);

	printf("%lu", t.tv_nsec + t.tv_sec * 1000000000UL);
	printf(",%lu,%lu", (unsigned long) a1 % MEM_SIZE, (unsigned long) a2 % MEM_SIZE);
	//printf(",%d", ((unsigned long) a1 & BANK_MASK) == ((unsigned long) a2 & BANK_MASK) ? 1 : 0);
	printf("\n");


	return 0;
}
