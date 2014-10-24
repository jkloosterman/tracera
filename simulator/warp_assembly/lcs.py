#!/usr/bin/python

# Least common substring from http://rosettacode.org/wiki/Longest_common_subsequence#Python.
# An easy optimization would be to make the x == y case greedier and take long
#  common subsequences.
def lcs(xstr, ystr):
    if not xstr or not ystr:
        return []
    x, xs, y, ys = xstr[0], xstr[1:], ystr[0], ystr[1:]
    if x == y:
        return [x] + lcs(xs, ys)
    else:
        return max(lcs(xstr, ys), lcs(xs, ystr), key=len)

# A dynamic programming approach.
# My guess: this won't work as well, because 
def lcs_dynamic_programming(a, b):
    lengths = [[0 for j in range(len(b)+1)] for i in range(len(a)+1)]
    # row 0 and column 0 are initialized to 0 already
    for i, x in enumerate(a):
        for j, y in enumerate(b):
            if x == y:
                lengths[i+1][j+1] = lengths[i][j] + 1
            else:
                lengths[i+1][j+1] = \
                    max(lengths[i+1][j], lengths[i][j+1])
    # read the substring out from the matrix
    result = ""
    x, y = len(a), len(b)
    while x != 0 and y != 0:
        if lengths[x][y] == lengths[x-1][y]:
            x -= 1
        elif lengths[x][y] == lengths[x][y-1]:
            y -= 1
        else:
            assert a[x-1] == b[y-1]
            result = a[x-1] + result
            x -= 1
            y -= 1
    return result

subsequence_cache = {}

def subsequence(traces):
    if len(traces) == 1:
        return traces[0]
    if len(traces) == 2:
        return lcs(traces[0], traces[1])

    cur_subsequence = lcs(traces[0], traces[1])
    for i in range(1, len(traces)):
        cur_subsequence = lcs(cur_subsequence, traces[i])
    return cur_subsequence

def warps_from_subsequence(common_subsequence, traces):
    s_idx = 0
    idxs = [0 for x in traces]
    rows = []

    while s_idx < len(common_subsequence):
#        print "s_idx %d, len_cs %d" % (s_idx, len(common_subsequence))
        row = [-1 for x in traces]

        divergent_choice = -1
        for i in range(len(traces)):
            if traces[i][idxs[i]] != common_subsequence[s_idx]:
                if divergent_choice == -1 or divergent_choice == traces[i][idxs[i]]:
                    divergent_choice = traces[i][idxs[i]]
                    row[i] = traces[i][idxs[i]]
                    idxs[i] += 1

        if divergent_choice == -1:
            for i in range(len(traces)):
                row[i] = traces[i][idxs[i]]
                idxs[i] += 1
            s_idx += 1

#        print "CS Row:", row
        rows.append(row)

    # At this point, the common subsequence is finished.
    # However, there might still be elements left in
    # some of the traces, and they might be common.
    # Strategy: start with the elements of the first one, see if there are matches
    #  in the others; coalesce if possible.
    remaining_rows = False
    for i in range(len(traces)):
        if idxs[i] < len(traces[i]):
            remaining_rows = True
        
    while remaining_rows:
        row = [-1 for x in traces]
        divergent_choice = -1

        for i in range(len(traces)):
            if idxs[i] < len(traces[i]):
                if divergent_choice == -1 or divergent_choice == traces[i][idxs[i]]:
                    divergent_choice = traces[i][idxs[i]]
                    row[i] = traces[i][idxs[i]]
                    idxs[i] += 1

#        print "Rem Row:", row
        rows.append(row)
        
        remaining_rows = False
        for i in range(len(traces)):
            if idxs[i] < len(traces[i]):
                remaining_rows = True

    return rows

def merge_traces(traces):
    trace_subsequence = subsequence(traces)
#    print "subsequence: ", trace_subsequence

    merged = warps_from_subsequence(trace_subsequence, traces)
#    print "Merged: ", merged

    return merged

# trace_a = [1,2,3,4]
# trace_b = [1,3,3,4]
# trace_c = [1,2,3,4]
# merge_traces([trace_a, trace_b, trace_c])

