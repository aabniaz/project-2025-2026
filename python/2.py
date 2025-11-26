# code for air temp in 2024
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.dates import DateFormatter

file_path = "данныепроекта.xlsx"   
df = pd.read_excel(file_path, header=0)

print("Колонки, которые прочитал файл:")
print(df.columns.tolist())

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
df['day'] = df['date'].dt.day

df = df[df['month'].isin([2, 3, 4])]

def find_first_thaw(station_df):
    pos = station_df[station_df['t_mean'] > 0]
    if len(pos) == 0:
        return None
    return pos['date'].iloc[0]

first_thaw = df.groupby(['region', 'station_id']).apply(find_first_thaw).reset_index()
first_thaw.columns = ['region', 'station_id', 'first_thaw_date']

print("\nПервые даты таяния по станциям:")
print(first_thaw)

df = df.sort_values(['station_id', 'date'])
df['dT_dt'] = df.groupby('station_id')['t_mean'].diff()

regional_daily = df.groupby(['region', 'date'])['t_mean'].mean().reset_index()

plt.figure(figsize=(12, 6))
for reg in regional_daily['region'].unique():
    subset = regional_daily[regional_daily['region'] == reg]
    plt.plot(subset['date'], subset['t_mean'], label=reg)

plt.axhline(0, color='black', linestyle='--')
plt.legend()
plt.title("Средняя температура воздуха по регионам (Февраль–Апрель 2024)")
plt.grid(True)
plt.xlabel("Дата")
plt.ylabel("Температура, °C")

date_format = DateFormatter("%d.%m.%Y")
plt.gca().xaxis.set_major_formatter(date_format)
plt.xticks(rotation=45)
plt.savefig('airtemp2024')
plt.show()

top10 = df.groupby('station_id')['dT_dt'].max().sort_values(ascending=False).head(10)

print("\nТОП-10 резких скачков температуры (dT/dt):")
print(top10)

monthly = df.groupby(['region', 'month'])['t_mean'].mean().reset_index()

print("\nСредняя температура по месяцам:")
print(monthly)

def plot_region(region_code):
    plt.figure(figsize=(12,5))
    sub = df[df['region'] == region_code]
    daily = sub.groupby('date')['t_mean'].mean()

    plt.plot(daily.index, daily.values)
    plt.axhline(0, color='black', linestyle='--')
    plt.grid(True)
    plt.title(f"Температура в регионе {region_code}")
    plt.xlabel("Дата")
    plt.ylabel("Температура, °C")

    date_format = DateFormatter("%d.%m.%Y")
    plt.gca().xaxis.set_major_formatter(date_format)
    plt.xticks(rotation=45)

    plt.show()

# plot_region("KZ_AKT")
