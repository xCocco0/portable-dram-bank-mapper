
CFLAGS=-Wall -Og -O0 -g

TARGETS=mem_delay mem_delay_verify mem_delay_bydiff merge_logs

DIR=benchmark_src


SRC=mem_delay_utilities.c
INC=mem_delay_utilities.c mem_delay_config.h

SRC:=$(addprefix $(DIR)/,$(SRC))
INC:=$(addprefix $(DIR)/,$(INC))

all: $(TARGETS)

mem_delay: $(DIR)/mem_delay.c $(SRC) $(INC) Makefile
	gcc -o $@ $(filter %.c, $^) $(CFLAGS)

mem_delay_verify: $(DIR)/mem_delay_verify.c $(SRC) $(INC) Makefile
	gcc -o $@ $(filter %.c, $^) $(CFLAGS)

mem_delay_bydiff: $(DIR)/mem_delay_bydiff.c $(SRC) $(INC) Makefile
	gcc -o $@ $(filter %.c, $^) $(CFLAGS)

merge_logs: $(DIR)/merge_logs.c
	gcc -o $@ $< $(CFLAGS)
clean:
	rm -f $(TARGETS)

.PHONY: clean
