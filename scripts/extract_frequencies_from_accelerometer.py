"""
FFT Analyzer with Hanning Window
--------------------------------

This Dash web app loads accelerometer/axis data from a Parquet file
and provides interactive analysis in both the time and frequency domain.

Features:
    - Load time series data from a Parquet file (expects 'timestamp' + axis columns).
    - Select a range of samples via an interactive slider.
    - Plot:
        * Raw time-domain signals.
        * Windowed signals using a Hanning window.
    - Compute FFT with zero-padding for frequency resolution.
    - Extract top 5 dominant frequencies per axis.
    - Display frequencies in a sortable table.
    - Export results to Excel (.xlsx) for further analysis.

Usage:
    python fft_analyzer.py

    - Modify the `route` variable to point to your `.parquet` file.
    - Run the script; a local Dash server will start (default: http://127.0.0.1:8050).
    - Open the URL in your browser.
    - Use the slider to select a time interval.
    - View raw and windowed signals, frequency spectrum, and top frequencies.
    - Click "Download Top Frequencies" to save results as Excel.

Requirements:
    pip install pandas numpy dash plotly scipy xlsxwriter pyarrow fastparquet

Author:
    Name: Zygimantas Jasiunas
    Affiliation: LASIGE - Faculty of Sciences of the University of Lisbon
    Email: zjasiunas at fc.ul.pt
"""


import pandas as pd
import numpy as np
from dash import Dash, dcc, html, Input, Output
import dash_table
import plotly.graph_objs as go
from scipy.fft import rfft, rfftfreq
from scipy.signal import windows
import io

# Load your data
route = "./acc/laboratory/washing_machine/becken-flt_BWM5381IX/cotton/wm_becken-flt_BWM5381IX_cold_cotton_40_0_acc.parquet"
df = pd.read_parquet(route)
df['timestamp'] = pd.to_datetime(df['timestamp'])
df = df.sort_values('timestamp').reset_index(drop=True)

# Constants
SAMPLE_RATE = 200  # Hz
DT = 1 / SAMPLE_RATE
MIN_SAMPLES = 256
PADDED_SIZE = 4096  # for FFT

# Axis detection
axis_columns = [col for col in df.columns if any(axis in col for axis in ['top.', 'side.', 'back.']) and col != 'timestamp']
axis_map = {
    'top.x': 'TX', 'top.y': 'TY', 'top.z': 'TZ',
    'back.x': 'BX', 'back.y': 'BY', 'back.z': 'BZ',
    'side.x': 'SX', 'side.y': 'SY', 'side.z': 'SZ'
}

# Slider marks
df['time_str'] = df['timestamp'].dt.strftime('%H:%M:%S.%f')
slider_indices = np.linspace(0, len(df)-1, 10, dtype=int)
slider_marks = {int(i): df['time_str'].iloc[int(i)][:12] for i in slider_indices}

# Global storage for frequency data
top_freq_df = pd.DataFrame()

# Dash App
app = Dash(__name__)
app.layout = html.Div([
    html.H2("FFT Analyzer with Hanning Window and Export"),

    html.Label("Select Time Range:"),
    dcc.RangeSlider(
        id='range-slider',
        min=0,
        max=len(df) - 1,
        value=[0, min(1024, len(df) - 1)],
        marks=slider_marks,
        step=1
    ),

    dcc.Graph(id="raw-plot"),
    dcc.Graph(id="windowed-plot"),

    html.Div(id="fft-output"),

    html.Button("Download Top Frequencies (.xlsx)", id="download-button"),
    dcc.Download(id="download")
])

@app.callback(
    Output("raw-plot", "figure"),
    Output("windowed-plot", "figure"),
    Output("fft-output", "children"),
    Input("range-slider", "value")
)
def update_graph_and_fft(index_range):
    global top_freq_df

    i_start, i_end = index_range
    if i_end - i_start < MIN_SAMPLES:
        return go.Figure(), go.Figure(), html.Div("⚠️ Select at least 256 samples.")

    df_sel = df.iloc[i_start:i_end + 1].copy()
    timestamps = df_sel['timestamp'].values
    signal_len = len(df_sel)
    window = windows.hann(signal_len)

    # --- Raw Plot ---
    raw_fig = go.Figure()
    for axis in axis_columns:
        raw_fig.add_trace(go.Scatter(x=timestamps, y=df_sel[axis].values, mode='lines', name=f"{axis} (raw)"))
    raw_fig.update_layout(title="Raw Signal", xaxis_title="Time", yaxis_title="Amplitude")

    # --- Windowed Plot ---
    windowed_fig = go.Figure()
    for axis in axis_columns:
        detrended = df_sel[axis].values - np.mean(df_sel[axis].values)
        windowed_signal = detrended * window
        windowed_fig.add_trace(go.Scatter(x=timestamps, y=windowed_signal, mode='lines', name=f"{axis} (windowed)"))
    windowed_fig.update_layout(title="Hanning Windowed Signal", xaxis_title="Time", yaxis_title="Amplitude")

    # --- Frequency Extraction ---
    freqs = rfftfreq(PADDED_SIZE, d=DT)
    top_freq_dict = {}

    for axis in axis_columns:
        signal = df_sel[axis].values - np.mean(df_sel[axis].values)
        windowed = signal * window
        fft_vals = np.abs(rfft(windowed, n=PADDED_SIZE))
        top_idx = np.argsort(fft_vals)[-5:][::-1]
        top_freqs = np.round(freqs[top_idx], 2)
        top_freq_dict[axis_map[axis]] = top_freqs

    # Build summary table
    top_freq_df = pd.DataFrame(top_freq_dict, index=[f"f{i+1}" for i in range(5)]).reset_index()
    top_freq_df.rename(columns={"index": "Top freq."}, inplace=True)

    freq_table_display = dash_table.DataTable(
        data=top_freq_df.to_dict("records"),
        columns=[{"name": col, "id": col} for col in top_freq_df.columns],
        style_cell={'textAlign': 'center'},
        style_header={'fontWeight': 'bold'},
        style_table={'marginTop': '20px'}
    )

    return raw_fig, windowed_fig, freq_table_display

@app.callback(
    Output("download", "data"),
    Input("download-button", "n_clicks"),
    prevent_initial_call=True
)
def download_top_freqs(n_clicks):
    global top_freq_df
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        top_freq_df.to_excel(writer, index=False, sheet_name="Top Frequencies")
    buffer.seek(0)
    return dcc.send_bytes(buffer.read(), filename="top_frequencies.xlsx")

if __name__ == '__main__':
    app.run(debug=True)
