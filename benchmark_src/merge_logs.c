
#include <stdio.h>
#include <stdlib.h>

#define MAX_LINE_SZ 128

#define MIN(x,y) (x > y ? y : x)

int main(int argc, char* argv[])
{
	if(argc < 3) {
		fprintf(stderr, "Error: missing operand\n");
		fprintf(stderr, "Usage: %20s <file1> <file2>\n", argv[0]);
		exit(1);
	}

	FILE* f1 = fopen(argv[1], "r");
	FILE* f2 = fopen(argv[2], "r");

	char line1[MAX_LINE_SZ], line2[MAX_LINE_SZ];
	int delay1, delay2;
	unsigned long a11, a21, a12, a22;

	while (fgets(line1, MAX_LINE_SZ, f1) && fgets(line2, MAX_LINE_SZ, f2))
	{
		sscanf(line1, "%d,%lu,%lu", &delay1, &a11, &a21);
		sscanf(line2, "%d,%lu,%lu", &delay2, &a12, &a22);
		
		if(a11 != a12 || a21 != a22) {
			fprintf(stderr, "Parsing error\n");
			fprintf(stderr, "%lu,%lu,%lu,%lu\n", a11, a21, a12, a22);
			exit(1);
		}

		printf("%d,%lu,%lu\n", MIN(delay1, delay2), a11, a21);
	}

	return 0;
}
