# WOfS Reservoir Dashboard (Streamlit)

A simple interactive dashboard of the thesis WOfS results for Bui, Tono and Vea, 2015–2025.
It is a fixed record built from the exported CSVs in `data/`; every statistic on the page is
computed from those rows when the app starts.

## Files

- `app.py`: the app.
- `requirements.txt`: Python packages.
- `data/bui_area.csv`: Bui area per date (BPA gauge-derived area, WOfS uncorrected and corrected), from `Bui_WOfS_volume.csv` (BPA-curve run, area columns only).
- `data/tono_series.csv`, `data/tono_pairs.csv`: from `Tono_WOfS_final_series 2.csv` and `Tono_WOfS_DW_matched_dates 2.csv`.
- `data/vea_series.csv`, `data/vea_pairs.csv`: from `Vea_WOfS_final_series.csv` and `Vea_WOfS_DW_matched_dates.csv`.
- `data/bui_volume.csv`, `data/bui_dw_vs_bpa.csv`: from the integral-route run of the Bui notebook (`Bui_WOfS_volume.csv`, `Bui_DW_vs_BPA.csv`; originals kept in `bui/integral_run/`).

## Run it on your computer

```
pip install -r requirements.txt
streamlit run app.py
```

It opens at http://localhost:8501.

## Put it online (free public link, Streamlit Community Cloud)

1. Create a new public repository on GitHub (for example `wofs-dashboard`) and upload this whole
   folder to it: `app.py`, `requirements.txt`, `README.md` and the `data` folder.
2. Go to https://share.streamlit.io and sign in with your GitHub account.
3. Click **Create app**, then **Deploy a public app from GitHub**. Choose the repository, branch `main`
   and main file `app.py`. Optionally pick a custom subdomain such as `wofs-ghana`.
4. Click **Deploy**. After a minute or two you get a link like `https://wofs-ghana.streamlit.app`.

To update the app later, change the files in the GitHub repository; Streamlit Cloud redeploys automatically.

Note that the data files in a public repository can be downloaded by anyone.
