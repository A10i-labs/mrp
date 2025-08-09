from typing import Dict, Any, List
import json
import statistics
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


class GenomicsReducer:
    def run(self, inputs: List[Dict[str, Any]], seed: str) -> Dict[str, Any]:
        shards_sorted = sorted(inputs, key=lambda x: x.get("bin_index_start", 0))
        merged_bins: List[int] = []
        total_reads = 0
        mapped_reads = 0
        total_variants = 0
        for shard in shards_sorted:
            merged_bins.extend([int(v) for v in shard.get("coverage_bins", [])])
            total_reads += int(shard.get("total_reads", 0))
            mapped_reads += int(shard.get("mapped_reads", 0))
            total_variants += int(shard.get("variant_count", 0))
        if not merged_bins:
            mean_coverage = 0.0
            median_coverage = 0.0
            min_coverage = 0
            max_coverage = 0
            coverage_breadth_pct = 0.0
        else:
            mean_coverage = float(sum(merged_bins)) / float(len(merged_bins))
            median_coverage = float(statistics.median(merged_bins))
            min_coverage = int(min(merged_bins))
            max_coverage = int(max(merged_bins))
            coverage_breadth_pct = (sum(1 for v in merged_bins if v > 0) / float(len(merged_bins))) * 100.0
        mapping_rate_pct = (float(mapped_reads) / float(total_reads) * 100.0) if total_reads else 0.0
        return {
            "bins": merged_bins,
            "stats": {
                "mean_coverage": mean_coverage,
                "median_coverage": median_coverage,
                "min_coverage": min_coverage,
                "max_coverage": max_coverage,
                "coverage_breadth_pct": coverage_breadth_pct,
                "total_reads": total_reads,
                "mapped_reads": mapped_reads,
                "mapping_rate_pct": mapping_rate_pct,
                "total_variants": total_variants,
            },
        }


class GenomicsReportProducer:
    def run(self, result: Dict[str, Any], seed: str) -> Dict[str, Any]:
        bins: List[int] = [int(v) for v in result.get("bins", [])]
        stats: Dict[str, Any] = result.get("stats", {})
        df = pd.DataFrame({"bin_index": list(range(len(bins))), "coverage": bins})
        df.to_csv("genomics_bins.csv", index=False)
        # Multi-panel plot roughly inspired by the demo
        fig = plt.figure(figsize=(16, 12))
        gs = fig.add_gridspec(2, 2, hspace=0.3, wspace=0.3)
        fig.suptitle("Genomics Analysis Results (Binned)", fontsize=18, fontweight="bold")
        # Panel 1: coverage vs bin index
        ax1 = fig.add_subplot(gs[0, :])
        ax1.plot(df["bin_index"], df["coverage"], linewidth=1.2, color="steelblue")
        ax1.set_xlabel("Bin index")
        ax1.set_ylabel("Coverage")
        ax1.set_title("Coverage Across Bins")
        if len(bins) > 0:
            ax1.axhline(stats.get("mean_coverage", 0.0), color="red", linestyle="--", alpha=0.7, label=f"Mean {stats.get('mean_coverage',0):.1f}")
            ax1.legend()
        # Panel 2: histogram
        ax2 = fig.add_subplot(gs[1, 0])
        ax2.hist(df["coverage"], bins=50, color="lightcoral", edgecolor="black", alpha=0.8)
        ax2.set_title("Coverage Distribution")
        ax2.set_xlabel("Coverage")
        ax2.set_ylabel("Count")
        # Panel 3: summary bars
        ax3 = fig.add_subplot(gs[1, 1])
        bars_labels = ["Mean", "Median", "Min", "Max"]
        bars_vals = [
            float(stats.get("mean_coverage", 0.0)),
            float(stats.get("median_coverage", 0.0)),
            float(stats.get("min_coverage", 0.0)),
            float(stats.get("max_coverage", 0.0)),
        ]
        ax3.bar(bars_labels, bars_vals, color=["skyblue", "lightgreen", "orange", "plum"], alpha=0.85, edgecolor="black")
        ax3.set_title("Coverage Stats")
        for i, v in enumerate(bars_vals):
            ax3.text(i, v, f"{v:.1f}", ha="center", va="bottom")
        fig.tight_layout()
        fig.savefig("genomics_analysis_plots.png", dpi=200)
        fig.savefig("genomics_analysis_plots.pdf")
        plt.close(fig)
        with open("genomics_summary.txt", "w") as f:
            f.write(json.dumps(stats, indent=2))
        # Machine-readable summary TSV
        with open("analysis_summary.tsv", "w") as f:
            f.write("metric\tvalue\tunit\n")
            f.write(f"total_reads\t{int(stats.get('total_reads',0))}\treads\n")
            f.write(f"mapped_reads\t{int(stats.get('mapped_reads',0))}\treads\n")
            f.write(f"mapping_rate\t{float(stats.get('mapping_rate_pct',0.0)):.2f}\tpercent\n")
            f.write(f"mean_coverage\t{float(stats.get('mean_coverage',0.0)):.2f}\tx\n")
            f.write(f"median_coverage\t{float(stats.get('median_coverage',0.0)):.2f}\tx\n")
            f.write(f"min_coverage\t{int(stats.get('min_coverage',0))}\tx\n")
            f.write(f"max_coverage\t{int(stats.get('max_coverage',0))}\tx\n")
            f.write(f"coverage_breadth\t{float(stats.get('coverage_breadth_pct',0.0)):.2f}\tpercent\n")
            f.write(f"variant_count\t{int(stats.get('total_variants',0))}\tvariants\n")
        # Markdown report
        with open("analysis_report.md", "w") as f:
            f.write("# Genomics Analysis Report\n\n")
            f.write("## Summary Metrics\n\n")
            f.write("- Total reads: {:,}\n".format(int(stats.get("total_reads", 0))))
            f.write("- Mapped reads: {:,}\n".format(int(stats.get("mapped_reads", 0))))
            f.write("- Mapping rate: {:.2f}%\n".format(float(stats.get("mapping_rate_pct", 0.0))))
            f.write("- Mean coverage: {:.2f}x\n".format(float(stats.get("mean_coverage", 0.0))))
            f.write("- Median coverage: {:.2f}x\n".format(float(stats.get("median_coverage", 0.0))))
            f.write("- Coverage breadth: {:.2f}%\n".format(float(stats.get("coverage_breadth_pct", 0.0))))
            f.write("- Variants found: {}\n\n".format(int(stats.get("total_variants", 0))))
            f.write("## Figures\n\n")
            f.write("See: genomics_analysis_plots.png and genomics_analysis_plots.pdf\n")
        result = dict(result)
        result["artifacts"] = {
            "bins_csv": "genomics_bins.csv",
            "summary": "genomics_summary.txt",
            "plots_png": "genomics_analysis_plots.png",
            "plots_pdf": "genomics_analysis_plots.pdf",
            "report_md": "analysis_report.md",
            "summary_tsv": "analysis_summary.tsv",
        }
        return result



