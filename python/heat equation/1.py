import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

FILEPATH = "данныепроекта.xlsx"

YEARS = [2021, 2024]

DATE_RANGE = {
    2021: ("2021-02-01", "2021-05-01"),
    2024: ("2024-02-01", "2024-05-01")
}

REGIONS = ["KZ-ATY", "KZ-ZAP", "KZ-AKT", "KZ-KUS", "KZ-SEV"]

# СЕТКА ПО ГЛУБИНЕ
L = 1.0
dz = 0.02
z = np.arange(0, L + dz, dz)
Nz = len(z)

dt = 24 * 3600  # сутки

# ТЕПЛОФИЗИЧЕСКИЕ ПАРАМЕТРЫ
KAPPA_BY_REGION = {
    "KZ-SEV": 0.90e-6,
    "KZ-KUS": 0.90e-6,
    "KZ-AKT": 0.70e-6,
    "KZ-ATY": 0.65e-6,
    "KZ-ZAP": 0.65e-6
}
DEFAULT_KAPPA = 0.75e-6

KAPPA_FACTOR_BY_SOILCODE = {
    0: 0.80, 1: 1.00, 2: 1.10, 3: 1.20,
    4: 0.85, 5: 0.85, 6: 0.90, 7: 0.90,
    8: 0.95, 9: 0.90
}

k_snow = 6.0

def to_num(s):
    return pd.to_numeric(s, errors="coerce")

def surface_bc(row):
    if pd.notna(row["t_soil_mean"]):
        return row["t_soil_mean"]
    H = row["snow_height_cm"] / 100 if pd.notna(row["snow_height_cm"]) else 0.0
    return row["t_air_mean"] * np.exp(-k_snow * H)

def build_kappa(row):
    base = KAPPA_BY_REGION.get(row["region"], DEFAULT_KAPPA)
    code = row["soil_code"]
    factor = KAPPA_FACTOR_BY_SOILCODE.get(int(code), 1.0) if pd.notna(code) else 1.0
    return base * factor

def solve_step(Tn, Tsurf, kappa):
    r = kappa * dt / dz**2
    A = np.zeros((Nz, Nz))
    b = np.zeros(Nz)

    # верхняя граница
    A[0, 0] = 1.0
    b[0] = Tsurf

    # внутренние узлы
    for i in range(1, Nz - 1):
        A[i, i - 1] = -r
        A[i, i] = 1 + 2 * r
        A[i, i + 1] = -r
        b[i] = Tn[i]

    # нижняя граница (нулевой поток)
    A[-1, -1] = 1.0
    A[-1, -2] = -1.0
    b[-1] = 0.0

    return np.linalg.solve(A, b)

def freezing_depth(T):
    for i in range(1, len(T)):
        if T[i] <= 0 < T[i - 1]:
            return z[i - 1]
    return np.nan

# ВЫБОР 1 РЕПРЕЗЕНТАТИВНОЙ СТАНЦИИ
KEY_COLS = ["t_air_mean", "t_soil_mean", "snow_height_cm"]

def select_one_station(df, region):
    dfr = df[df["region"] == region]

    miss = (
        dfr.groupby("station_id")[KEY_COLS]
        .apply(lambda x: x.isna().mean().mean())
        .rename("miss_frac")
    )

    snow_med = (
        dfr.groupby("station_id")["snow_height_cm"]
        .median()
        .rename("snow_med")
    )

    stats = pd.concat([miss, snow_med], axis=1).reset_index()
    reg_snow_med = stats["snow_med"].median()
    stats["snow_dist"] = (stats["snow_med"] - reg_snow_med).abs()

    stats = stats.sort_values(["miss_frac", "snow_dist"])
    return stats["station_id"].iloc[0]


df = pd.read_excel(FILEPATH)

df = df.rename(columns={
    "Регион": "region",
    "Станция_айди": "station_id",
    "Дата": "date",
    "Средтемпвоздуха": "t_air_mean",
    "Средтемппочвы": "t_soil_mean",
    "Высотапокровасм": "snow_height_cm",
    "Шифрпочвы": "soil_code"
})

