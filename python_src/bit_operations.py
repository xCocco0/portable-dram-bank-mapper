
import numpy as np

def bank_from_bits(addr, bits):
    res = 0
    for b in bits:
        res <<= 1
        res |= (addr >> b) & 0x1
    return res

def bank_from_bitmasks(addr, masks):
    res = 0
    for m in masks:
        res <<= 1
        v = addr & m
        # The following will xor all the bits in v
        # Adapted from https://graphics.stanford.edu/~seander/bithacks.html#CountBitsSetKernighan
        while v:
            v &= v - 1
            res ^= 1
    return res

def bitmasks_to_readable(masks):

    out = ""
    for mask in masks:

        if out != "":
            out += ", "

        literals = 0
        for i in range(54,-1,-1):
            if mask & (1 << i):
                if literals > 0:
                    out += "^"
                out += f"{i}"
                literals += 1
    return out

def bitmasks_to_matrix(masks, n = None):
    
    if n is None:
        n = 1+int(np.floor(np.log2(max(masks))))
    return np.array([[
            ((masks[j] >> i) & 1)
                for i in range(n-1, -1, -1)]
                for j in range(len(masks))
            ], dtype = np.int8)

def sum_ones(x):
    n = 0
    while x:
        x &= x - 1
        n += 1
    return n

def explore_functions(masks, max_recursion, count = None):

    if count is None:
        count = int((max_recursion**2)/2)

    masks = np.array(masks, dtype = np.int64)
    ncols = 1 + int(np.log2(masks).max())
    nrows = masks.shape[0]

    out = {tuple(masks)}

    def swap_row(masks,i,j):
        masks[[i,j]] = masks[[j,i]]
    def sum_row_to(masks,i,rows):
        masks[rows] ^= masks[i]
    def neg_row(masks,i):
        masks[i] = ~masks[i] & (( 1 << ncols ) - 1)

    old_nodes = {tuple(masks)}
    new_nodes = set()
    out = set()

    for i in range(max_recursion):

        for m in old_nodes:

            m = np.array(m)

            for choice in range(nrows + nrows*(nrows-1)):
            # nrows + nrows*(nrows-1) choices

                if choice < nrows:
                    # self xor
                    
                    source_row = choice
                    neg_row(m, source_row)

                else:

                    choice -= nrows
                    # choice = choice1 * (nrows-1) + choice2 < nrows * (nrows-1)
                    choice2 = choice % (nrows-1)              # 0 ~ nrows-2
                    choice1 = int((choice - choice2)/nrows)   # 0 ~ nrows-1

                    source_row = choice1
                    if choice2 >= source_row:
                        target_row = choice2 + 1
                    else:
                        target_row = choice2

                    sum_row_to(m, source_row, target_row)
                
                m.sort()
                new_nodes.add(tuple(m))

        out = out.union(new_nodes)
        old_nodes = new_nodes
        new_nodes = set()

    return sorted(out, key = lambda t: sum(sum_ones(v) for v in t))



def compose_rref(best, max_rows, levels: tuple):

    def __compose_rref_recursive(rows, best, max_rows, levelmin, level):
        # rows = (1<<13, 1<<12|1<<11...)
        if len(rows) == max_rows:
            #print(bitmasks_to_readable(rows))
            yield rows
            return
        while level > levelmin:
            if all( ((r >> (level-1)) & 1) == 0 for r in rows):
                for r in best[level-1]:
                    if 1:
                        for n in __compose_rref_recursive((*rows, r), best, max_rows, levelmin, level-1):
                            yield n
            level -= 1
    levelmin, levelmax = levels
    return __compose_rref_recursive((), best, max_rows, levelmin, levelmax)


def compose_rref_byindex(ranking, max_rows):

    #bit_min = int(np.log2(ranking["fn"].min()))
    #bit_max = int(np.log2(ranking["fn"].max()))

    ranking_by_pivot = list(ranking.groupby(ranking["fn"].apply(lambda x: int(np.log2(x)))))

    def __compose_rref_byindex_recursive(rows, rowindices, best, max_rows, i):
        # rows = (1<<13, 1<<12|1<<11...)
        if len(rows) == max_rows:
            #print(bitmasks_to_readable(rows))
            yield rows, rowindices
            return
        while i > 0:
            lv, rows_df = best[i-1]
            if all( ((r >> lv) & 1) == 0 for r in rows):
                for ind, r_df in rows_df.iterrows():
                    if 1:
                        for n in __compose_rref_byindex_recursive((*rows, r_df["fn"]), (*rowindices, ind), best, max_rows, i-1):
                            yield n
            i -= 1

    return __compose_rref_byindex_recursive((), (), ranking_by_pivot, max_rows, len(ranking_by_pivot))







