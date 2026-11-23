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
    fig, ax1 = plt.subplots(figsize=(8, 3.8), dpi=200)

    runs = ['Run 1 (25m)', 'Run 2 (35m)', 'Run 3 (15 deg Skew)', 'Run 4 (Restored 25m)']
    depths = [1390.0, 1950.0, 1950.0, 1390.0]
    keys_count = [1066, 1070, 1070, 1066]

    color1 = '#1f77b4'
    ax1.set_xlabel('Consecutive Execution Session Runs', fontsize=10, fontweight='bold')
    ax1.set_ylabel('Girder Depth D (mm)', color=color1, fontsize=10, fontweight='bold')
    l1 = ax1.plot(runs, depths, color=color1, marker='o', linewidth=2.5, markersize=8, label='Girder Depth D (mm)')
    ax1.tick_params(axis='y', labelcolor=color1)
    ax1.set_ylim(1200, 2100)

    ax2 = ax1.twinx()
    color2 = '#2ca02c'
    ax2.set_ylabel('Output Dictionary Key Count', color=color2, fontsize=10, fontweight='bold')
    l2 = ax2.plot(runs, keys_count, color=color2, marker='s', linewidth=2.0, linestyle='--', markersize=7, label='Output Dict Keys')
    ax2.tick_params(axis='y', labelcolor=color2)
    ax2.set_ylim(1000, 1120)

    lines = l1 + l2
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc='center right', fontsize=9)
    ax1.set_title('Multi-Run State Persistence: Section Scaling & Key Stability (TC-04)', fontsize=11, fontweight='bold')
    ax1.grid(True, linestyle=':', alpha=0.6)

    plt.tight_layout()
    fig_path = Path(__file__).resolve().parent / 'figures' / 'fig_multirun_persistence.png'
    fig_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(fig_path)
    plt.close()
    print(f'Successfully regenerated: {fig_path} (Size: {fig_path.stat().st_size} bytes)')

if __name__ == '__main__':
    generate_multirun_persistence_plot()