df["date"] = pd.to_datetime(df["date"], errors="coerce")
df = df.dropna(subset=["date"])

# ВАЖНО: принудительно суточная дискретизация
df["date"] = df["date"].dt.floor("D")

df = df[df["region"].isin(REGIONS)]


for c in ["t_air_mean", "t_soil_mean", "snow_height_cm", "soil_code"]:
    df[c] = to_num(df[c])


for reg in REGIONS:

    fig, axes = plt.subplots(
        nrows=3, ncols=2,
        figsize=(20, 12),
        sharex=False
    )

    fig.suptitle(
        f"1D тепловая модель сезонного оттаивания почвы\nРегион: {reg}",
        fontsize=14
    )

    for col, year in enumerate(YEARS):

        date_start, date_end = DATE_RANGE[year]

        dfy = df.copy()
        dfy = dfy[dfy["date"].dt.year == year]
        dfy = dfy[(dfy["date"] >= date_start) & (dfy["date"] <= date_end)]
        dfy = dfy[dfy["region"] == reg]

        if dfy.empty:
            continue

        station = select_one_station(dfy, reg)

        dfs = dfy[dfy["station_id"] == station]
        
        dfd = (
            dfs.groupby("date", as_index=False)
            .agg({
                "t_air_mean": "mean",
                "t_soil_mean": "mean",
                "snow_height_cm": "mean",
                "soil_code": "median"
            })
        )
        dfd["region"] = reg

        dfd["Tsurf"] = dfd.apply(surface_bc, axis=1).interpolate()
        dfd["kappa"] = dfd.apply(build_kappa, axis=1)

        # начальное условие
        T = np.full(Nz, dfd["Tsurf"].iloc[0])
        profiles, depths = [], []

        for _, row in dfd.iterrows():
            T = solve_step(T, row["Tsurf"], row["kappa"])
            profiles.append(T.copy())
            depths.append(freezing_depth(T))

        profiles = np.array(profiles)

        # 1. Температуры
        ax = axes[0, col]
        for d in [0.0, 0.1, 0.3, 0.5, 1.0]:
            idx = int(d / dz)
            ax.plot(dfd["date"], profiles[:, idx], label=f"{d} м")

        ax.axhline(0, linestyle="--", color="black")
        ax.set_title(f"{year}, станция {station}")
        ax.set_ylabel("T, °C")
        ax.grid(False)
        ax.legend(fontsize=8)

        # 2. Глубина 0°C
        ax = axes[1, col]
        ax.plot(dfd["date"], depths, color="black", linewidth=2)
        ax.set_ylabel("Глубина, м")
        ax.grid(False)

        # 3. Heatmap
        ax = axes[2, col]
        extent = [
            mdates.date2num(dfd["date"].iloc[0]),
            mdates.date2num(dfd["date"].iloc[-1]),
            z[-1], z[0]
        ]

        im = ax.imshow(
            profiles.T,
            aspect="auto",
            cmap="viridis",
            extent=extent,
            interpolation="nearest"
        )

        ax.plot(dfd["date"], depths, color="white", linewidth=2)
        ax.set_xlabel("Дата")
        ax.set_ylabel("Глубина, м")

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.savefig(f"heatmaps_{reg}_2021_vs_2024.png", dpi=300)
    plt.close()





  
# draft 1
# import numpy as np
# import pandas as pd
# import matplotlib.pyplot as plt
# import matplotlib.dates as mdates

# FILEPATH = "данныепроекта.xlsx"
# YEAR = 2021

# DATE_START = f"{YEAR}-02-01"
# DATE_END   = f"{YEAR}-05-01"

# REGIONS = ["KZ-ATY", "KZ-ZAP", "KZ-AKT", "KZ-KUS", "KZ-SEV"]

