
import argparse
import numpy as np
from python_src.classify import *

parser = argparse.ArgumentParser()
parser.add_argument("logfile", help = "the log file to read")
parser.add_argument("-m", "--min_iterations", type = int, default = 20, help = "minimum number of single bit functions to combine (default=20)")
parser.add_argument("-M", "--max_iterations", type = int, default = 70, help = "maximum number of single bit functions to combine (default=70)")
parser.add_argument("-B", "--n_banks", type = int, default = 8, help = "number of the banks in the target DRAM")
parser.add_argument("-R", "--max_literals_per_bit", type = int, default = 5, help = "maximum number of literals in a single bit function")
parser.add_argument("-l", "--bit_min", type = int, default = 6, help = "lower address bit to use inside single bit functions")
parser.add_argument("-L", "--bit_max", type = int, default = 20, help = "higher address bit to use inside single bit functions")
parser.add_argument("-N", "--target_n_cores", type = int, help = "number of cores of the target architecture (only used for computing the treshold)")
parser.add_argument("-U", "--mem_usage", type = float, help = "a number between 0 to 1 representing the average memory load of the other CPU cores (only used for computing the treshold)")
parser.add_argument("-C", "--custom_treshold", type = float, help = "custom treshold for diving same bank memory access time from different bank accesses. If this parameter is set, target_n_cores and mem_usages parameters are ignored")

args = parser.parse_args()

bank_bits = int(np.log2(args.n_banks))

df, longdelay, treshold = read_log(args.logfile, args.n_banks, args.mem_usage, args.target_n_cores, args.custom_treshold)

single_ranking = score_single_bits_fn(df, longdelay, args.max_literals_per_bit, args.bit_min, args.bit_max)

ranking = score_combined_fn(df, longdelay, single_ranking, args.n_banks, args.min_iterations, args.max_iterations, args.max_literals_per_bit, args.bit_min, args.bit_max)

print("Final functions scores: (top 100)")
i = 1
for fn, sc, uncrt in ranking[:100]:
    print(f"{i:3d}: {bitmasks_to_readable(fn):55s} \t {sc:4.2f} \t {uncrt:2.2f}") # \t {uncertainty_score(uncrt, 1.17):1.3f}")
    i += 1
