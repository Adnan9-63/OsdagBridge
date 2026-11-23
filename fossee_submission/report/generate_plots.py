import os
import sys
from pathlib import Path

# Ensure conda env DLLs are in PATH for Windows
conda_lib_bin = r'C:\Users\ADNAN\anaconda3\envs\osdagbridge-env\Library\bin'
if os.path.exists(conda_lib_bin):
    os.environ['PATH'] = conda_lib_bin + os.pathsep + os.environ.get('PATH', '')

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def generate_multirun_persistence_plot():
    # Academic publication styling
    plt.rcParams.update({
        'font.family': 'serif',
        'font.size': 9,
        'axes.labelsize': 10,
        'axes.titlesize': 10,
        'xtick.labelsize': 8.5,
        'ytick.labelsize': 8.5,
        'legend.fontsize': 8.5,
        'figure.titlesize': 11
    })

    fig, ax1 = plt.subplots(figsize=(7.2, 3.2), dpi=300)
    fig.patch.set_facecolor('white')
    ax1.set_facecolor('white')

    runs = ['Run 1 (25m)', 'Run 2 (35m)', 'Run 3 (15 deg Skew)', 'Run 4 (25m Reload)']
    depths = [1390.0, 1950.0, 1950.0, 1390.0]
    keys_count = [1066, 1070, 1070, 1066]

    color_depth = '#1f2937'  # Dark charcoal
    ax1.set_xlabel('Consecutive Execution Session Runs', fontweight='semibold', labelpad=6)
    ax1.set_ylabel('Girder Depth D (mm)', color=color_depth, fontweight='semibold')
    l1 = ax1.plot(runs, depths, color=color_depth, marker='o', linewidth=1.8, markersize=6, label='Girder Depth D (mm)')
    ax1.tick_params(axis='y', labelcolor=color_depth)
    ax1.set_ylim(1200, 2150)

    ax2 = ax1.twinx()
    color_keys = '#4b5563'  # Muted slate
    ax2.set_ylabel('Output Dictionary Key Count', color=color_keys, fontweight='semibold')
    l2 = ax2.plot(runs, keys_count, color=color_keys, marker='s', linewidth=1.5, linestyle='--', markersize=5.5, label='Output Dict Keys')
    ax2.tick_params(axis='y', labelcolor=color_keys)
    ax2.set_ylim(1020, 1100)

    lines = l1 + l2
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc='center right', framealpha=0.9, edgecolor='#d1d5db')
    ax1.set_title('Multi-Run State Persistence: Girder Depth & Key Stability (TC-04)', pad=8, fontweight='semibold')
    ax1.grid(True, linestyle=':', color='#e5e7eb', linewidth=0.8)

    plt.tight_layout()
    fig_path = Path(__file__).resolve().parent / 'figures' / 'fig_multirun_persistence.png'
    fig_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(fig_path, dpi=300)
    plt.close()
    print(f'Successfully regenerated: {fig_path} (Size: {fig_path.stat().st_size} bytes)')

if __name__ == '__main__':
    generate_multirun_persistence_plot()