# L = 1.0
# dz = 0.02
# z = np.arange(0, L + dz, dz)
# Nz = len(z)

# dt = 24 * 3600  # сутки

# KAPPA_BY_REGION = {
#     "KZ-SEV": 0.90e-6,
#     "KZ-KUS": 0.90e-6,
#     "KZ-AKT": 0.70e-6,
#     "KZ-ATY": 0.65e-6,
#     "KZ-ZAP": 0.65e-6
# }
# DEFAULT_KAPPA = 0.75e-6

# KAPPA_FACTOR_BY_SOILCODE = {
#     0: 0.80, 1: 1.00, 2: 1.10, 3: 1.20,
#     4: 0.85, 5: 0.85, 6: 0.90, 7: 0.90,
#     8: 0.95, 9: 0.90
# }

# k_snow = 6.0

# # ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# def to_num(s):
#     return pd.to_numeric(s, errors="coerce")

# def surface_bc(row):
#     if pd.notna(row["t_soil_mean"]):
#         return row["t_soil_mean"]
#     H = row["snow_height_cm"] / 100 if pd.notna(row["snow_height_cm"]) else 0
#     return row["t_air_mean"] * np.exp(-k_snow * H)

# def build_kappa(row):
#     base = KAPPA_BY_REGION.get(row["region"], DEFAULT_KAPPA)
#     code = row["soil_code"]
#     factor = KAPPA_FACTOR_BY_SOILCODE.get(int(code), 1.0) if pd.notna(code) else 1.0
#     return base * factor

# def solve_step(Tn, Tsurf, kappa):
#     r = kappa * dt / dz**2
#     A = np.zeros((Nz, Nz))
#     b = np.zeros(Nz)

#     A[0, 0] = 1.0
#     b[0] = Tsurf

#     for i in range(1, Nz - 1):
#         A[i, i - 1] = -r
#         A[i, i] = 1 + 2 * r
#         A[i, i + 1] = -r
#         b[i] = Tn[i]

#     A[-1, -1] = 1.0
#     A[-1, -2] = -1.0
#     b[-1] = 0.0

#     return np.linalg.solve(A, b)

# def freezing_depth(T):
#     for i in range(1, len(T)):
#         if T[i] <= 0 < T[i - 1]:
#             return z[i - 1]
#     return np.nan

# # ЗАГРУЗКА ДАННЫХ
# df = pd.read_excel(FILEPATH)

# df = df.rename(columns={
#     "Регион": "region",
#     "Станция_айди": "station_id",
#     "Дата": "date",
#     "Средтемпвоздуха": "t_air_mean",
#     "Средтемппочвы": "t_soil_mean",
#     "Высотапокровасм": "snow_height_cm",
#     "Шифрпочвы": "soil_code"
# })

# df["date"] = pd.to_datetime(df["date"], errors="coerce")
# df = df.dropna(subset=["date"])

# df = df[df["date"].dt.year == YEAR]
# df = df[(df["date"] >= DATE_START) & (df["date"] <= DATE_END)]
# df = df[df["region"].isin(REGIONS)]

# for c in ["t_air_mean", "t_soil_mean", "snow_height_cm", "soil_code"]:
#     df[c] = to_num(df[c])

# # ВЫБОР 2 РЕПРЕЗЕНТАТИВНЫХ СТАНЦИЙ НА РЕГИОН
# selected = {}

# KEY_COLS = ["t_air_mean", "t_soil_mean", "snow_height_cm"]

# for reg in REGIONS:
#     dfr = df[df["region"] == reg]

#     # доля пропусков
#     miss = (
#         dfr.groupby("station_id")[KEY_COLS]
#         .apply(lambda x: x.isna().mean().mean())
#         .rename("miss_frac")
#     )

#     # медиана снега
#     snow_med = (
#         dfr.groupby("station_id")["snow_height_cm"]
#         .median()
#         .rename("snow_med")
#     )

#     stats = pd.concat([miss, snow_med], axis=1).reset_index()

