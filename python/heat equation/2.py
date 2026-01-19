import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from scipy.interpolate import interp1d

FILEPATH = "данныепроекта.xlsx"
YEARS = [2021, 2024]
DATE_RANGE = {
    2021: ("2021-02-01", "2021-05-01"),
    2024: ("2024-02-01", "2024-05-01")
}
REGIONS = ["KZ-ATY", "KZ-ZAP", "KZ-AKT", "KZ-KUS", "KZ-SEV"]

L = 1.0 
dz = 0.02
z = np.arange(0, L + dz, dz)
Nz = len(z)
dt = 24 * 3600  

KAPPA_BY_REGION = {
    "KZ-SEV": 0.90e-6, "KZ-KUS": 0.90e-6,  # черноземы
    "KZ-AKT": 0.70e-6, "KZ-ATY": 0.65e-6,  # каштановые/песчаные
    "KZ-ZAP": 0.65e-6
}
KAPPA_FACTOR_BY_SOILCODE = {0:0.80, 1:1.00, 2:1.10, 3:1.20, 4:0.85, 5:0.85, 6:0.90, 7:0.90, 8:0.95, 9:0.90}
k_snow = 6.0  # затухание T под снегом

# ФАЗОВЫЙ ПЕРЕХОД
L = 3.34e5      # Дж/кг (скрытая теплота)
rho_ice = 917   # кг/м³
C_soil = 2.0e6  # Дж/м³К

# ПАРАМЕТРЫ ДАРСИ ПО РЕГИОНАМ
DARSI_PARAMS = {
    "KZ-SEV": {"K_sat": 5.0, "psi_f": 25},   # черноземы
    "KZ-KUS": {"K_sat": 6.0, "psi_f": 22},
    "KZ-AKT": {"K_sat": 10.0, "psi_f": 15},  # каштановые
    "KZ-ATY": {"K_sat": 30.0, "psi_f": 10},  # песчаные
    "KZ-ZAP": {"K_sat": 15.0, "psi_f": 18}
}

def to_num(s):
    return pd.to_numeric(s, errors="coerce")

def surface_bc(row):
    """Граничное условие поверхности"""
    if pd.notna(row["t_soil_mean"]):
        return row["t_soil_mean"]
    H = row["snow_height_cm"] / 100 if pd.notna(row["snow_height_cm"]) else 0.0
    return row["t_air_mean"] * np.exp(-k_snow * H)

def build_kappa(row):
    base = KAPPA_BY_REGION.get(row["region"], 0.75e-6)
    code = row["soil_code"]
    factor = KAPPA_FACTOR_BY_SOILCODE.get(int(code), 1.0) if pd.notna(code) else 1.0
    return base * factor

def solve_step_stefan(Tn, Tsurf, kappa):
    """Неявная схема с фазовым переходом (энтальпия)"""
    r = kappa * dt / dz**2
    
    A = np.zeros((Nz, Nz))
    b = np.zeros(Nz)
    
    # Верх: Dirichlet T[0] = Tsurf
    A[0, 0] = 1.0
    b[0] = Tsurf
    
    # Низ: нулевой поток теплоизоляция
    A[-1, -1] = 1.0
    A[-1, -2] = -1.0
    b[-1] = 0.0
    
    # Внутренние точки
    for i in range(1, Nz-1):
        A[i, i-1] = -r
        A[i, i] = 1 + 2*r
        A[i, i+1] = -r
        b[i] = Tn[i]
    
    T_new = np.linalg.solve(A, b)
    return T_new

def freezing_depth(T):
    """Глубина изотермы 0°C"""
    for i in range(1, len(T)):
        if T[i-1] > 0 >= T[i]:  # переход через 0°C
            return z[i-1]
    return 0.0 if T[0] > 0 else np.nan

def melt_rate(T_prev, T_curr):
    """Интенсивность таяния мм/ч"""
    ice_prev = np.sum(T_prev < 0) * dz * rho_ice / 1000  # м вод. слоя
    ice_curr = np.sum(T_curr < 0) * dz * rho_ice / 1000
    return max(0, (ice_prev - ice_curr) * 24)  # мм/сутки

def green_ampt_infil(M_rate, Z_0C, region, F_cum):
    """Инфильтрация Green-Ampt (устойчивая реализация)"""
    params = DARSI_PARAMS[region]
    K_sat = params["K_sat"] / 24      # мм/ч
    psi_f = params["psi_f"] / 100     # м

    # Редукция по глубине талого слоя
    thawed_eff = min(1.0, Z_0C / 0.3) if Z_0C > 0 else 0.0
    K_red = K_sat * thawed_eff

    # защита от F = 0
    if F_cum <= 1e-6:
        f = K_red
    else:
        f = K_red * (psi_f + F_cum) / F_cum

    return min(f, M_rate)


def select_station(df, region):
    """Выбор репрезентативной станции"""
    dfr = df[df["region"] == region]
    if dfr.empty:
        return None
    
    miss_frac = dfr.groupby("station_id")[["t_air_mean", "t_soil_mean"]].apply(
        lambda x: x.isna().mean().mean()
    )
    snow_med = dfr.groupby("station_id")["snow_height_cm"].median()
    
    stats = pd.concat([miss_frac, snow_med], axis=1).dropna()
    return stats.index[0]

df = pd.read_excel(FILEPATH)
df = df.rename(columns={
    "Регион": "region", "Станция_айди": "station_id", "Дата": "date",
    "Средтемпвоздуха": "t_air_mean", "Средтемппочвы": "t_soil_mean",
    "Высотапокровасм": "snow_height_cm", "Шифрпочвы": "soil_code"
})

