# 2024 vs 2021 air temp

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.dates import DateFormatter


file_path = "почва.xlsx"
# sheet_name = "темп почвы"

# xls = pd.ExcelFile(file_path)
# print("Листы в файле:", xls.sheet_names)

# try:
#     df = pd.read_excel(file_path, sheet_name=sheet_name)
#     print(f"Второй лист '{sheet_name}', первые 3 строки:")
#     print(df.head(3))
# except ValueError as e:
#     print(f"Ошибка: лист '{sheet_name}' не найден. \n{e}")



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

#первая дата таяния
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
    # plt.title(f"Температура воздуха по регионам - {year}", fontsize=16, fontweight='bold')
    plt.xlabel("Дата")
    plt.ylabel("Температура, °C")
    plt.grid(True)
    plt.legend()

    date_format = DateFormatter("%d.%m.%Y")
    plt.gca().xaxis.set_major_formatter(date_format)
    plt.xticks(rotation=45)

plt.tight_layout()
# plt.savefig('air temp 2024 vs 2021')
plt.show()