#     reg_snow_med = stats["snow_med"].median()
#     stats["snow_dist"] = (stats["snow_med"] - reg_snow_med).abs()

#     stats = stats.sort_values(["miss_frac", "snow_dist"])
#     selected[reg] = stats["station_id"].iloc[:2].tolist()

# print("Выбранные репрезентативные станции:")
# for r, s in selected.items():
#     print(r, "→", s)

# # МОДЕЛИРОВАНИЕ И ГРАФИКИ
# for reg in REGIONS:

#     # Для каждого региона выбираем одну станцию за 2021 и одну за 2024
#     stations_2021 = selected[reg]  # Станции для 2021 года
#     stations_2024 = selected[reg]  # Станции для 2024 года (или другой способ выбора станций для 2024)

#     fig, axes = plt.subplots(
#         nrows=3, ncols=2,
#         figsize=(20, 12),
#         sharex=False
#     )

#     fig.suptitle(
#         f"1D тепловая модель сезонного оттаивания почвы\nРегион: {reg}",
#         fontsize=14
#     )

#     # Станция для 2021 года (первый подграфик)
#     st_2021 = stations_2021[0]  # Первая станция для 2021 года
#     dfs_2021 = df[(df["region"] == reg) & (df["station_id"] == st_2021) & (df["date"].dt.year == 2021)]

#     dfd_2021 = (
#         dfs_2021.groupby("date", as_index=False)
#         .agg({
#             "t_air_mean": "mean",
#             "t_soil_mean": "mean",
#             "snow_height_cm": "mean",
#             "soil_code": "median"
#         })
#     )
#     dfd_2021["region"] = reg

#     dfd_2021["Tsurf"] = dfd_2021.apply(surface_bc, axis=1).interpolate()
#     dfd_2021["kappa"] = dfd_2021.apply(build_kappa, axis=1)

#     T_2021 = np.full(Nz, dfd_2021["Tsurf"].iloc[0])
#     profiles_2021, depths_2021 = [], []

#     for _, row in dfd_2021.iterrows():
#         T_2021 = solve_step(T_2021, row["Tsurf"], row["kappa"])
#         profiles_2021.append(T_2021.copy())
#         depths_2021.append(freezing_depth(T_2021))

#     profiles_2021 = np.array(profiles_2021)

#     # 1) Температура на глубинах для 2021
#     ax_2021 = axes[0, 0]
#     for d in [0.0, 0.1, 0.3, 0.5, 1.0]:
#         idx = int(d / dz)
#         ax_2021.plot(dfd_2021["date"], profiles_2021[:, idx], label=f"{d} м")

#     ax_2021.axhline(0, linestyle="--", color="black")
#     ax_2021.set_title(f"Станция {st_2021} (2021)\nТемпература на глубинах")
#     ax_2021.set_ylabel("T, °C")
#     ax_2021.grid(True)
#     ax_2021.legend(fontsize=8)

#     # 2) Глубина изотермы 0°C для 2021
#     ax_2021_depth = axes[1, 0]
#     ax_2021_depth.plot(dfd_2021["date"], depths_2021, color="black", linewidth=2)
#     ax_2021_depth.set_title("Глубина границы 0°C (2021)")
#     ax_2021_depth.set_ylabel("Глубина, м")
#     ax_2021_depth.grid(True)

#     # 3) Heatmap T(z,t) для 2021
#     ax_2021_heatmap = axes[2, 0]
#     extent_2021 = [
#         mdates.date2num(dfd_2021["date"].iloc[0]),
#         mdates.date2num(dfd_2021["date"].iloc[-1]),
#         z[-1], z[0]
#     ]

#     im_2021 = ax_2021_heatmap.imshow(
#         profiles_2021.T,
#         aspect="auto",
#         cmap="viridis",
#         extent=extent_2021,
#         interpolation="nearest"
#     )

