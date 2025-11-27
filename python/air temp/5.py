# 2024 vs 2021 air temp 4 figures    
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.dates import DateFormatter

file_path = "данныепроекта.xlsx"

df = pd.read_excel(file_path, header=0)

df = df.rename(columns={
    'Регион': 'region',
    'Станция_айди': 'station_id',
    'Станция': 'station_name',
    'Дата': 'date',
    'Сред': 't_mean',
    'Макс': 't_max',
    'Мин': 't_min'
})

df = df.dropna(how='all')

df['date'] = pd.to_datetime(df['date'], format='%d.%m.%Y', errors='coerce')
df = df.dropna(subset=['date'])

df['t_mean'] = pd.to_numeric(df['t_mean'], errors='coerce')
df['t_max'] = pd.to_numeric(df['t_max'], errors='coerce')
df['t_min'] = pd.to_numeric(df['t_min'], errors='coerce')

df['year'] = df['date'].dt.year
df['month'] = df['date'].dt.month

df = df[df['month'].isin([2, 3, 4])]

# 1. ГРАФИК РАЗНИЦЫ (2024 - 2021)
df24 = df[df['year'] == 2024]
df21 = df[df['year'] == 2021]

reg24 = df24.groupby(['region', 'date'])['t_mean'].mean().reset_index()
reg21 = df21.groupby(['region', 'date'])['t_mean'].mean().reset_index()

min_len = min(len(reg24), len(reg21))
reg24 = reg24.iloc[:min_len]
reg21 = reg21.iloc[:min_len]

reg_diff = reg24.copy()
reg_diff['t_diff'] = reg24['t_mean'].values - reg21['t_mean'].values

plt.figure(figsize=(14, 10))
for region in reg_diff['region'].unique():
    sub = reg_diff[reg_diff['region'] == region]
    plt.plot(sub['date'], sub['t_diff'], label=region)

plt.axhline(0, color='black', linestyle='--')
plt.title("Разница средней температуры (2024 – 2021)", fontsize=16, fontweight='bold')
plt.xlabel("Дата")
plt.ylabel("ΔT, °C")
plt.legend()
plt.grid(True)
plt.xticks(rotation=45)
plt.savefig('raznica2024vs2021')
plt.show()

# 2. СКОРОСТЬ ПРОГРЕВА (dT/dt)
df24s = df24.sort_values(['station_id', 'date'])
df21s = df21.sort_values(['station_id', 'date'])

df24s['dT_dt'] = df24s.groupby('station_id')['t_mean'].diff()
df21s['dT_dt'] = df21s.groupby('station_id')['t_mean'].diff()

dT24 = df24s.groupby('date')['dT_dt'].mean().reset_index()
dT21 = df21s.groupby('date')['dT_dt'].mean().reset_index()

plt.figure(figsize=(14, 10))
plt.plot(dT24['date'], dT24['dT_dt'], label="2024", color="red")
plt.plot(dT21['date'], dT21['dT_dt'], label="2021", color="blue")
plt.axhline(0, color='black', linestyle='--')
plt.title("Скорость прогрева воздуха (dT/dt): 2024 vs 2021", fontsize=16, fontweight='bold')
plt.xlabel("Дата")
plt.ylabel("dT/dt (°C/день)")
plt.legend()
plt.grid(True)
plt.xticks(rotation=45)
plt.savefig('scorostprogreva2024vs2021')
plt.show()

# 3. График начала таяния (точки)
def thaw_day(st_df):
    pos = st_df[st_df['t_mean'] > 0]
    if len(pos) == 0:
        return None
    return pos['date'].iloc[0]

thaw = df.groupby(['year', 'region', 'station_id']).apply(thaw_day).reset_index()
thaw.columns = ['year', 'region', 'station_id', 'first_thaw']

plt.figure(figsize=(14, 10))
for yr in thaw['year'].unique():
    sub = thaw[thaw['year'] == yr]
    plt.scatter(sub['region'], sub['first_thaw'], label=str(yr))

plt.title("Первая дата перехода температуры > 0°C по станциям", fontsize=16, fontweight='bold')
plt.xlabel("Регион")
plt.ylabel("Дата")
plt.legend()
plt.grid(True)
plt.xticks(rotation=45)
plt.savefig('nachalotayania2024vs2021')
plt.show()

# 4. HEATMAP сравнения месяцев
monthly = df.groupby(['year', 'region', 'month'])['t_mean'].mean().reset_index()
heat = monthly.pivot_table(values='t_mean', index='region', columns=['year', 'month'])

plt.figure(figsize=(12, 10))
plt.imshow(heat, cmap='coolwarm', aspect='auto')
plt.title("Heatmap: средняя температура по месяцам, регионам и годам", fontsize=16, fontweight='bold')
plt.colorbar(label='Температура, °C')
plt.xticks(range(len(heat.columns)), heat.columns, rotation=90)
plt.yticks(range(len(heat.index)), heat.index)
plt.savefig('heatmap2024vs2021')
plt.show()
