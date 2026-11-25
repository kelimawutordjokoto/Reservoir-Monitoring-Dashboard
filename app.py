"""WOfS reservoir surface area dashboard, 2015-2025 (Bui, Tono, Vea).

Fixed record built from the thesis CSV exports in ./data. All statistics are
computed from those rows when the app starts; nothing is typed in by hand.
Run locally with:  streamlit run app.py
"""
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

DATA = Path(__file__).parent
VALIDATION_START = 2022  # calibration 2015-2021, validation 2022-2025

C_WOFS, C_REF, C_RAW, C_VAL = "#1f6fb4", "#d1792a", "#8c9bab", "#2a9d6f"

st.set_page_config(page_title="WOfS Reservoir Dashboard", layout="wide")


@st.cache_data
def load():
    bui = pd.read_csv(DATA / "bui_area.csv", parse_dates=["date"])
    out = {"bui": bui,
           "bui_vol": pd.read_csv(DATA / "bui_volume.csv", parse_dates=["date"]),
           "bui_dw": pd.read_csv(DATA / "bui_dw_vs_bpa.csv", parse_dates=["date"])}
    for site in ("tono", "vea"):
        out[f"{site}_series"] = pd.read_csv(DATA / f"{site}_series.csv", parse_dates=["date"])
        out[f"{site}_pairs"] = pd.read_csv(DATA / f"{site}_pairs.csv", parse_dates=["date", "dw_date"])
    return out


def stats(obs, ref):
    """Bias, bias %, RMSE, NSE and R² of obs against ref."""
    obs, ref = np.asarray(obs, float), np.asarray(ref, float)
    e = obs - ref
    return {
        "Dates": len(e),
        "Bias (km²)": e.mean(),
        "Bias (%)": 100 * e.mean() / ref.mean(),
        "RMSE (km²)": np.sqrt((e ** 2).mean()),
        "NSE": 1 - (e ** 2).sum() / ((ref - ref.mean()) ** 2).sum(),
        "R²": np.corrcoef(obs, ref)[0, 1] ** 2,
    }


def fmt_table(df, dec):
    return df.style.format({"Bias (km²)": f"{{:.{dec}f}}", "Bias (%)": "{:.1f}", "RMSE (km²)": f"{{:.{dec}f}}",
                            "Bias (10⁸ m³)": "{:.3f}", "RMSE (10⁸ m³)": "{:.3f}",
                            "NSE": "{:.3f}", "R²": "{:.3f}"})


def vol_stats(obs, ref):
    s = stats(obs, ref)
    return {"Dates": s["Dates"], "Bias (10⁸ m³)": s["Bias (km²)"], "Bias (%)": s["Bias (%)"],
            "RMSE (10⁸ m³)": s["RMSE (km²)"], "NSE": s["NSE"]}


def time_chart(traces, divider=None):
    fig = go.Figure(traces)
    if divider is not None:
        fig.add_vline(x=divider, line_dash="dash", line_color="grey")
        fig.add_annotation(x=divider, y=1, yref="paper", text="Validation →", showarrow=False, xanchor="left", yanchor="bottom")
    fig.update_layout(height=420, margin=dict(l=10, r=10, t=30, b=10), hovermode="x unified",
                      yaxis_title="Surface area (km²)", legend=dict(orientation="h", y=1.08, x=0))
    return fig


def scatter_chart(traces, lo, hi, xlab, ylab):
    fig = go.Figure(traces)
    fig.add_trace(go.Scatter(x=[lo, hi], y=[lo, hi], mode="lines", name="1:1 line",
                             line=dict(color="grey", dash="dash"), hoverinfo="skip"))
    fig.update_layout(height=420, margin=dict(l=10, r=10, t=30, b=10), xaxis_title=xlab, yaxis_title=ylab,
                      legend=dict(orientation="h", y=1.08, x=0))
    fig.update_yaxes(scaleanchor="x", scaleratio=1)
    return fig


d = load()
bui = d["bui"]
cal, val = bui[bui.date.dt.year < VALIDATION_START], bui[bui.date.dt.year >= VALIDATION_START]
b = (cal.bpa_km2 - cal.wofs_raw_km2).mean()

