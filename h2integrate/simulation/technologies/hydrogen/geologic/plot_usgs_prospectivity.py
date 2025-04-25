from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt


ROOT = Path(__file__).parent

if __name__ == "__main__":
    map_path = ROOT / "usgs/cos.csv"
    p_map = np.loadtxt(map_path, skiprows=6, delimiter=",")
    p_map[p_map == -9999] = 0
    p_map = np.flipud(map)

    plt.set_cmap("viridis_r")
    plt.contourf(p_map, levels=256)
    plt.show()
