import csv
import functools
import heapq
import itertools
import os
from pathlib import Path
import random
import statistics
import string
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parent
VARIANTS = ["trie", "pairwise", "interval", "packed", "sorted"]
SYMBOLS = string.digits + string.ascii_lowercase + string.ascii_uppercase + "_"


def encode(weights, entries):
    symbols = SYMBOLS[:len(weights)]
    header = " ".join(f"{c} {w}" for c, w in zip(symbols, weights))
    return f"{len(weights)}\n{header}\n{len(entries)}\n" + "".join(
        "".join(f"{c} {code}\n" for c, code in submission)
        for submission in entries
    )


def reference_codes(weights):
    heap = [(w, i, {SYMBOLS[i]: ""}) for i, w in enumerate(weights)]
    heapq.heapify(heap)
    for i in range(len(weights) - 1):
        wa, _, a = heapq.heappop(heap)
        wb, _, b = heapq.heappop(heap)
        merged = {c: "0" + s for c, s in a.items()}
        merged.update({c: "1" + s for c, s in b.items()})
        heapq.heappush(heap, (wa + wb, len(weights) + i, merged))
    return list(heap[0][2].items())


def exhaustive_cost(weights):
    # Enumerate every unordered root partition of each leaf subset.
    @functools.lru_cache(None)
    def cost(mask):
        if mask.bit_count() == 1:
            return 0
        weight = sum(w for i, w in enumerate(weights) if mask >> i & 1)
        first = mask & -mask
        best = float("inf")
        part = (mask - 1) & mask
        while part:
            if part & first:
                best = min(best, cost(part) + cost(mask ^ part))
            part = (part - 1) & mask
        return weight + best
    return cost((1 << len(weights)) - 1)


def expected(weights, submission):
    code_map = dict(submission)
    if len(code_map) != len(weights) or set(code_map) != set(SYMBOLS[:len(weights)]):
        return "No"
    # In lexical order a prefix conflict must occur at an adjacent pair.
    ordered = sorted(code_map.values())
    prefix_free = all(not b.startswith(a) for a, b in zip(ordered, ordered[1:]))
    cost = sum(w * len(code_map[c]) for c, w in zip(SYMBOLS, weights))
    return "Yes" if prefix_free and cost == exhaustive_cost(tuple(weights)) else "No"


def cases():
    official = """7
A 1 B 1 C 1 D 3 E 3 F 6 G 6
4
A 00000
B 00001
C 0001
D 001
E 01
F 10
G 11
A 01010
B 01011
C 0100
D 011
E 10
F 11
G 00
A 000
B 001
C 010
D 011
E 100
F 101
G 110
A 00000
B 00001
C 0001
D 001
E 00
F 10
G 11
"""
    yield "PTA sample", official, ["Yes", "Yes", "No", "No"]
    w = [4, 2, 1, 1]
    entries = [
        list(zip("0123", ["0", "10", "110", "111"])),
        list(zip("3210", ["101", "100", "11", "0"])),
        list(zip("0123", ["0", "00", "110", "111"])),
        list(zip("0123", ["0", "10", "110", "110"])),
        list(zip("0123", ["00", "01", "10", "11"])),
        list(zip("0122", ["0", "10", "110", "111"])),
    ]
    yield "weighted and prefix edge cases", encode(w, entries), ["Yes", "Yes", "No", "No", "No", "No"]
    # Optimal cost is 250. After forced merges 11+12 and 13+14,
    # Huffman must merge 23+24; this tree instead pairs 23 with 26.
    w = [26, 24, 14, 13, 12, 11]
    entries = [list(zip("012345", ["00", "10", "110", "111", "010", "011"]))]
    assert expected(w, entries[0]) == "Yes"
    yield "optimal tree outside Huffman merge choices", encode(w, entries), ["Yes"]
    w = [0, 0]
    entries = [[("0", "0" * 63), ("1", "0")],
               [("0", "0"), ("1", "0" * 63)],
               [("0", "1"), ("1", "0")]]
    yield "both prefix directions and length 63", encode(w, entries), ["No", "No", "Yes"]
    w = [0, 5]
    yield "zero weight and a non-full optimal code", encode(w, [[("0", "1" * 63), ("1", "0")]]), ["Yes"]
    rng = random.Random(20261110)
    for case in range(120):
        w = [rng.randrange(11) for _ in range(rng.randrange(2, 8))]
        valid = reference_codes(w)
        flipped = [(c, code.translate(str.maketrans("01", "10"))) for c, code in valid]
        entries = [valid, flipped]
        for _ in range(18):
            entry = valid.copy()
            for i in rng.sample(range(len(w)), rng.randrange(1, len(w) + 1)):
                entry[i] = (entry[i][0], "".join(rng.choices("01", k=rng.randrange(1, 9))))
            rng.shuffle(entry)
            entries.append(entry)
        yield f"random {case + 1}", encode(w, entries), [expected(w, e) for e in entries]
    w = [0] * 63
    comb = [("1" * i + "0") for i in range(62)] + ["1" * 62]
    entries = [list(zip(SYMBOLS, comb))]
    # Equal weighted cost forces the prefix checker to inspect every candidate.
    for order in [list(range(63)), list(reversed(range(63)))]:
        duplicate = entries[0].copy()
        duplicate[-1] = (duplicate[-1][0], duplicate[-2][1])
        entries.append([duplicate[i] for i in order])
    long_valid = list(zip(SYMBOLS, ["0" * 57 + format(i, "06b") for i in range(63)]))
    entries.extend([long_valid, list(reversed(long_valid))])
    yield "max trie depth and long shared prefix", encode(w, entries), ["Yes", "No", "No", "Yes", "Yes"]
    # Enumerate every small codebook, including repeated codes.
    for n, max_length in [(2, 3), (3, 2)]:
        words = [format(v, f"0{length}b")
                 for length in range(1, max_length + 1) for v in range(1 << length)]
        entries = [list(zip(SYMBOLS[:n], codes))
                   for codes in itertools.product(words, repeat=n)]
        for weights in [[0] * n, [1] * n, list(range(1, n + 1)), list(range(n, 0, -1))]:
            yield f"exhaustive n={n} weights={weights}", encode(weights, entries), [
                expected(weights, entry) for entry in entries]
    # Scale weights and permute every code bit and symbol row without changing validity.
    for n in [2, 7, 31, 63]:
        weights = [1 + (i * 37) % 500 for i in range(n)]
        valid = reference_codes(weights)
        permuted = [(c, code.translate(str.maketrans("01", "10")))
                    for c, code in reversed(valid)]
        yield f"metamorphic n={n}", encode(weights, [valid, permuted]), ["Yes", "Yes"]
        yield f"scaled weights n={n}", encode([2 * w for w in weights], [valid, permuted]), ["Yes", "Yes"]
    malformed = [
        [("0", "02"), ("1", "1")],
        [("0", "0"), ("x", "1")],
        [("0", "0"), ("1", "10x")],
        [("0", "0"), ("1", "1")],
    ]
    yield "binary validation and input alignment", encode([1, 1], malformed), ["No", "No", "No", "Yes"]
    w = [1000] * 63
    yield "max symbols and submissions", encode(w, [reference_codes(w)] * 1000), ["Yes"] * 1000


