
from matplotlib import pyplot as plt
import numpy as np
import pandas as pd
import itertools
import time
import math

from python_src.rref import *
from python_src.bit_operations import *
from python_src.progressbar import *


def uncertainty_score(ratio, param):
    """
    Returns
    ------
                    1
    1 - -------------------------
         1 + (log_param(ratio))^2

    """
    if ratio == 0:
        return 1
    else:
        return 1 - (1 / (1 + (np.log(ratio)/np.log(param))**2))


def plothist(df, bitmask):
    
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

    return fig, ax


def plottreshold(df, treshold):
    
    def nbins(d):
        step = 10**(int(np.log10(d.mean()))-1)
        #return int((d.max()-d.min())/step)
        ret = list(range(int(d.min()/step)*step, d.max() + step, step))
        ret.append(treshold)
        ret.sort()
        return ret

    fig, ax = plt.subplots()
    
    ax.axvline(x = treshold, color="grey", linewidth=1.5)
    ax.hist(df[0][df[0] < treshold], bins = nbins(df[0]), color = "b")
    ax.hist(df[0][df[0] >= treshold], bins = nbins(df[0]), color = "r")

    plt.show()

    return fig, ax


#----[ Read files ] ----#

def read_log(filename, n_banks, mem_usage, target_n_cores, custom_treshold = None):

    df = pd.read_csv(filename, dtype = int, header = None)

    df = df[df[0] <= 10 * df[0].mean()]

    #df_sb = df[0].where(df["bank1"] == df["bank2"]).dropna().to_numpy(dtype=int)
    #df_db = df[0].where(df["bank1"] != df["bank2"]).dropna().to_numpy(dtype=int)


    if custom_treshold:
        treshold = custom_treshold
    else:
        interf_prob = 1 - (1 - mem_usage/n_banks)**target_n_cores
        treshold = df[0].sort_values().iloc[int(df.shape[0] * (1 - 1/n_banks) * (1 - interf_prob))]

    longdelay = (df[0] >= treshold)

    return df, longdelay, treshold


#----[ Test single bit functions ] ----#

def score_single_bits_fn(df, longdelay, max_literals_per_bit, bit_min, bit_max):

    single_ranking = list()

    iterations = sum(math.comb(bit_max - bit_min + 1, i+1) for i in range(max_literals_per_bit))
    pb = ProgressBar(iterations, 0.2)

    for nl in range(1, max_literals_per_bit + 1):
        for bitlist in itertools.combinations(range(bit_min, bit_max + 1), nl):

            bitmask = 0
            for n in bitlist:
                bitmask |= (1<<n)

            tmp1 = df[longdelay][1].apply(bank_from_bitmasks, args = [[bitmask]])
            tmp2 = df[longdelay][2].apply(bank_from_bitmasks, args = [[bitmask]])
            df_sb = df[0][longdelay][tmp1 == tmp2].dropna().to_numpy(dtype=int)
            df_db = df[0][longdelay][tmp1 != tmp2].dropna().to_numpy(dtype=int)

            score = df_sb.size# * (1.5 ** n)
            if np.random.random() < 0:
                print("mask", bitmask, "\t score", score)
            single_ranking.append([bitmask, score])
            
            pb.progress()

    return sorted(single_ranking, key = lambda x: x[1], reverse = True)



#----[ Create a ranking of best functions ] ----#

def score_combined_fn(df, longdelay, single_ranking, n_banks, min_iterations, max_iterations, max_literals_per_bit, bit_min, bit_max):

    bank_bits = int(np.log2(n_banks))

    min_iterations = min(min_iterations, len(single_ranking))
    min_iterations = min(max_iterations, len(single_ranking))

    prune_perc = 0 # keep values that are greater than best_perc% of the best values
    perc_tr = max(j for i,j in single_ranking[1:])*prune_perc
    max_index = 1 + max(i for i in range(len(single_ranking)) if single_ranking[i][1] >= perc_tr)
    max_index = max(min_iterations, max_index)
    max_index = min(max_iterations, max_index)

    single_ranking = single_ranking[:max_index*(max_literals_per_bit+1)]

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

    ranking = list()

    #iterations = sum(len(list(compose_rref(ranking_by_pivot, nb+1, (bit_min, bit_max)))) for nb in range(bank_bits))
    #iterations = sum(len(list(compose_rref_byindex(single_ranking_df, nb+1))) for nb in range(bank_bits))
    iterations = 0
    for nb in range(bank_bits-1, bank_bits):
        for bitmasks, fn_indices in compose_rref_byindex(single_ranking_df, nb+1):
            iterations += 1

    pb = ProgressBar(iterations, 0.2)
    
    for nb in range(bank_bits-1, bank_bits): #range(0, bank_bits) # to try less than bank_bits
        for bitmasks, fn_indices in compose_rref_byindex(single_ranking_df, nb+1):
            """
            for fn_tuples in itertools.combinations(single_ranking_df[["fn","equal"]].itertuples(), nb + 1):
            for bitmasks in compose_rref(ranking_by_pivot, nb+1, (bit_min, bit_max)):
            for bitmasks in itertools.combinations((fn for fn, sc in single_ranking), nb + 1):
            """
            
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
            df_sb = df[longdelay & sb_mask]
            df_db = df[longdelay & ~sb_mask]
            
            #score = df_sb.shape[0] * (2**bits_used)
            score = df_sb.shape[0]

            if np.random.random() < 0:
                print("mask", bitmasks, "\t score", score)

            ranking.append([bitmasks, score, uncertainty]) #uncertainty_score(uncertainty, 1.25)])

            pb.progress()

    return sorted(ranking, key = lambda x: x[1], reverse = True)



