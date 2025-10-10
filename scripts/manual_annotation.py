#MPLBACKEND=TkAgg python manual.py

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import SpanSelector, Button
import matplotlib.dates as mdates

# Optional: SciPy improves spectrogram quality/performance
try:
    from scipy.signal import spectrogram as sp_spectrogram
    HAVE_SCIPY = True
except Exception:
    HAVE_SCIPY = False

FS_ACC = 200.0  # accelerometer sampling rate

ACC_CHANNELS = [
    # uncomment as needed
    # "top.x", "top.y", "top.z",
    # "back.x", "back.y", "back.z",
    # "side.x", "side.y", "side.z"
    "side.x"
]

# Collect CSV files
# csv_files = [f for f in os.listdir() if f.endswith('.csv')]
csv_files = []
annotated_twins = set()

def is_valid_cycle_csv(root, fname):
    if not fname.endswith(".csv"):
        return False
    if fname.startswith("annotated_"):
        return False
    if fname.startswith("._"):               # macOS AppleDouble
        return False
    if fname.endswith("_metadata.csv"):      # metadata files
        return False
    base = os.path.basename(fname)
    if not base.startswith("wm_"):           # only washing-machine general files
        return False
    # optional: skip eco (40–60) here if you never want to annotate them
    # if os.path.sep + "eco" + os.path.sep in os.path.join(root, fname):
    #     return False
    return True

for root, dirs, files in os.walk("laboratory/washing_machine"):
    for f in files:
        full = os.path.join(root, f)

        # track “annotated_*.csv” to exclude their twins
        if f.startswith("annotated_") and f.endswith(".csv"):
            twin = os.path.join(root, f[len("annotated_"):])
            annotated_twins.add(os.path.normpath(twin))
            continue

        # keep only valid raw cycle csv
        if is_valid_cycle_csv(root, f):
            csv_files.append(os.path.normpath(full))

# Keep only raw files that do NOT have an annotated twin
csv_files = [p for p in csv_files if p not in annotated_twins]

# print(f"Pending CSVs to annotate: {len(csv_files)}")
csv_index = 0

# Globals
df = None
df_acc = None
fig = None
ax_power = None
ax_water = None
axes_specs = {}
span = None
label_column = 'centrifuge_label'
save_button = None
next_button = None


# -------- Timestamp helpers --------
def _to_utc_naive(ts: pd.Series) -> pd.Series:
    ts = pd.to_datetime(ts, utc=True, errors='coerce')
    return ts.dt.tz_localize(None)

def _csv_timestamp_to_utc_naive(s: pd.Series) -> pd.Series:
    s_num = pd.to_numeric(s, errors='coerce')
    ts = pd.to_datetime(s_num, unit='s', utc=True)
    return ts.dt.tz_localize(None)

def align_csv_to_acc(csv_ts, t_csv0, t_csv1, t_acc0, t_acc1):
    if t_csv1 == t_csv0:
        return pd.Series([t_acc0] * len(csv_ts))
    frac = (csv_ts - t_csv0) / (t_csv1 - t_csv0)
    return t_acc0 + frac * (t_acc1 - t_acc0)


