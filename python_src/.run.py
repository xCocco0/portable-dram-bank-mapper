
from matplotlib import pyplot as plt
import numpy as np
import pandas as pd
import itertools
import time
import math

from python_src.rref import *
from python_src.bit_operations import *

infilename = "logrpi_user_merge3.txt"

n_banks = 8

min_iterations = 10
max_iterations = 20

max_literals_per_bit = 2
bank_bits = 5
bit_min = 6
bit_max = 20
#"./mem2.csv"

#log3.txt 0.94
#logfp4.txt 0.82
#logfp4_long.txt 0.7
#logsandy.txt 0.92

target_n_cores = 4
prob_mem = 0.5

interf_prob = 1 - (1 - prob_mem/n_banks)**target_n_cores

custom_treshold = None

def uncertainty_score(ratio, param):
    """
    Returns
    ------
                    1
    1 - -------------------------
         1 + (log_param(ratio))^2

    """
    return 1 - (1 / (1 + (np.log(ratio)/np.log(param))**2))


def bank(addr):
    #return (addr & 0x7800) >> 11
    #return (addr & 0x78000) >> 15
    return bank_from_bits(addr, [14,13,12,11])


def plothist(bitmask):
    
    global df
    
    def nbins(d):
        step = 10**(int(np.log10(d.mean()))-1)
        #return int((d.max()-d.min())/step)
        return range(int(d.min()/step)*step, d.max() + step, step)

    tmp1 = df[1].apply(bank_from_bitmasks, args = [bitmask])
    tmp2 = df[2].apply(bank_from_bitmasks, args = [bitmask])
    df_sb = df[0].where(tmp1 == tmp2).dropna().to_numpy(dtype=int)
    #df_db = df[0].where(tmp1 != tmp2).dropna().to_numpy(dtype=int)

    fig, ax = plt.subplots()
    
    ax.hist(df[0], bins = nbins(df[0]))
    ax.hist(df_sb, bins = nbins(df_sb))

    plt.show()



#----[ Read files ] ----#

df = pd.read_csv(infilename, dtype = int, header = None)

df = df[df[0] <= 10 * df[0].mean()]

#df_sb = df[0].where(df["bank1"] == df["bank2"]).dropna().to_numpy(dtype=int)
#df_db = df[0].where(df["bank1"] != df["bank2"]).dropna().to_numpy(dtype=int)

if custom_treshold:
    treshold = custom_treshold
else:
    treshold = df[0].sort_values().iloc[int(df.shape[0] * (1 - 1/n_banks) * (1 - interf_prob))]

mask = (df[0] >= treshold)

single_ranking = list()

"""
for n in range(3,5):
    for mask in itertools.combinations(range(2**6, 2**30), n):
"""



#----[ Test single bit functions ] ----#

iterations = sum(math.comb(bit_max - bit_min + 1, i+1) for i in range(max_literals_per_bit))
start_time = time.time()
i = 0

for nl in range(max_literals_per_bit):
    for bitlist in itertools.combinations(range(bit_min, bit_max + 1), nl + 1):

        bitmask = 0
        for n in bitlist:
            bitmask |= (1<<n)

        tmp1 = df[mask][1].apply(bank_from_bitmasks, args = [[bitmask]])
        tmp2 = df[mask][2].apply(bank_from_bitmasks, args = [[bitmask]])
        df_sb = df[0][mask][tmp1 == tmp2].dropna().to_numpy(dtype=int)
        df_db = df[0][mask][tmp1 != tmp2].dropna().to_numpy(dtype=int)

        score = df_sb.size# * (1.5 ** n)
        if np.random.random() < 0:
            print("mask", bitmask, "\t score", score)
        single_ranking.append([bitmask, score])
        
        i += 1
        if not i % 100:
            elapsed_time = time.time() - start_time
            remaining_time = (elapsed_time/i)*(iterations-i)
            print(f"{i:6d}/{iterations}\tElapsed: {elapsed_time:6.0f}s, Remaining: {remaining_time:6.0f}s", end = "\r")

print()



#----[ Create a ranking of best functions ] ----#

single_ranking = sorted(single_ranking, key = lambda x: x[1], reverse = True)

min_iterations = min(min_iterations, len(single_ranking))
min_iterations = min(max_iterations, len(single_ranking))

perc_tr = max(j for i,j in single_ranking[1:])*0
max_index = 1 + max(i for i in range(len(single_ranking)) if single_ranking[i][1] >= perc_tr)
max_index = max(min_iterations, max_index)
max_index = min(max_iterations, max_index)