def build(folder, variant):
    exe = folder / (variant + ".exe")
    flags = [] if variant == "trie" else ["-D" + variant.upper()]
    subprocess.run([os.getenv("CC", "gcc"), "-std=c99", "-O2", "-Wall", "-Wextra",
                    "-Werror", "-pedantic", *flags, str(ROOT / "huffman.c"), "-o", str(exe)],
                   check=True)
    return exe


def run(exe, data):
    return subprocess.run([str(exe)], input=data.encode(), capture_output=True,
                          check=True, timeout=20).stdout.decode().splitlines()


def benchmark(exes):
    rng = random.Random(73)
    rows = []
    for n in [8, 32, 63]:
        for scenario in ["all_valid", "mixed"]:
            w = [rng.randrange(1, 1001) for _ in range(n)]
            valid = reference_codes(w)
            j = next(i for i, (_, code) in enumerate(valid[:-1]) if len(code) == len(valid[-1][1]))
            invalid = valid[:-1] + [(valid[-1][0], valid[j][1])]
            data = encode(w, [invalid if scenario == "mixed" and i % 2 else valid
                              for i in range(1000)])
            want = ["No" if scenario == "mixed" and i % 2 else "Yes" for i in range(1000)]
            timings = [[] for _ in VARIANTS]
            for i in range(11):
                for j in [(i + offset) % len(VARIANTS) for offset in range(len(VARIANTS))]:
                    start = time.perf_counter_ns()
                    assert run(exes[j], data) == want
                    timings[j].append((time.perf_counter_ns() - start) / 1e6)
            for name, times in zip(VARIANTS, timings):
                rows.append([n, scenario, name, f"{statistics.median(times[1:]):.3f}"])
    with (ROOT / "benchmark.csv").open("w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["symbols", "scenario", "variant", "median_ms"])
        writer.writerows(rows)


if __name__ == "__main__":
    with tempfile.TemporaryDirectory(dir=ROOT) as directory:
        exes = [build(Path(directory), mode) for mode in VARIANTS]
        files = submissions = 0
        for name, data, want in cases():
            for exe in exes:
                got = run(exe, data)
                assert got == want, (name, exe.name, got, want)
            files += 1
            submissions += len(want)
        print(f"{files} inputs, {submissions} submissions passed for all five versions.")
        if "--benchmark" in sys.argv:
            benchmark(exes)


