"""Measure prefix checks in C, independently of process startup and input parsing."""
import csv
from pathlib import Path
import statistics
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parent
VARIANTS = ["trie", "pairwise", "interval"]

def main():
    rows = []
    with tempfile.TemporaryDirectory(dir=ROOT) as directory:
        executables = []
        for variant in VARIANTS:
            exe = Path(directory) / (variant + ".exe")
            flags = [] if variant == "trie" else ["-D" + variant.upper()]
            subprocess.run(["gcc", "-std=c99", "-O2", "-Wall", "-Wextra", "-Werror",
                            "-pedantic", *flags, str(ROOT / "benchmark_prefix.c"),
                            "-o", str(exe)], check=True)
            executables.append(exe)
        for n in [8, 32, 63]:
            width = (n - 1).bit_length()
            short = [format(i, f"0{width}b") for i in range(n)]
            long = ["0" * (63 - width) + code for code in short]
            conflict = long[:-1] + [long[-2]]
            for scenario, codes, valid in [
                ("short_valid", short, True), ("long_valid", long, True),
                ("late_duplicate", conflict, False)]:
                data = (str(n) + "\n" + "\n".join(codes) + "\n").encode()
                times = [[] for _ in VARIANTS]
                for repeat in range(7):
                    for j in [(repeat + offset) % 3 for offset in range(3)]:
                        result = subprocess.run([str(executables[j])], input=data,
                                                capture_output=True, check=True,
                                                timeout=20).stdout.decode().split()
                        assert int(result[1]) == (20100 if valid else 0)
                        times[j].append(float(result[0]))
                for variant, measurements in zip(VARIANTS, times):
                    rows.append([n, scenario, variant, f"{statistics.median(measurements):.3f}",
                                 f"{min(measurements):.3f}", f"{max(measurements):.3f}"])
    with (ROOT / "prefix_benchmark.csv").open("w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["symbols", "scenario", "variant", "median_ns", "min_ns", "max_ns"])
        writer.writerows(rows)

if __name__ == "__main__":
    main()
