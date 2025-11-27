# 2024 vs 2021 air temp

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.dates import DateFormatter

file_path = "данныепроекта.xlsx"

df = pd.read_excel(file_path, header=1)
print("\nКолонки, прочитанные из файла:")
print(df.columns.tolist())

df = df.rename(columns={
    df.columns[0]: 'region',
    df.columns[1]: 'station_id',
    df.columns[2]: 'station_name',
    df.columns[3]: 'date',
    df.columns[4]: 't_mean',
    df.columns[5]: 't_max',
    df.columns[6]: 't_min'
})

df = df.dropna(how='all')

df['date'] = pd.to_datetime(df['date'], format='%d.%m.%Y', errors='coerce')
df = df.dropna(subset=['date'])

for col in ['t_mean', 't_max', 't_min']:
    df[col] = pd.to_numeric(df[col], errors='coerce')

df['year'] = df['date'].dt.year
df['month'] = df['date'].dt.month

df = df[df['month'].isin([2, 3, 4])]

# первая дата таяния
def find_first_thaw(station_df):
    pos = station_df[station_df['t_mean'] > 0]
    if len(pos) == 0:
        return None
    return pos['date'].iloc[0]

results = {}

for year in sorted(df['year'].unique()):
    year_df = df[df['year'] == year].copy()

    # dT/dt
    year_df = year_df.sort_values(['station_id', 'date'])
    year_df['dT_dt'] = year_df.groupby('station_id')['t_mean'].diff()

    # первая дата таяния
    first_thaw = (year_df.groupby(['region', 'station_id'])
                           .apply(find_first_thaw)
                           .reset_index())
    first_thaw.columns = ['region', 'station_id', 'first_thaw_date']

    # ТОП скачков температуры
    top_jumps = (year_df.groupby('station_id')['dT_dt']
                 .max()
                 .sort_values(ascending=False)
                 .head(10))

    # средняя температура по месяцам
    monthly_mean = (year_df.groupby(['region', 'month'])['t_mean']
                    .mean()
                    .reset_index())

    results[year] = {
        'data': year_df,
        'first_thaw': first_thaw,
        'top_jumps': top_jumps,
        'monthly_mean': monthly_mean
    }

for year in results:
    print(f"\n=== ГОД {year} ===")

    print("\nПервые даты таяния:")
    print(results[year]['first_thaw'])

    print("\nТОП-10 резких скачков температуры:")
    print(results[year]['top_jumps'])

    print("\nСредняя температура по месяцам:")
    print(results[year]['monthly_mean'])

unique_years = sorted(df['year'].unique())
num_years = len(unique_years)

plt.figure(figsize=(14, 5 * num_years))

for i, year in enumerate(unique_years, start=1):
    year_df = results[year]['data']
    reg_daily = year_df.groupby(['region', 'date'])['t_mean'].mean().reset_index()

    plt.subplot(num_years, 1, i)

    for reg in reg_daily['region'].unique():
        sub = reg_daily[reg_daily['region'] == reg]
        plt.plot(sub['date'], sub['t_mean'], label=reg)

    plt.axhline(0, color='black', linestyle='--')
    plt.title(f"Температура воздуха по регионам - {year}", fontsize=16, fontweight='bold')
    plt.xlabel("Дата")
    plt.ylabel("Температура, °C")
    plt.grid(True)
    plt.legend()

    date_format = DateFormatter("%d.%m.%Y")
    plt.gca().xaxis.set_major_formatter(date_format)
    plt.xticks(rotation=45)

plt.tight_layout()
plt.savefig('air temp 2024 vs 2021')
plt.show()












# #2024 vs 2021 air temp
# #   АНАЛИЗ ТЕМПЕРАТУРЫ ВОЗДУХА: 2024 (ПАВОДКОВЫЙ) vs 2021 (СПОКОЙНЫЙ)

# import pandas as pd
# import numpy as np
# import matplotlib.pyplot as plt
# import matplotlib.dates as mdates
# from matplotlib.dates import DateFormatter