# ---------------------------------------------------------------- header
st.title("WOfS reservoir surface area, 2015–2025")
summary = pd.DataFrame([
    {"Reservoir": "Bui", "Reference": "BPA gauge-derived area", **stats(bui.wofs_raw_km2, bui.bpa_km2)},
    {"Reservoir": "Tono", "Reference": "Dynamic World (±1 day)", **stats(d["tono_pairs"].wofs_km2, d["tono_pairs"].dw_km2)},
    {"Reservoir": "Vea", "Reference": "Dynamic World (±1 day)", **stats(d["vea_pairs"].wofs_km2, d["vea_pairs"].dw_km2)},
]).set_index("Reservoir")
corr_val = stats(val.wofs_corrected_km2, val.bpa_km2)
st.markdown(
    f"WOfS follows the rise and fall of all three reservoirs closely but reports less water than the reference: "
    f"**{abs(summary.loc['Bui', 'Bias (%)']):.1f}%** below the BPA gauge-derived area at Bui, and "
    f"**{abs(summary.loc['Tono', 'Bias (%)']):.1f}%** and **{abs(summary.loc['Vea', 'Bias (%)']):.1f}%** below "
    f"Dynamic World at Tono and Vea. At Bui an additive correction of **{b:.2f} km²** brings the validation RMSE "
    f"to **{corr_val['RMSE (km²)']:.2f} km²** (NSE {corr_val['NSE']:.2f})."
)
st.caption("Fixed record from the thesis runs (Landsat WOfS, Digital Earth Africa). Not a live feed.")

# ---------------------------------------------------------------- sidebar
st.sidebar.header("View")
site = st.sidebar.radio("Reservoir", ["Bui", "Tono", "Vea"])
years = st.sidebar.slider("Years shown in charts", 2015, 2025, (2015, 2025))
st.sidebar.caption("The year filter changes the charts only. Statistics always use the full record, "
                   "as reported in the thesis.")


def in_years(df):
    return df[df.date.dt.year.between(*years)]


# ---------------------------------------------------------------- summary
with st.expander("All three reservoirs against their reference (uncorrected WOfS)", expanded=True):
    st.dataframe(fmt_table(summary.drop(columns="NSE"), 3), width="stretch")
    st.caption("Bias is WOfS minus reference. Dynamic World is a second satellite product, not ground truth, so at "
               "Tono and Vea the comparison describes relative behaviour only. No correction is applied there.")

