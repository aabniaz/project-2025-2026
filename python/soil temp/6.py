import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter

file_path = "почва.xlsx"

df = pd.read_excel(file_path, header=0)

df = df.rename(columns={
    'Регион': 'region',
    'Станция_айди': 'station_id',
    'Станция': 'station_name',
    'Дата': 'date',
    'Сред': 't_surface_mean',
    'Макс': 't_surface_max',
    'Мин': 't_surface_min'
})

df = df.dropna(how='all')

df['date'] = pd.to_datetime(df['date'], format='%d.%m.%Y', errors='coerce')
df = df.dropna(subset=['date'])

df['year'] = df['date'].dt.year
df['month'] = df['date'].dt.month
df['day'] = df['date'].dt.day

df['t_surface_mean'] = pd.to_numeric(df['t_surface_mean'], errors='coerce')
df['t_surface_max'] = pd.to_numeric(df['t_surface_max'], errors='coerce')
df['t_surface_min'] = pd.to_numeric(df['t_surface_min'], errors='coerce')

df = df[df['month'].isin([2, 3, 4])]

regions = df['region'].unique()
n = len(regions)

# КЛАССИФИКАЦИЯ СОСТОЯНИЯ СНЕГА
def classify_snow(temp):
    if temp < 0:
        return "Снег (мороз)"
    if 0 <= temp <= 1.5:
        return "Мокрый снег"
    if temp > 1.5:
        return "Снег растаял"
    return "Неопределено"

df['snow_state'] = df['t_surface_mean'].apply(classify_snow)

state_colors = {
    "Снег (мороз)": "blue",
    "Мокрый снег": "purple",
    "Снег растаял": "green",
    "Неопределено": "gray"
}

# АНОМАЛИЯ 2024 – 2021 (по дню-месяцу)
df['dm'] = df['date'].dt.strftime("%d-%m")
mean_ts = df.groupby(['dm','region','year'])['t_surface_mean'].mean().reset_index()

tab21 = mean_ts[mean_ts['year']==2021].pivot(index='dm', columns='region', values='t_surface_mean')
tab24 = mean_ts[mean_ts['year']==2024].pivot(index='dm', columns='region', values='t_surface_mean')

common_dm = tab21.index.intersection(tab24.index)

if len(common_dm) > 0:
    anomaly = (tab24.loc[common_dm] - tab21.loc[common_dm]).sort_index(
        key=lambda x: pd.to_datetime(x, format="%d-%m")
    )
else:
    anomaly = None


# ТЕМПЕРАТУРА ПОВЕРХНОСТИ 2021 vs 2024
fig, axes = plt.subplots(n, 1, figsize=(15, 4*n), sharex=True)

for i, reg in enumerate(regions):
    ax = axes[i]

    sub21 = df[(df['region']==reg) & (df['year']==2021)].groupby('date')['t_surface_mean'].mean()
    sub24 = df[(df['region']==reg) & (df['year']==2024)].groupby('date')['t_surface_mean'].mean()

    ax.plot(sub21.index, sub21.values, label="2021", color="blue")
    ax.plot(sub24.index, sub24.values, label="2024", color="red")
    ax.axhline(0, linestyle='--', color='black')

    ax.set_title(f"{reg}: Температура поверхности 2021 vs 2024")
    ax.grid(True)
    ax.legend()

    ax.xaxis.set_major_formatter(DateFormatter("%d.%m"))

plt.tight_layout()
plt.show()


# АНОМАЛИЯ (2024 – 2021) по регионам
if anomaly is not None:
    fig, axes = plt.subplots(n, 1, figsize=(15, 4*n), sharex=True)

    for i, reg in enumerate(regions):
        ax = axes[i]

        if reg in anomaly.columns:
            ax.plot(anomaly.index, anomaly[reg], label=f"Аномалия {reg}")
            ax.axhline(0, linestyle='--', color='black')

            ax.set_title(f"{reg}: Аномалия поверхности почвы (2024 – 2021)")
            ax.grid(True)
            ax.legend()

    plt.tight_layout()
    plt.show()


# СОСТОЯНИЕ СНЕГА 2024 (scatter)
fig, axes = plt.subplots(n, 1, figsize=(15, 4*n), sharex=True)

for i, reg in enumerate(regions):
    ax = axes[i]
    sub = df[(df['region']==reg) & (df['year']==2024)].copy()

    if sub.empty:
        continue

    sub['color'] = sub['snow_state'].map(state_colors).fillna('gray')

    ax.scatter(sub['date'], sub['t_surface_mean'], c=sub['color'], s=20)
    ax.axhline(0, linestyle='--', color='black')

    ax.set_title(f"{reg}: Состояние снега (2024)")
    ax.set_ylabel("Температура поверхности, °C")
    ax.grid(True)

    ax.xaxis.set_major_formatter(DateFormatter("%d.%m"))

plt.tight_layout()
plt.show()
