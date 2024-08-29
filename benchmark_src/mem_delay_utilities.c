
#include "mem_delay_utilities.h"

#include <stdio.h>
#include <stdlib.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/mman.h>
#include <errno.h>

#if defined(__x86_64__) || defined(_M_X64)
#define MEM_BARRIER() asm volatile ("mfence\n\t" "cpuid" ::: "eax", "ebx", "ecx", "edx", "memory")
#elif defined(__arm__) || defined(__aarch64__)
#define MEM_BARRIER() asm volatile ("dsb sy" ::: "memory")
#else
#error Architecture not supported
#endif    

#define READ(value) asm volatile ("" : : "g"(value))

#if defined(__x86_64__) || defined(_M_X64)
#define GETTIME(t) do {\
	t.tv_sec = 0;\
	t.tv_nsec = 0;\
	asm volatile("rdtsc" : "=a"(t.tv_nsec) :: "edx"); \
} while(0);
#else
#define GETTIME(t) clock_gettime(CLOCK_MONOTONIC_RAW, &t)
#endif    

#define CACHE_SETS ((CACHE_SIZE)/(CACHE_LINE_BYTES*CACHE_WAYS))

#define MULT 2 // safe factor for victim cache etc

#define SIZE1GB (1<<30)
#define SIZE2MB (1<<21)


void printbin(size_t addr, int size)
{
	printf("0b");
	for(int i = 0; i < size; ++i) {
		
		if(addr & (1 << (size - i - 1))) printf("1");
		else printf("0");
		if((size - i - 1) % 4 == 0) printf(" ");
	}
	printf("\n");
}

void diff_timespec(struct timespec *out, const struct timespec *time1, const struct timespec *time0)
{
	out->tv_sec = time1->tv_sec - time0->tv_sec;
	out->tv_nsec = time1->tv_nsec - time0->tv_nsec;

	if (out->tv_nsec < 0) {
		out->tv_nsec += 1000000000UL; // nsec/sec
		out->tv_sec--;
	}
}

void time_to_mem(const char *ptr1, const char *ptr2, struct timespec *delta)
{
	struct timespec t1, t2;
	const volatile register int *p1 = (int *) ptr1;
	const volatile register int *p2 = (int *) ptr2;

	GETTIME(t1); // populate icache for clock_gettime

	MEM_BARRIER();
	GETTIME(t1);
	
	READ(*p1);
	READ(*p2);

	MEM_BARRIER();
	GETTIME(t2);
	
	diff_timespec(delta, &t2, &t1);

	(void) p1;
	(void) p2;
}


static inline int fill_cache_reuse1gbpage(char *base, char *addr1, char *addr2)
{
	/* fill all the cache sets
	 * fill all the tags that do not conflict with avoid1 and avoid2 */

	const unsigned long avoid1 = (unsigned long) addr1, avoid2 = (unsigned long) addr2;
	
	unsigned long ptr;

	for(int s = 0; s < CACHE_SETS; ++s)
	{
		for(int w = 0; w < CACHE_WAYS * MULT; ++w)
		{
			ptr = (s * CACHE_LINE_BYTES) \
				+ (w * CACHE_LINE_BYTES * CACHE_SETS) \
				+ (~avoid1 & (1<<28)) \
				+ (~avoid2 & (1<<29));
			
			//printbin(ptr, 35);
			READ(ptr);
			
		}
		
	}

	//printbin(avoid1, 35);
	//printbin(avoid2, 35);

	return 0;
}

static inline int fill_cache_alloc2mbpages(void)
{
	const size_t mem_size = ( (CACHE_SIZE*MULT - 1) / SIZE2MB + 1) * SIZE2MB;

	char * addr = mmap(NULL, mem_size, PROT_READ | PROT_WRITE,
		MAP_PRIVATE | MAP_ANONYMOUS | MAP_POPULATE | MAP_HUGETLB, -1, 0);
	if(addr == (char*) -1) {
		return 1;
	}

	for(size_t i = 0; i < mem_size; ++i) {
		READ(addr[i]);
	}

	return 0;
}

static inline int fill_cache_generic(void)
{
	const size_t mem_size = ( (CACHE_SIZE*MULT*2 - 1) / SIZE2MB + 1) * SIZE2MB;

	char * addr = mmap(NULL, mem_size, PROT_READ | PROT_WRITE,
		MAP_PRIVATE | MAP_ANONYMOUS | MAP_POPULATE, -1, 0);
	if(addr == (char*) -1) {
		return 1;
	}

	for(size_t i = 0; i < mem_size; ++i) {
		READ(addr[i]);
	}

	return 0;
}

void* virt2phy(void *vaddr)
{
	char pagemap_filename[128];
	int pagemap_fd;
	size_t nread;
	ssize_t ret;
	uint64_t data;
	unsigned long vpn, pfn, paddr;

	snprintf(pagemap_filename, sizeof(pagemap_filename), "/proc/%lu/pagemap", (uintmax_t) getpid());
	pagemap_fd = open(pagemap_filename, O_RDONLY);
	if (pagemap_fd < 0) {
		return NULL;
	}

	vpn = (unsigned long) vaddr / sysconf(_SC_PAGE_SIZE);

	nread = 0;
	while (nread < sizeof(data)) {
		ret = pread(pagemap_fd, ((uint8_t*)&data) + nread, sizeof(data) - nread,
				vpn * sizeof(data) + nread);
		nread += ret;
		if (ret <= 0) {
			return NULL;
		}
	}

	pfn = data & ((1UL << 55) - 1);
	if(pfn == 0) {
		return NULL;
	}
	//soft_dirty = (data >> 55) & 1;
	//file_page = (data >> 61) & 1;
	//swapped = (data >> 62) & 1;
	//present = (data >> 63) & 1;
	
	close(pagemap_fd);

	paddr = (pfn * sysconf(_SC_PAGE_SIZE)) + ((unsigned long) vaddr % sysconf(_SC_PAGE_SIZE));

	return (void *) paddr;

}

int fill_cache(char *base, char *addr1, char *addr2)
{
#if defined(__x86_64__) || defined(_M_X64)
	asm volatile ("clflush (%0)" :: "r"(addr1));
	asm volatile ("clflush (%0)" :: "r"(addr2));
	return 0;
#else

#if HAS_1GB_HUGEPAGES
	return fill_cache_reuse1gbpage(base, addr1, addr2);
#elif HAS_2MB_HUGEPAGES
	return fill_cache_alloc2mbpages();
#else
	return fill_cache_generic();
#endif

#endif
}

char * get_mem_chunk(void)
{
	char *addr = NULL;
#if HAS_1GB_HUGEPAGES == 1 || HAS_1GB_HUGEPAGES == 1
	addr = mmap(NULL, MEM_SIZE, PROT_READ | PROT_WRITE,
		MAP_PRIVATE | MAP_ANONYMOUS | MAP_POPULATE | MAP_HUGETLB, -1, 0);
	if(addr == (char *) -1) {
		fprintf(stderr, "%d ", errno);
		perror("Error mmap");
		exit(1);
	}
#else
	addr = (char *) malloc(MEM_SIZE);
#endif

	return addr;
}
