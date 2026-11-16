# ADS Project 5 — Huffman Codes

huffman.c is the submission program, written in C99. It verifies symbol coverage, binary codes, minimum weighted length and the prefix property.

## Build

    gcc -std=c99 -O2 huffman.c -o huffman.exe

The default is the compact Trie. Select a comparison build with one macro.

| Macro | Prefix checker | Worst-case checking time |
|---|---|---|
| none | Trie with 16-bit child indices | O(S) |
| -DPAIRWISE | Pairwise string comparisons | O(N² L) |
| -DINTERVAL | Packed dyadic intervals with qsort | O(S + N log N) |
| -DPACKED | Pairwise integer interval overlap | O(S + N²) |
| -DSORTED | Sorted insertion with neighbor checks | O(S + N²) |

S is the total code length and L is the longest code. All variants share minimum-cost calculation and input validation. Input follows the PTA statement, including at most 63 symbols and 63 bits per code.

## Verification

Python 3.10+ and GCC on PATH are required.

    python test_huffman.py
    python test_mutations.py

The correctness suite checks all five builds on 144 input files containing 5,088 submissions. It includes the official example, exhaustive small codebooks, an independent subset oracle, a non-Huffman optimal tree, maximum-size batches, zero weights, long codes, equivalent transformations and malformed submission rows. The mutation runner checks two additional witnesses against all five builds, then requires each of ten targeted incorrect programs to produce an output mismatch. mutation_results.csv records the first counterexample.

Static analysis command, also run with each comparison macro:

    gcc -std=c99 -O2 -Wall -Wextra -Werror -pedantic -fanalyzer -fsyntax-only huffman.c

## Measurements

    python test_huffman.py --benchmark
    python benchmark_prefix.py

benchmark.csv contains whole-program median times, including startup and I/O. prefix_benchmark.csv contains median/minimum/maximum batch-mean nanoseconds per prefix check. Its C harness uses Windows QueryPerformanceCounter and times 20,000 calls after 100 warm-ups, over seven batches. It covers six input shapes at N=8,32,63. Both drivers rotate variant order and verify answers.

## Report

report.pdf is the rendered report. report.tex is its editable source.

    pdflatex -interaction=nonstopmode -halt-on-error report.tex

Measured rankings depend on input shape and environment. Insertion sorting benefits already ordered intervals, while early conflicts favor immediate rejection. The default Trie retains its linear checking bound.
