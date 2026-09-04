"""
Nifty 100 Multi-Axis Radar Visualizer
Module: src/visualization/radar.py
Description: Generates 8-axis polar radar charts comparing individual company 
             fundamental profiles against peer group averages.
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def normalize_to_radar_scale(df: pd.DataFrame, axes_cols: list) -> pd.DataFrame:
    """Normalizes selected metric columns to a 0-100 scale for radar plotting."""
    df_norm = df.copy()
    for col in axes_cols:
        if col not in df_norm.columns:
            df_norm[col] = 50.0
            continue
        vals = pd.to_numeric(df_norm[col], errors="coerce")
        # Invert D/E: lower is better (0 debt -> 100 score)
        if col == "debt_to_equity":
            scaled = (1.0 - (vals.clip(0, 3.0) / 3.0)) * 100.0
        else:
            p10, p90 = vals.quantile(0.10), vals.quantile(0.90)
            clipped = vals.clip(p10, p90)
            min_v, max_v = clipped.min(), clipped.max()
            if min_v == max_v:
                scaled = pd.Series(50.0, index=vals.index)
            else:
                scaled = ((clipped - min_v) / (max_v - min_v)) * 100.0
        df_norm[col + "_score"] = scaled.fillna(50.0)
    return df_norm


def plot_company_radar_chart(
    company_id: str,
    company_name: str,
    peer_group_name: str,
    company_scores: list,
    peer_avg_scores: list,
    categories: list,
    output_path: str
):
    """Renders and saves an 8-axis dark-themed polar radar chart."""
    num_vars = len(categories)
    angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()

    # Complete the circular loop
    company_scores_plot = company_scores + [company_scores[0]]
    peer_avg_scores_plot = peer_avg_scores + [peer_avg_scores[0]]
    angles_plot = angles + [angles[0]]

    # Dark theme figure setup
    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True), dpi=300)
    fig.patch.set_facecolor('#0B0F19')
    ax.set_facecolor('#0D1117')

    # Polar styling
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    plt.xticks(angles, categories, color='#94A3B8', size=10, fontweight='bold')
    ax.set_rlabel_position(0)
    plt.yticks([25, 50, 75, 100], ["25", "50", "75", "100"], color="#4B5563", size=8)
    plt.ylim(0, 100)
    ax.grid(color="#1F2937", linestyle='--', linewidth=0.8)
    ax.spines['polar'].set_color('#1F2937')

    # Plot Peer Group Average (Dashed Gold Line)
    ax.plot(angles_plot, peer_avg_scores_plot, color='#F59E0B', linewidth=1.8, linestyle='--', label=f'{peer_group_name} Avg')

    # Plot Target Company (Filled Cyan Polygon)
    ax.plot(angles_plot, company_scores_plot, color='#38BDF8', linewidth=2.2, linestyle='solid', label=company_id)
    ax.fill(angles_plot, company_scores_plot, color='#38BDF8', alpha=0.35)

    # Title & Legend
    plt.title(f"{company_name} ({company_id})\nFundamental Profile vs. {peer_group_name}", 
              size=13, color='#FFFFFF', weight='bold', pad=25)
    ax.legend(loc='upper right', bbox_to_anchor=(1.25, 1.12), facecolor='#161B22', edgecolor='#1F2937', labelcolor='#FFFFFF')

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, facecolor=fig.get_facecolor(), bbox_inches='tight')
    plt.close()


def generate_all_radar_charts(df_universe: pd.DataFrame, df_peer_groups: pd.DataFrame, output_dir: str = "reports/radar_charts"):
    """Batch generates radar charts for all companies in the universe."""
    os.makedirs(output_dir, exist_ok=True)

    axes_metrics = [
        "return_on_equity_pct", "operating_profit_margin_pct", "net_profit_margin_pct",
        "debt_to_equity", "free_cash_flow_cr", "pat_cagr_5yr", "revenue_cagr_5yr",
        "composite_quality_score"
    ]
    axes_labels = ["ROE", "OPM", "NPM", "Leverage (Inv)", "FCF", "PAT CAGR", "Rev CAGR", "Quality Score"]

    # Merge peer group information
    df_merged = pd.merge(df_universe, df_peer_groups, on="company_id", how="left")
    df_merged["peer_group_name"] = df_merged["peer_group_name"].fillna("General Market")

    # Normalize metrics to 0-100 scale
    df_scaled = normalize_to_radar_scale(df_merged, axes_metrics)
    score_cols = [col + "_score" for col in axes_metrics]

    # Calculate peer group averages
    peer_averages = df_scaled.groupby("peer_group_name")[score_cols].mean()

    exported_count = 0
    for _, row in df_scaled.iterrows():
        cid = row["company_id"]
        cname = row.get("company_name", cid)
        pg_name = row["peer_group_name"]

        company_vals = row[score_cols].tolist()
        peer_vals = peer_averages.loc[pg_name].tolist() if pg_name in peer_averages.index else [50.0] * len(axes_labels)

        out_path = os.path.join(output_dir, f"{cid}_radar.png")
        plot_company_radar_chart(cid, cname, pg_name, company_vals, peer_vals, axes_labels, out_path)
        exported_count += 1

    return exported_count