df["date"] = pd.to_datetime(df["date"]).dt.floor("D")
df = df[df["region"].isin(REGIONS)]

for col in ["t_air_mean", "t_soil_mean", "snow_height_cm", "soil_code"]:
    df[col] = to_num(df[col])

all_results = []

for reg in REGIONS:
    fig, axes = plt.subplots(4, 2, figsize=(16, 20))
    # fig.suptitle(f'КОСТАНАЙ 2024 vs 2021: Физика паводков\n(reg={reg})', fontsize=16)
    
    for col, year in enumerate(YEARS):
        date_start, date_end = DATE_RANGE[year]
        dfy = df[(df["date"].dt.year == year) & 
                (df["date"] >= date_start) & (df["date"] <= date_end) & 
                (df["region"] == reg)]
        
        if dfy.empty:
            continue
            
        station = select_station(dfy, reg)
        dfs = dfy
        
        dfd = dfs.groupby("date", as_index=False).agg({
            "t_air_mean": "mean",
            "t_soil_mean": "mean",
            "snow_height_cm": "mean",
            "soil_code": "median"
        })

        dfd["region"] = reg
        
        dfd["Tsurf"] = dfd.apply(surface_bc, axis=1).interpolate()
        dfd["kappa"] = dfd.apply(build_kappa, axis=1)
        
        # Heat 
        T = np.full(Nz, dfd["Tsurf"].iloc[0] - 5)  # холодное начальное
        profiles, depths, melt_rates, F_cum = [], [], [], 0
        
        for i, (_, row) in enumerate(dfd.iterrows()):
            T = solve_step_stefan(T, row["Tsurf"], row["kappa"])
            
            profiles.append(T.copy())
            depths.append(freezing_depth(T))
            
            # ТАЯНИЕ
            if i > 0:
                M = melt_rate(profiles[-2], T)
            else:
                M = 0
            melt_rates.append(M)
            
            # Green-Ampt кумулятив
            F_cum += M * 0.001  # м
            
            # ИНФИЛЬТРАЦИЯ
            q_infil = green_ampt_infil(M, depths[-1], reg, F_cum)
            Q_stok = M - q_infil
            
        profiles = np.array(profiles)
        dfd["Z_0C"] = depths
        dfd["M_rate"] = melt_rates
        dfd["q_infil"] = [green_ampt_infil(m, d, reg, F_cum) for m, d in zip(melt_rates, depths)]
        dfd["Q_stok"] = dfd["M_rate"] - dfd["q_infil"]
        
        all_results.append(dfd)
        
        # 1. Профили T(z,t)
        ax = axes[0, col]
        for depth in [0, 0.1, 0.3, 0.5]:
            idx = int(depth / dz)
            ax.plot(dfd["date"], profiles[:, idx], label=f"{depth}m")
        ax.axhline(0, ls="--", c="k", lw=2)
        ax.set_title(f"{reg}, {year}")
        ax.legend(fontsize=8)
        ax.set_ylabel("T,°C")

        # 2. Глубина 0°C
        ax = axes[1, col]
        ax.plot(dfd["date"], dfd["Z_0C"], 'r-', lw=2)
        ax.set_ylabel("Z₀°C, м")
        
        # 3. Таяние + инфильтрация
        ax = axes[2, col]
        ax.plot(dfd["date"], dfd["M_rate"], 'b-', label="Melting")
        ax.plot(dfd["date"], dfd["q_infil"], 'g-', label="Infiltration")
        ax.plot(dfd["date"], dfd["Q_stok"], 'r-', label="Runoff", lw=2)
        ax.legend()
        ax.set_ylabel("mm/day")
        
        # 4. Heatmap T(z,t)
        ax = axes[3, col]
        extent = [mdates.date2num(dfd["date"].iloc[0]), mdates.date2num(dfd["date"].iloc[-1]), z[-1], z[0]]
        im = ax.imshow(profiles.T, cmap="RdBu_r", extent=extent, aspect="auto")
        ax.xaxis_date()
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax.contour(profiles.T, levels=[0], colors="k", extent=extent)
        ax.set_ylabel('Depth, m')
        ax.set_xlabel('Date')
        plt.colorbar(im, ax=ax)


    
    plt.tight_layout()
    plt.savefig(f"full_analysis_{reg}_2021vs2024.png", dpi=300, bbox_inches='tight')
    plt.close()

results_df = pd.concat(all_results)
results_df["year"] = results_df["date"].dt.year

print("\nРЕЗУЛЬТАТ:")
print(
    results_df
    .groupby(["region", "year"])
    .agg({
        "M_rate": ["sum", "max"],
        "Z_0C": "max",
        "Q_stok": "sum"
    })
    .round(1)
)


print("\n2024 vs 2021: ФИЗИКА ПАВОДОК")
comparison = (
    results_df
    .groupby(["region", "year"])
    .agg({
        "Q_stok": "sum",
        "Z_0C": "max"
    })
    .unstack()
)

print("\n2024 vs 2021: ФИЗИКА ПАВОДОК")
print(comparison.round(1))

print(comparison.round(1))
print("\nHeat → Darcy → Saint-Venant готово! Запускай Saint-Venant с Q_stok(t)")

station_log = (
    df.groupby("region")["station_id"]
    .nunique()
    .reset_index(name="n_stations")
)

print(station_log)