# -------- Plotting helpers --------
def _spectrogram(ax_plot, ts0_naive, x, fs, title, cax=None, fmax=2000):
    x = pd.to_numeric(x, errors='coerce').to_numpy(np.float64)
    x = np.nan_to_num(x, nan=0.0, posinf=0.0, neginf=0.0)

    nfft = int(max(64, min(4096, round(fs * 2.0))))
    noverlap = int(nfft // 2)

    if HAVE_SCIPY:
        f, t, Sxx = sp_spectrogram(x, fs=fs, nperseg=nfft, noverlap=noverlap,
                                   scaling='spectrum', mode='psd')
    else:
        from matplotlib.mlab import specgram as mpl_specgram
        Sxx, f, t = mpl_specgram(x, NFFT=nfft, Fs=fs, noverlap=noverlap)

    t_dt = ts0_naive + pd.to_timedelta(t, unit='s')
    Sxx_db = 10.0 * np.log10(np.maximum(Sxx, np.finfo(float).eps))

    mesh = ax_plot.pcolormesh(t_dt, f, Sxx_db, shading='auto')
    ax_plot.set_title(title, fontsize=9)
    ax_plot.set_ylabel('Freq (Hz)')
    ax_plot.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
    ax_plot.set_ylim(0, min(fmax, np.max(f)))

    if cax is not None:
        cax.cla()
        cbar = plt.colorbar(mesh, cax=cax)
        cbar.set_label('Power (dB)', fontsize=8)


def _overlay_power(ax_spec, ts_naive, power):
    # Reuse a single twin y-axis per spectrogram axis
    ax_r = getattr(ax_spec, "_power_twin", None)
    if ax_r is None or ax_r.figure is None:
        ax_r = ax_spec.twinx()
        ax_spec._power_twin = ax_r
    else:
        ax_r.cla()  # clear previous contents when loading the next file

    ax_r.plot(ts_naive, power, lw=1, alpha=0.8, color='red')
    ax_r.set_ylabel('Power')
    ax_r.grid(False)
    ax_r.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
    return ax_r

def load_file(index):
    global df, df_acc

    filename = csv_files[index]
    raw = pd.read_csv(filename)
    df = raw.copy()
    cutoff = 0
    
    if len(df) < 6000:
        cutoff = 0
    else:
        cutoff = 0.5
    
    # build timestamp
    df["temporary_timestamp"] = _csv_timestamp_to_utc_naive(df['timestamp'])

    if label_column not in df.columns:
        df[label_column] = 0

    # -------- restrict display to last 40% --------
    n = len(df)
    start_idx = int(n * cutoff)
    df_view = df.iloc[start_idx:]
    tmin, tmax = df_view["temporary_timestamp"].iloc[0], df_view["temporary_timestamp"].iloc[-1]

    # --- Power plot ---
    ax_power.clear()
    ax_power.plot(df_view['temporary_timestamp'], df_view['power'], label='Power')
    ax_power.set_title(f"{filename} (Drag to annotate)")
    ax_power.set_xlabel("Time (UTC)")
    ax_power.set_ylabel("Power")
    ax_power.legend(loc='upper right')
    ax_power.set_xlim(tmin, tmax)
    ax_power.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))

    # --- Water plot ---
    ax_water.clear()
    if 'water_inlet' in df.columns and 'water_outlet' in df.columns:
        ax_water.plot(df_view['temporary_timestamp'], df_view['water_inlet'], label='Water Inlet', color='blue')
        ax_water.plot(df_view['temporary_timestamp'], df_view['water_outlet'], label='Water Outlet', color='green')
    ax_water.plot(df_view['temporary_timestamp'], df_view['power'], label='Power', color='red', alpha=0.5)
    ax_water.set_title("Water inlet/outlet vs Power")
    ax_water.set_ylabel("Value")
    ax_water.legend(loc='upper right')
    ax_water.set_xlim(tmin, tmax)
    ax_water.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))

    # --- Load accelerometer parquet ---
    rel_path = os.path.relpath(filename, "laboratory")  
    base, _ = os.path.splitext(rel_path)
    acc_path = os.path.join("acc", "laboratory", f"{base}_acc.parquet")
    print(f"Looking for accel data at: {acc_path}")

    if not os.path.exists(acc_path):
        for ch in ACC_CHANNELS:
            ax, _ = axes_specs[ch]
            ax.clear()
            ax.text(0.5, 0.5, "No parquet found", ha="center", va="center", transform=ax.transAxes)
        plt.draw()
        return

    df_acc = pd.read_parquet(acc_path)
    acc_ts = _to_utc_naive(df_acc['timestamp'])

    # -------- restrict accelerometer to last 40% --------
    n_acc = len(df_acc)
    acc_start = int(n_acc * cutoff)
    df_acc_view = df_acc.iloc[acc_start:]
    acc_ts_view = acc_ts.iloc[acc_start:]
    ts0 = acc_ts_view.iloc[0]

    # Align CSV timestamps to accel timeline (use full df here, not df_view)
    t_csv0, t_csv1 = df['temporary_timestamp'].iloc[0], df['temporary_timestamp'].iloc[-1]
    t_acc0, t_acc1 = acc_ts.iloc[0], acc_ts.iloc[-1]
    df['timestamp_aligned'] = align_csv_to_acc(df['temporary_timestamp'], t_csv0, t_csv1, t_acc0, t_acc1)

    # --- Spectrograms ---
    for ch in ACC_CHANNELS:
        ax, cax = axes_specs[ch]
        ax.clear()
        if ch in df_acc_view.columns:
            _spectrogram(ax, ts0, df_acc_view[ch], FS_ACC, f"Spectrogram: {ch}", cax=cax)
            _overlay_power(ax, df['timestamp_aligned'], df['power'])
            ax.set_xlim(tmin, tmax)
        else:
            ax.text(0.5, 0.5, f"{ch} missing", ha="center", va="center", transform=ax.transAxes)

    plt.draw()