# ---------------------------------------------------------------- Bui
if site == "Bui":
    st.header("Bui: WOfS against the BPA gauge-derived area")
    st.caption("BPA area is from the water level and the BPA elevation–area table. The correction adds a constant "
               f"b = {b:.2f} km², the mean BPA minus WOfS difference over 2015–2021 (calibration); "
               "2022–2025 is held out for validation.")
    tab_a, tab_v, tab_d = st.tabs(["Surface area", "Storage volume", "Dynamic World against BPA"])
    with tab_a:
        show = st.multiselect("Series", ["BPA (gauge-derived)", "WOfS uncorrected", "WOfS corrected"],
                              default=["BPA (gauge-derived)", "WOfS uncorrected", "WOfS corrected"])
        v = in_years(bui)
        tr = []
        if "BPA (gauge-derived)" in show:
            tr.append(go.Scatter(x=v.date, y=v.bpa_km2, name="BPA (gauge-derived)", mode="lines", line=dict(color=C_REF, width=2.5),
                                 customdata=v.level_m, hovertemplate="%{y:.1f} km² (level %{customdata:.2f} m)"))
        if "WOfS uncorrected" in show:
            tr.append(go.Scatter(x=v.date, y=v.wofs_raw_km2, name="WOfS uncorrected", mode="lines", line=dict(color=C_RAW),
                                 hovertemplate="%{y:.1f} km²"))
        if "WOfS corrected" in show:
            tr.append(go.Scatter(x=v.date, y=v.wofs_corrected_km2, name="WOfS corrected", mode="lines", line=dict(color=C_WOFS),
                                 hovertemplate="%{y:.1f} km²"))
        div = pd.Timestamp(f"{VALIDATION_START}-01-01")
        st.plotly_chart(time_chart(tr, div if v.date.min() < div < v.date.max() else None), width="stretch")

        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Corrected WOfS against BPA")
            vc, vv = in_years(cal), in_years(val)
            sc = [go.Scatter(x=x.bpa_km2, y=x.wofs_corrected_km2, mode="markers", name=n, marker=dict(color=c, size=7),
                             customdata=x.date.dt.strftime("%d %b %Y"),
                             hovertemplate="%{customdata}<br>BPA %{x:.1f} km²<br>WOfS corrected %{y:.1f} km²<extra></extra>")
                  for x, n, c in ((vc, "Calibration 2015–2021", C_WOFS), (vv, "Validation 2022–2025", C_VAL))]
            lo = min(bui.bpa_km2.min(), bui.wofs_corrected_km2.min()); hi = max(bui.bpa_km2.max(), bui.wofs_corrected_km2.max())
            st.plotly_chart(scatter_chart(sc, lo, hi, "BPA area (km²)", "Corrected WOfS area (km²)"), width="stretch")
        with c2:
            st.subheader("Accuracy before and after correction")
            t = pd.DataFrame([
                {"Series and dates": "Uncorrected, all dates 2015–2025", **stats(bui.wofs_raw_km2, bui.bpa_km2)},
                {"Series and dates": "Uncorrected, validation 2022–2025", **stats(val.wofs_raw_km2, val.bpa_km2)},
                {"Series and dates": "Corrected, validation 2022–2025", **corr_val},
            ]).set_index("Series and dates")[["Dates", "Bias (km²)", "RMSE (km²)", "NSE"]]
            st.dataframe(fmt_table(t, 2), width="stretch")
        st.download_button("Download Bui area rows (CSV)", bui.to_csv(index=False).encode(), "bui_area.csv", "text/csv")

    with tab_v:
        vol = d["bui_vol"]
        st.caption("Storage from the integral of area over level, scaled to the tabulated BPA storage at each table row "
                   "(after Baup et al., 2014). The reference is the storage at the BPA water level; WOfS storage uses "
                   "the corrected WOfS area. Units 10⁸ m³.")
        vv = in_years(vol)
        tr = [go.Scatter(x=vv.date, y=vv.volume_ref_e8m3, name="BPA reference", mode="lines", line=dict(color=C_REF, width=2.5),
                         hovertemplate="%{y:.2f} ×10⁸ m³"),
              go.Scatter(x=vv.date, y=vv.volume_wofs_uncorr_e8m3, name="WOfS uncorrected", mode="lines", line=dict(color=C_RAW),
                         hovertemplate="%{y:.2f} ×10⁸ m³"),
              go.Scatter(x=vv.date, y=vv.volume_wofs_e8m3, name="WOfS corrected", mode="lines", line=dict(color=C_WOFS),
                         hovertemplate="%{y:.2f} ×10⁸ m³")]
        fig = time_chart(tr, div if vv.date.min() < div < vv.date.max() else None)
        fig.update_layout(yaxis_title="Storage (10⁸ m³)")
        st.plotly_chart(fig, width="stretch")
        vval = vol[vol.date.dt.year >= VALIDATION_START]
        t = pd.DataFrame([
            {"Series and dates": "Uncorrected, validation 2022–2025", **vol_stats(vval.volume_wofs_uncorr_e8m3, vval.volume_ref_e8m3)},
            {"Series and dates": "Corrected, validation 2022–2025", **vol_stats(vval.volume_wofs_e8m3, vval.volume_ref_e8m3)},
        ]).set_index("Series and dates")
        st.dataframe(fmt_table(t, 3), width="stretch")
        st.caption(f"Reference storage ranges from {vol.volume_ref_e8m3.min():.2f} to {vol.volume_ref_e8m3.max():.2f} "
                   f"×10⁸ m³ (mean {vol.volume_ref_e8m3.mean():.2f}) over {len(vol)} dates.")
        st.download_button("Download Bui volume rows (CSV)", vol.to_csv(index=False).encode(), "bui_volume.csv", "text/csv")

    with tab_d:
        dw = d["bui_dw"]
        st.caption("Dynamic World area on dates with at least 90% valid coverage, against the BPA gauge-derived area on "
                   "the same date. This checks Dynamic World itself, which is the reference used at Tono and Vea.")
        vd = in_years(dw)
        tr = [go.Scatter(x=vd.date, y=vd.bpa_km2, name="BPA (gauge-derived)", mode="lines", line=dict(color=C_REF, width=2.5),
                         hovertemplate="%{y:.1f} km²"),
              go.Scatter(x=vd.date, y=vd.dw_km2, name="Dynamic World", mode="markers", marker=dict(color=C_WOFS, size=6),
                         customdata=vd.coverage_pct, hovertemplate="%{y:.1f} km² (coverage %{customdata:.0f}%)")]
        st.plotly_chart(time_chart(tr), width="stretch")
        t = pd.DataFrame([{"Comparison": "Dynamic World − BPA, all dates", **stats(dw.dw_km2, dw.bpa_km2)}]).set_index("Comparison")
        st.dataframe(fmt_table(t, 2), width="stretch")
        st.caption(f"Dynamic World was below the BPA area on {(dw.dw_minus_bpa < 0).sum()} of {len(dw)} dates. It tracks "
                   "the variation of the reservoir but is biased low, so it is a reference for relative behaviour only.")
        st.download_button("Download Bui Dynamic World rows (CSV)", dw.to_csv(index=False).encode(), "bui_dw_vs_bpa.csv", "text/csv")

