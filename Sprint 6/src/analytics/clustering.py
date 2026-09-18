"""
Nifty 100 Analytics - K-Means Clustering Engine
Module: src/analytics/clustering.py
Day 36 Milestone
"""

import os
import sqlite3

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

# -------------------------------------------------------------------------
# Configuration & Paths
# -------------------------------------------------------------------------
DB_CANDIDATES = ["/content/nifty100.db", "data/nifty100.db", "nifty100.db"]
CF_INTEL_PATH = "output/cashflow_intelligence.xlsx"
ELBOW_PLOT_PATH = "reports/elbow_plot.png"
OUTPUT_CSV_PATH = "output/cluster_labels.csv"

FEATURES = ["return_on_equity_pct", "debt_to_equity", "revenue_cagr_5yr", "fcf_cagr_5yr", "operating_profit_margin_pct"]


def get_db_connection():
    """Execute Get db connection routine."""
    for path in DB_CANDIDATES:
        if os.path.exists(path):
            return sqlite3.connect(path)
    # Search recursively in current working directory
    for root, _, files in os.walk("."):
        for file in files:
            if file == "nifty100.db":
                return sqlite3.connect(os.path.join(root, file))
    raise FileNotFoundError("Could not find 'nifty100.db'. Please upload or verify the path.")


def find_col(df, candidates):
    """Execute Find col routine."""
    for c in candidates:
        if c in df.columns:
            return c
        for col_name in df.columns:
            if c.lower() == col_name.lower():
                return col_name
    return None


# -------------------------------------------------------------------------
# Step 1: Ingestion & Feature Preparation
# -------------------------------------------------------------------------
def prepare_clustering_dataset():
    """Execute Prepare clustering dataset routine."""
    conn = get_db_connection()
    df_comp = pd.read_sql_query("SELECT * FROM companies;", conn)
    df_ratios = pd.read_sql_query("SELECT * FROM financial_ratios ORDER BY year ASC;", conn)
    conn.close()

    cid_col = find_col(df_comp, ["id", "company_id", "ticker"])
    df_comp["company_id"] = df_comp[cid_col].astype(str).str.strip()

    r_cid_col = find_col(df_ratios, ["company_id", "id", "ticker"])
    df_ratios["company_id"] = df_ratios[r_cid_col].astype(str).str.strip()

    # Get latest financial ratios per company
    latest_ratios = df_ratios.groupby("company_id").last().reset_index()

    # Dynamic column mapping for financial metrics
    roe_col = find_col(latest_ratios, ["return_on_equity_pct", "roe_pct", "roe"])
    de_col = find_col(latest_ratios, ["debt_to_equity", "de_ratio", "d_e"])
    rev_col = find_col(latest_ratios, ["revenue_cagr_5yr", "sales_cagr_5yr", "rev_cagr_5yr"])
    fcf_col = find_col(latest_ratios, ["fcf_cagr_5yr", "free_cash_flow_cagr_5yr"])
    opm_col = find_col(latest_ratios, ["operating_profit_margin_pct", "opm_pct", "ebitda_margin_pct"])

    # Base feature dataframe from companies
    df = pd.DataFrame({"company_id": df_comp["company_id"].unique()})

    # Sector mapping (prioritize cashflow_intelligence.xlsx)
    if os.path.exists(CF_INTEL_PATH):
        df_cf = pd.read_excel(CF_INTEL_PATH)
        df_cf["company_id"] = df_cf["company_id"].astype(str).str.strip()
        sec_map = dict(zip(df_cf["company_id"], df_cf["sector"]))
        df["sector"] = df["company_id"].map(sec_map).fillna("Diversified Industrials")
    else:
        sec_col = find_col(df_comp, ["sector", "broad_sector", "industry"])
        df["sector"] = df_comp[sec_col].astype(str).str.strip() if sec_col else "Diversified Industrials"

    # Merge available metrics
    sub_metrics = latest_ratios[["company_id"]].copy()
    sub_metrics["return_on_equity_pct"] = pd.to_numeric(latest_ratios[roe_col], errors="coerce") if roe_col else np.nan
    sub_metrics["debt_to_equity"] = pd.to_numeric(latest_ratios[de_col], errors="coerce") if de_col else np.nan
    sub_metrics["revenue_cagr_5yr"] = pd.to_numeric(latest_ratios[rev_col], errors="coerce") if rev_col else np.nan
    sub_metrics["fcf_cagr_5yr"] = pd.to_numeric(latest_ratios[fcf_col], errors="coerce") if fcf_col else np.nan
    sub_metrics["operating_profit_margin_pct"] = (
        pd.to_numeric(latest_ratios[opm_col], errors="coerce") if opm_col else np.nan
    )

    # Check cashflow_intelligence.xlsx for fcf_cagr_5yr fallback
    if os.path.exists(CF_INTEL_PATH):
        df_cf = pd.read_excel(CF_INTEL_PATH)
        df_cf["company_id"] = df_cf["company_id"].astype(str).str.strip()
        if "fcf_cagr_5yr" in df_cf.columns:
            fcf_intel = dict(zip(df_cf["company_id"], df_cf["fcf_cagr_5yr"]))
            sub_metrics["fcf_cagr_5yr"] = sub_metrics["fcf_cagr_5yr"].fillna(sub_metrics["company_id"].map(fcf_intel))

    df = df.merge(sub_metrics, on="company_id", how="left")

    # ---------------------------------------------------------------------
    # Step 2: Sector Median Imputation (Fallback to Global Median)
    # ---------------------------------------------------------------------
    for col in FEATURES:
        # Group by sector and fill median
        sector_medians = df.groupby("sector")[col].transform("median")
        df[col] = df[col].fillna(sector_medians)
        # Fallback to global median if whole sector is missing
        global_median = df[col].median()
        if pd.isna(global_median):
            global_median = 12.0  # Safe fundamental benchmark
        df[col] = df[col].fillna(global_median)

    return df


