
#include <stdio.h>
#include <stdint.h>
#include <time.h>
#include <stdlib.h>
#include <errno.h>
#include <sys/mman.h>
#include <unistd.h>
#include <limits.h>
#include <sched.h>

#include "mem_delay_utilities.h"

int main(int argc, char* argv[])
{
	
#if HAS_1GB_HUGEPAGES != 1 && HAS_2MB_HUGEPAGES != 1
	fprintf(stderr, "Cannot use without huge pages support\n");
	exit(1);
#endif

	if(argc < 3) {
		fprintf(stderr, "Usage: %20s <addr1> <addr2>\n", argv[0]);
		exit(1);
	}

	unsigned long long addr1, addr2;
	addr1 = strtoull(argv[1], NULL, 0);
	addr2 = strtoull(argv[2], NULL, 0);
	if(addr1 == ULLONG_MAX || addr2 == ULLONG_MAX) {
		perror("strtoull");
		exit(1);
	}

	struct timespec t;
	
	char * addr = mmap(NULL, MEM_SIZE, PROT_READ | PROT_WRITE,
		MAP_PRIVATE | MAP_ANONYMOUS | MAP_POPULATE | MAP_HUGETLB, -1, 0);
	if(addr == (char*) -1) {
		fprintf(stderr, "%d ", errno);
		perror("Error mmap");
		exit(1);
	}

	mlockall(MCL_CURRENT | MCL_FUTURE);

	clock_gettime(CLOCK_MONOTONIC, &t);

	register char *a1 = addr + (addr1 % MEM_SIZE), *a2 = addr + (addr2 % MEM_SIZE);

	if(fill_cache(addr, a1, a2) != 0) {
		perror("Error fill cache");
		exit(1);
	}

	t.tv_sec = 0; t.tv_nsec = 0;

	sched_yield();

	time_to_mem(a1, a2, &t);

	printf("%lu", t.tv_nsec + t.tv_sec * 1000000000UL);
	printf(",%lu,%lu", (unsigned long) a1 % MEM_SIZE, (unsigned long) a2 % MEM_SIZE);
	//printf(",%d", ((unsigned long) a1 & BANK_MASK) == ((unsigned long) a2 & BANK_MASK) ? 1 : 0);
	printf("\n");

	return 0;
}