# -------- Annotation tools --------
def onselect(xmin, xmax):
    tmin = pd.to_datetime(mdates.num2date(xmin)).tz_localize(None)
    tmax = pd.to_datetime(mdates.num2date(xmax)).tz_localize(None)
    mask = (df['temporary_timestamp'] >= tmin) & (df['temporary_timestamp'] <= tmax)
    df.loc[mask, label_column] = 1
    print(f"Marked: {tmin} → {tmax} ({mask.sum()} points)")
    ax_power.axvspan(tmin, tmax, color='red', alpha=0.3)
    plt.draw()

def save_callback(event):
    filename = csv_files[csv_index]  # e.g. laboratory/.../eco/wm_foo.csv
    folder = os.path.dirname(filename)
    basename = os.path.basename(filename)

    out_name = f"annotated_{basename}"
    out_path = os.path.join(folder, out_name) if folder else out_name

    df_out = df.copy()
    df_out.drop(columns=[c for c in ["temporary_timestamp", "timestamp_aligned"] if c in df_out],
                inplace=True)

    df_out.to_csv(out_path, index=False)
    
    
    
    print(f"✅ Saved to {out_path}")


def next_callback(event):
    global csv_index
    save_callback(None)
    csv_index += 1
    if csv_index < len(csv_files):
        load_file(csv_index)
        print(f"➡️ Loaded: {csv_files[csv_index]}")
    else:
        print("🎉 All files annotated!")
        plt.close()


# -------- Layout --------
nrows = 2 + len(ACC_CHANNELS)  # power row + water row + spectrograms

fig = plt.figure(figsize=(15, 2*nrows))
gs = fig.add_gridspec(
    nrows=nrows, ncols=2,
    width_ratios=[50, 1],
    height_ratios=[1.5, 1.5] + [1]*len(ACC_CHANNELS)
)

ax_power = fig.add_subplot(gs[0, 0])
ax_water = fig.add_subplot(gs[1, 0])
axes_specs = {}
for i, ch in enumerate(ACC_CHANNELS, start=2):
    ax = fig.add_subplot(gs[i, 0], sharex=ax_power)
    cax = fig.add_subplot(gs[i, 1])
    axes_specs[ch] = (ax, cax)

plt.subplots_adjust(bottom=0.25, hspace=0.6, wspace=0.05)

span = SpanSelector(ax_power, onselect, direction='horizontal',
                    useblit=False, props=dict(alpha=0.3, facecolor='red'),
                    interactive=True)

# Create Buttons and keep references
save_ax = plt.axes([0.70, 0.05, 0.10, 0.075])
next_ax = plt.axes([0.82, 0.05, 0.10, 0.075])
save_button = Button(save_ax, 'Save CSV')
next_button = Button(next_ax, 'Next')
save_button.on_clicked(save_callback)
next_button.on_clicked(next_callback)

# -------- Start --------
if csv_files:
    load_file(csv_index)
    print(f"🔄 Ready to annotate: {csv_files[csv_index]}")
else:
    print("⚠️ No CSV files found")

plt.show()