# -------------------------------------------------------------------------
# Step 3: Elbow Plot Generation (k = 2 to 10)
# -------------------------------------------------------------------------
def generate_elbow_plot(X_scaled):
    """Execute Generate elbow plot routine."""
    os.makedirs(os.path.dirname(ELBOW_PLOT_PATH), exist_ok=True)
    k_range = range(2, 11)
    inertias = []

    for k in k_range:
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        km.fit(X_scaled)
        inertias.append(km.inertia_)

    fig, ax = plt.subplots(figsize=(7, 4.2), dpi=180)
    ax.plot(k_range, inertias, marker="o", linewidth=2, color="#1E3A8A", markersize=6)
    ax.axvline(x=5, color="#DC2626", linestyle="--", linewidth=1.5, label="Chosen k = 5")
    ax.scatter([5], [inertias[3]], color="#DC2626", s=100, zorder=5)

    ax.set_title("K-Means Inertia Elbow Curve (k=2 to 10)", fontsize=11, fontweight="bold", color="#0F172A", pad=10)
    ax.set_xlabel("Number of Clusters (k)", fontsize=9.5, fontweight="bold", color="#334155")
    ax.set_ylabel("Inertia (Within-Cluster Sum of Squares)", fontsize=9.5, fontweight="bold", color="#334155")
    ax.set_xticks(list(k_range))
    ax.grid(True, linestyle="--", alpha=0.5, color="#CBD5E1")
    ax.legend(loc="upper right", frameon=False, fontsize=9)
    plt.tight_layout()

    plt.savefig(ELBOW_PLOT_PATH, bbox_inches="tight")
    plt.close(fig)
    print(f"[✓] Elbow plot saved to: {ELBOW_PLOT_PATH}")


# -------------------------------------------------------------------------
# Step 4: KMeans (k=5), Dynamic Cluster Naming & Centroid Distances
# -------------------------------------------------------------------------
def assign_cluster_names(df, feature_cols, centers):
    """
    Labels each cluster by analyzing centroid coordinates:
    Evaluates Capital Return (ROE), Leverage (D/E), and Cash Flow/Growth dynamics.
    """
    cluster_names = {}
    for i, c in enumerate(centers):
        roe, de, rev, fcf, opm = c
        if roe > 0.5 and de < 0.0 and (rev > 0.0 or fcf > 0.0):
            cluster_names[i] = "High-Quality Compounders"
        elif de > 0.8:
            cluster_names[i] = "Leveraged / Capital-Intensive"
        elif rev > 0.5 and fcf > 0.2:
            cluster_names[i] = "High-Growth Reinvestors"
        elif opm > 0.5 and rev < 0.0:
            cluster_names[i] = "Mature Cash Generators"
        else:
            cluster_names[i] = f"Balanced Compounders (Cluster {i})"

    # Ensure unique descriptive names across clusters
    used = set()
    for i in range(len(centers)):
        name = cluster_names.get(i, f"Core Allocators (Cluster {i})")
        counter = 2
        orig_name = name
        while name in used:
            name = f"{orig_name} - Group {counter}"
            counter += 1
        used.add(name)
        cluster_names[i] = name

    return cluster_names


def run_clustering():
    """Execute Run clustering routine."""
    df = prepare_clustering_dataset()
    print(f"[✓] Ingested {len(df)} companies across features: {FEATURES}")

    # Standard Scaling
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(df[FEATURES])

    # Generate and save Elbow Plot
    generate_elbow_plot(X_scaled)

    # Fit KMeans with k=5
    kmeans = KMeans(n_clusters=5, random_state=42, n_init=10)
    cluster_ids = kmeans.fit_predict(X_scaled)
    centers = kmeans.cluster_centers_

    # Calculate Euclidean distance from assigned centroid
    assigned_centers = centers[cluster_ids]
    distances = np.linalg.norm(X_scaled - assigned_centers, axis=1)

    # Assign Cluster Labels & Names
    cluster_names_map = assign_cluster_names(df, FEATURES, centers)

    df["cluster_id"] = cluster_ids
    df["cluster_name"] = df["cluster_id"].map(cluster_names_map)
    df["distance_from_centroid"] = np.round(distances, 4)

    # Select final deliverable columns
    output_df = df[["company_id", "cluster_id", "cluster_name", "distance_from_centroid"]].sort_values("company_id")
    os.makedirs(os.path.dirname(OUTPUT_CSV_PATH), exist_ok=True)
    output_df.to_csv(OUTPUT_CSV_PATH, index=False)

    print(f"[✓] Successfully generated {OUTPUT_CSV_PATH} ({len(output_df)} rows)")
    print("\nCluster Distribution:")
    print(output_df["cluster_name"].value_counts().to_string())


if __name__ == "__main__":
    run_clustering()