#     ax_2021_heatmap.plot(dfd_2021["date"], depths_2021, color="white", linewidth=2, label="T=0°C")
#     ax_2021_heatmap.set_title(f"T(z,t) heatmap (2021)")
#     ax_2021_heatmap.set_xlabel("Дата")
#     ax_2021_heatmap.set_ylabel("Глубина, м")
#     ax_2021_heatmap.legend()

#     # Станция для 2024 года (второй подграфик)
#     st_2024 = stations_2024[0]  # Первая станция для 2024 года (можно изменить по аналогии с 2021)
#     dfs_2024 = df[(df["region"] == reg) & (df["station_id"] == st_2024) & (df["date"].dt.year == 2024)]

#     dfd_2024 = (
#         dfs_2024.groupby("date", as_index=False)
#         .agg({
#             "t_air_mean": "mean",
#             "t_soil_mean": "mean",
#             "snow_height_cm": "mean",
#             "soil_code": "median"
#         })
#     )
#     dfd_2024["region"] = reg

#     dfd_2024["Tsurf"] = dfd_2024.apply(surface_bc, axis=1).interpolate()
#     dfd_2024["kappa"] = dfd_2024.apply(build_kappa, axis=1)

#     T_2024 = np.full(Nz, dfd_2024["Tsurf"].iloc[0])
#     profiles_2024, depths_2024 = [], []

#     for _, row in dfd_2024.iterrows():
#         T_2024 = solve_step(T_2024, row["Tsurf"], row["kappa"])
#         profiles_2024.append(T_2024.copy())
#         depths_2024.append(freezing_depth(T_2024))

#     profiles_2024 = np.array(profiles_2024)

#     # 1) Температура на глубинах для 2024
#     ax_2024 = axes[0, 1]
#     for d in [0.0, 0.1, 0.3, 0.5, 1.0]:
#         idx = int(d / dz)
#         ax_2024.plot(dfd_2024["date"], profiles_2024[:, idx], label=f"{d} м")

#     ax_2024.axhline(0, linestyle="--", color="black")
#     ax_2024.set_title(f"Станция {st_2024} (2024)\nТемпература на глубинах")
#     ax_2024.set_ylabel("T, °C")
#     ax_2024.grid(True)
#     ax_2024.legend(fontsize=8)

#     # 2) Глубина изотермы 0°C для 2024
#     ax_2024_depth = axes[1, 1]
#     ax_2024_depth.plot(dfd_2024["date"], depths_2024, color="black", linewidth=2)
#     ax_2024_depth.set_title("Глубина границы 0°C (2024)")
#     ax_2024_depth.set_ylabel("Глубина, м")
#     ax_2024_depth.grid(True)

#     # 3) Heatmap T(z,t) для 2024
#     ax_2024_heatmap = axes[2, 1]
#     extent_2024 = [
#         mdates.date2num(dfd_2024["date"].iloc[0]),
#         mdates.date2num(dfd_2024["date"].iloc[-1]),
#         z[-1], z[0]
#     ]

#     im_2024 = ax_2024_heatmap.imshow(
#         profiles_2024.T,
#         aspect="auto",
#         cmap="viridis",
#         extent=extent_2024,
#         interpolation="nearest"
#     )

#     ax_2024_heatmap.plot(dfd_2024["date"], depths_2024, color="white", linewidth=2, label="T=0°C")
#     ax_2024_heatmap.set_title(f"T(z,t) heatmap (2024)")
#     ax_2024_heatmap.set_xlabel("Дата")
#     ax_2024_heatmap.set_ylabel("Глубина, м")
#     ax_2024_heatmap.legend()

#     plt.tight_layout(rect=[0, 0, 1, 0.95])

#     filename = f"heatmaps_{reg}_2021_2024.png"
#     plt.savefig(filename, dpi=300) 
#     plt.close() и

#     plt.tight_layout(rect=[0, 0, 1, 0.95])
#     filename = f"heatmaps_{reg}_{YEAR}.png"
#     plt.savefig(filename, dpi=300) 
#     plt.close() и