# ---------------------------------------------------------------- Tono / Vea
else:
    key = site.lower()
    s, p = d[f"{key}_series"], d[f"{key}_pairs"]
    st.header(f"{site}: WOfS against Dynamic World")
    st.caption(f"Gap-filled WOfS series ({len(s)} dates) with Dynamic World on dates within one day and at least "
               f"90% valid coverage ({len(p)} pairs). No correction is applied.")
    vs, vp = in_years(s), in_years(p)
    tr = [
        go.Scatter(x=vs.date, y=vs.wofs_high_km2, mode="lines", line=dict(width=0), showlegend=False, hoverinfo="skip"),
        go.Scatter(x=vs.date, y=vs.wofs_low_km2, mode="lines", line=dict(width=0), fill="tonexty",
                   fillcolor="rgba(31,111,180,0.18)", name="Fill uncertainty band", hoverinfo="skip"),
        go.Scatter(x=vs.date, y=vs.wofs_km2, mode="lines", name="WOfS (gap-filled)", line=dict(color=C_WOFS),
                   customdata=vs.contamination * 100, hovertemplate="%{y:.2f} km² (contamination %{customdata:.0f}%)"),
        go.Scatter(x=vp.date, y=vp.dw_km2, mode="markers", name="Dynamic World (paired dates)",
                   marker=dict(color=C_REF, size=7), hovertemplate="%{y:.2f} km²"),
    ]
    st.plotly_chart(time_chart(tr), width="stretch")

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("WOfS against Dynamic World on paired dates")
        sc = [go.Scatter(x=vp.dw_km2, y=vp.wofs_km2, mode="markers", name="Paired date", marker=dict(color=C_WOFS, size=7),
                         customdata=np.stack([vp.date.dt.strftime("%d %b %Y"), vp.dw_date.dt.strftime("%d %b %Y"),
                                              vp.contamination * 100], axis=-1),
                         hovertemplate="WOfS %{customdata[0]}: %{y:.3f} km²<br>DW %{customdata[1]}: %{x:.3f} km²"
                                       "<br>Contamination %{customdata[2]:.0f}%<extra></extra>")]
        lo = min(p.dw_km2.min(), p.wofs_km2.min()); hi = max(p.dw_km2.max(), p.wofs_km2.max())
        st.plotly_chart(scatter_chart(sc, lo, hi, "Dynamic World area (km²)", "WOfS area (km²)"), width="stretch")
    with c2:
        st.subheader("Agreement statistics")
        t = pd.DataFrame([{"Comparison": "WOfS − Dynamic World, all pairs", **stats(p.wofs_km2, p.dw_km2)}]).set_index("Comparison")
        st.dataframe(fmt_table(t, 3), width="stretch")
        st.caption("Dynamic World was itself below the BPA area at Bui, so these differences describe WOfS relative "
                   "to Dynamic World, not absolute error.")
    st.download_button(f"Download {site} paired dates (CSV)", p.to_csv(index=False).encode(), f"{key}_pairs.csv", "text/csv")

with st.expander("Definitions and data sources"):
    st.markdown(
        "- **Bias**: mean of WOfS minus reference. **Bias (%)**: bias divided by the mean reference area.\n"
        "- **RMSE**: root mean square difference. **NSE**: Nash–Sutcliffe efficiency. **R²**: squared Pearson correlation.\n"
        "- **Fill uncertainty band** (Tono, Vea): range of the gap-filled area across the low and high fill thresholds.\n"
        "- Data: `bui_area.csv` (from `Bui_WOfS_volume.csv`, BPA-curve run, area columns only); "
        "`tono_series.csv` and `tono_pairs.csv` (from the Tono \" 2\" exports); "
        "`vea_series.csv` and `vea_pairs.csv` (Vea exports); `bui_volume.csv` and `bui_dw_vs_bpa.csv` "
        "(integral-route run of the Bui notebook)."
    )