# file_path = "данныепроекта.xlsx"   # твой файл
# df = pd.read_excel(file_path, header=0)

# print("Колонки, прочитанные из файла:")
# print(df.columns.tolist())

# df = df.rename(columns={
#     'Регион': 'region',
#     'Станция_айди': 'station_id',
#     'Станция': 'station_name',
#     'Дата': 'date',
#     'Сред': 't_mean',
#     'Макс': 't_max',
#     'Мин': 't_min'
# })

# df = df.dropna(how='all')

# df['date'] = pd.to_datetime(df['date'], format='%d.%m.%Y', errors='coerce')

# df = df.dropna(subset=['date'])

# df['t_mean'] = pd.to_numeric(df['t_mean'], errors='coerce')
# df['t_max'] = pd.to_numeric(df['t_max'], errors='coerce')
# df['t_min'] = pd.to_numeric(df['t_min'], errors='coerce')

# df['year'] = df['date'].dt.year
# df['month'] = df['date'].dt.month
# df['day'] = df['date'].dt.day

# df = df[df['month'].isin([2, 3, 4])]

# # НАЙТИ ДАТУ ПЕРВОГО ТАЯНИЯ

# def find_first_thaw(station_df):
#     pos = station_df[station_df['t_mean'] > 0]
#     if len(pos) == 0:
#         return None
#     return pos['date'].iloc[0]

# # РАСЧЁТ ДАТ ПЕРВОГО ТАЯНИЯ ПО СТАНЦИЯМ

# first_thaw = df.groupby(['region', 'station_id']).apply(find_first_thaw).reset_index()
# first_thaw.columns = ['region', 'station_id', 'first_thaw_date']

# print("\nПервые даты таяния по станциям:")
# print(first_thaw)

# # ВЫЧИСЛЯЕМ СКОРОСТЬ ПРОГРЕВА (dT/dt)

# df = df.sort_values(['station_id', 'date'])
# df['dT_dt'] = df.groupby('station_id')['t_mean'].diff()


# df_2024 = df[df['year'] == 2024]
# df_2021 = df[df['year'] == 2021]

# regions = df['region'].unique()

# for reg in regions:
#     fig, axes = plt.subplots(2, 1, figsize=(14, 8), sharex=True)

#     # ----- 2024 -----
#     sub24 = df_2024[df_2024['region'] == reg]
#     daily24 = sub24.groupby('date')['t_mean'].mean()

#     axes[0].plot(daily24.index, daily24.values, color='red', linewidth=2)
#     axes[0].axhline(0, linestyle='--', color='black')
#     axes[0].set_title(f"{reg} — 2024 (ПАВОДКОВЫЙ ГОД)")
#     axes[0].set_ylabel("Температура, °C")
#     axes[0].grid(True)

#     # ----- 2021 -----
#     sub21 = df_2021[df_2021['region'] == reg]
#     daily21 = sub21.groupby('date')['t_mean'].mean()

#     axes[1].plot(daily21.index, daily21.values, color='blue', linewidth=2)
#     axes[1].axhline(0, linestyle='--', color='black')
#     axes[1].set_title(f"{reg} — 2021 (СПОКОЙНЫЙ ГОД)")
#     axes[1].set_xlabel("Дата")
#     axes[1].set_ylabel("Температура, °C")
#     axes[1].grid(True)

#     date_format = DateFormatter("%d.%m.%Y")
#     axes[1].xaxis.set_major_formatter(date_format)
#     plt.xticks(rotation=45)

#     fig.tight_layout()
#     plt.show()

# # ТОП-10 РЕЗКИХ СКАЧКОВ (dT/dt)

# top10 = df.groupby('station_id')['dT_dt'].max().sort_values(ascending=False).head(10)

# print("\nТОП-10 самых резких скачков температуры (dT/dt):")
# print(top10)

# # СРЕДНЯЯ ТЕМПЕРАТУРА ПО МЕСЯЦАМ

# monthly = df.groupby(['region', 'month'])['t_mean'].mean().reset_index()

# print("\nСредняя температура по месяцам (2021 + 2024):")
# print(monthly)