single_ranking = single_ranking[:max_index*(max_literals_per_bit+1)]
"""
i = 0
while i < len(single_ranking) and i < 10:
    j = i
    while j < len(single_ranking) and j < 10:
        # i is better than j
        # if lit(i) subset lit(j)
        print("at", i, j)
        if (single_ranking[i][0] & single_ranking[j][0]) == single_ranking[i][0] and i != j:
            print(single_ranking[i][0], single_ranking[j][0], "discard")
            single_ranking.pop(j)
        else:
            print(single_ranking[i][0], single_ranking[j][0], "keep")
            j += 1
    i += 1
"""

to_remove = set()
for i in range(len(single_ranking)):
    for j in range(i, len(single_ranking)):
        if (single_ranking[i][0] & single_ranking[j][0]) == single_ranking[i][0] and i != j:
            to_remove.add(j)
for i in sorted(to_remove, reverse = True):
    single_ranking.pop(i)
        
single_ranking = single_ranking[:max_index]

print("Bit functions to test:")
for fn,sc in single_ranking:
    print(f"{bitmasks_to_readable([fn]):36s}", sc)

ranking_by_pivot = { i : list() for i in range(bit_min, bit_max + 1) }

for fn, sc in single_ranking:
    ranking_by_pivot[int(np.log2(fn))].append(fn)

single_ranking_df = pd.DataFrame((
        [fn,
        sc,
        (df[1].apply(bank_from_bitmasks, args = [[fn]]) == df[2].apply(bank_from_bitmasks, args = [[fn]])).to_numpy(dtype = bool)]
        for fn, sc in single_ranking),
        columns = ["fn", "score", "equal"])



#----[ Combine the single bit functions ] ----#

ranking = list()

#iterations = sum(len(list(compose_rref(ranking_by_pivot, nb+1, (bit_min, bit_max)))) for nb in range(bank_bits))
#iterations = sum(len(list(compose_rref_byindex(single_ranking_df, nb+1))) for nb in range(bank_bits))
iterations = 0
for nb in range(bank_bits):
    for bitmasks, fn_indices in compose_rref_byindex(single_ranking_df, nb+1):
        iterations += 1

start_time = time.time()
i = 0

for nb in range(bank_bits):
    for bitmasks, fn_indices in compose_rref_byindex(single_ranking_df, nb+1):
        """
        for fn_tuples in itertools.combinations(single_ranking_df[["fn","equal"]].itertuples(), nb + 1):
        for bitmasks in compose_rref(ranking_by_pivot, nb+1, (bit_min, bit_max)):
        for bitmasks in itertools.combinations((fn for fn, sc in single_ranking), nb + 1):
        """

        i += 1
        if not i % 100:
            elapsed_time = time.time() - start_time
            remaining_time = (elapsed_time/i)*(iterations-i)
            print(f"{i:6d}/{iterations}\tElapsed: {elapsed_time:6.0f}s, Remaining: {remaining_time:6.0f}s", end = "\r")
        
        """
        rref = rref_bitmasks(bitmasks)[0]
        #print("/ rref:", bitmasks_to_readable(rref))
        if not np.array_equal(sorted(bitmasks, reverse = True), rref):
            #print("discarded:", bitmasks_to_readable(bitmasks))
            continue
        #print("ok:", bitmasks_to_readable(bitmasks))
        """
        bits_used = sum(1 for j in bitmasks if j != 0)
        """      
        tmp1 = df[1].apply(bank_from_bitmasks, args = [bitmasks])
        tmp2 = df[2].apply(bank_from_bitmasks, args = [bitmasks])

        df_sb = df[0][tmp1 == tmp2].dropna()
        df_db = df[0][tmp1 != tmp2].dropna()

        uncertainty = (2**bits_used)*df_sb.shape[0]/df.shape[0]

        df_sb = df_sb[mask]
        df_db = df_db[mask]

        """

        sb_mask = (sum(single_ranking_df.loc[list(fn_indices)]["equal"]) == bank_bits)
        df_sb = df[0][sb_mask]
        df_db = df[0][~sb_mask]
        uncertainty = (2**bits_used)*df_sb.shape[0]/df.shape[0]
        #uncertainty = 1
        df_sb = df[mask & sb_mask]
        df_db = df[mask & ~sb_mask]
        
        score = df_sb.shape[0] * (2**bits_used)
        #score = df_sb.shape[0]

        if np.random.random() < 0:
            print("mask", bitmasks, "\t score", score)

        ranking.append([bitmasks, score, uncertainty]) #uncertainty_score(uncertainty, 1.25)])


print()

ranking = sorted(ranking, key = lambda x: x[1], reverse = True)

print("Final functions scores: (top 100)")
i = 1
for fn, sc, uncrt in ranking[:100]:
    print(f"{i:3d}: {bitmasks_to_readable(fn):55s} \t {sc:4.2f} \t {uncrt:2.2f} \t {uncertainty_score(uncrt, 1.17):1.3f}")
    i += 1
