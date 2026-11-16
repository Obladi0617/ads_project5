"""Compile targeted incorrect variants and require a counterexample for each."""
import csv
import subprocess
import tempfile
from pathlib import Path
from test_huffman import ROOT, VARIANTS, build, cases, run

MUTATIONS = {
    "omit_optimal_cost": ("cost == optimum", "optimum >= 0"),
    "omit_duplicate_terminal": (
        "trie[node].terminal || trie[node].children[0] || trie[node].children[1]",
        "trie[node].children[0] || trie[node].children[1]"),
    "omit_existing_prefix": ("if (trie[node].terminal)", "if (false)"),
    "omit_new_prefix": (
        "trie[node].terminal || trie[node].children[0] || trie[node].children[1]",
        "trie[node].terminal"),
    "omit_symbol_uniqueness": ("weights[key] < 0 || seen[key] ||", "weights[key] < 0 ||"),
}
EXTRA_MUTATIONS = {
    "interval_reject_adjacent": ("INTERVAL",
        "intervals[i].start < intervals[i - 1].end",
        "intervals[i].start <= intervals[i - 1].end"),
    "interval_reverse_sort": ("INTERVAL",
        "(a->start > b->start) - (a->start < b->start)",
        "(a->start < b->start) - (a->start > b->start)"),
    "packed_wrong_overlap": ("PACKED",
        "current.start < intervals[j].end && intervals[j].start < current.end",
        "current.start < intervals[j].end || intervals[j].start < current.end"),
    "sorted_omit_right_neighbor": ("SORTED",
        "(position < i && intervals[position].start < current.end)", "false"),
    "wrong_merge_cost": ("",
        "cost += weight;", "cost += weight + 1;"),
}
# Fixed, independently obvious witnesses supplement the shared regression suite.
WITNESSES = [
    ("duplicate_symbol_with_optimal_cost",
     "2\n0 1 1 1\n1\n0 0\n0 1\n", ["No"]),
    ("duplicate_code_with_optimal_cost",
     "2\n0 1 1 1\n1\n0 0\n1 0\n", ["No"]),
]

def main():
    source = (ROOT / "huffman.c").read_text()
    tests = list(cases()) + WITNESSES
    results = []
    with tempfile.TemporaryDirectory(dir=ROOT) as directory:
        folder = Path(directory)
        for variant in VARIANTS:
            baseline = build(folder, variant)
            for title, data, want in WITNESSES:
                assert run(baseline, data) == want, (variant, title)
        mutations = [(name, "", old, new) for name, (old, new) in MUTATIONS.items()]
        mutations.extend((name, variant, old, new)
                         for name, (variant, old, new) in EXTRA_MUTATIONS.items())
        for name, variant, old, new in mutations:
            assert source.count(old) == 1, name
            path = folder / (name + ".c")
            exe = folder / (name + ".exe")
            path.write_text(source.replace(old, new))
            flags = ["-D" + variant] if variant else []
            subprocess.run(["gcc", "-std=c99", "-O2", *flags, str(path), "-o", str(exe)], check=True)
            witness = None
            for title, data, want in tests:
                if run(exe, data) != want:
                    witness = title
                    break
            assert witness is not None, f"Surviving mutation: {name}"
            results.append([name, "killed", witness])
    with (ROOT / "mutation_results.csv").open("w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["mutation", "result", "first_counterexample"])
        writer.writerows(results)
    print(f"{len(results)}/{len(MUTATIONS) + len(EXTRA_MUTATIONS)} targeted mutations detected.")

if __name__ == "__main__":
    main()
