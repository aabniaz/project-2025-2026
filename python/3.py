#to fill region and station_id on excel
import pandas as pd

file_path = "данныепроекта.xlsx"   
df = pd.read_excel(file_path, header=0)

stations = [
    ("KZ-ATY-01", "Атырау", "KZ-ATY"),
    ("KZ-ATY-02", "Ганюшкино", "KZ-ATY"),
    ("KZ-ATY-03", "Индерборский", "KZ-ATY"),
    ("KZ-ATY-04", "Карабау", "KZ-ATY"),
    ("KZ-ATY-05", "Кульсары", "KZ-ATY"),
    ("KZ-ATY-06", "Махамбет", "KZ-ATY"),
    ("KZ-ATY-07", "Новый Уштоган", "KZ-ATY"),
    ("KZ-ATY-08", "Пешной", "KZ-ATY"),
    ("KZ-ATY-09", "Сагиз", "KZ-ATY"),
    ("KZ-ATY-10", "Тайпак", "KZ-ATY"),

    ("KZ-AKT-01", "Актобе", "KZ-AKT"),
    ("KZ-AKT-02", "Аяккум", "KZ-AKT"),
    ("KZ-AKT-03", "Ильинский", "KZ-AKT"),
    ("KZ-AKT-04", "Иргиз", "KZ-AKT"),
    ("KZ-AKT-05", "Карабутак", "KZ-AKT"),
    ("KZ-AKT-06", "Караулкельды", "KZ-AKT"),
    ("KZ-AKT-07", "Комсомольское", "KZ-AKT"),
    ("KZ-AKT-08", "Кос-Истек", "KZ-AKT"),
    ("KZ-AKT-09", "Мартук", "KZ-AKT"),
    ("KZ-AKT-10", "Мугоджарская", "KZ-AKT"),
    ("KZ-AKT-11", "Новоалексеевка", "KZ-AKT"),
    ("KZ-AKT-12", "Нура", "KZ-AKT"),
    ("KZ-AKT-13", "Родниковка", "KZ-AKT"),
    ("KZ-AKT-14", "Темир", "KZ-AKT"),
    ("KZ-AKT-15", "Уил", "KZ-AKT"),
    ("KZ-AKT-16", "Шалкар", "KZ-AKT"),
    ("KZ-AKT-17", "Эмба", "KZ-AKT"),

    ("KZ-KUS-01", "Амангельды", "KZ-KUS"),
    ("KZ-KUS-02", "Аркалык", "KZ-KUS"),
    ("KZ-KUS-03", "Аршалинский З/СВХ", "KZ-KUS"),
    ("KZ-KUS-04", "Диевская", "KZ-KUS"),
    ("KZ-KUS-05", "Екидин", "KZ-KUS"),
    ("KZ-KUS-06", "Железнодорожный СВХ.", "KZ-KUS"),
    ("KZ-KUS-07", "Житикара", "KZ-KUS"),
    ("KZ-KUS-08", "Карабалык", "KZ-KUS"),
    ("KZ-KUS-09", "Караменды", "KZ-KUS"),
    ("KZ-KUS-10", "Карасу", "KZ-KUS"),
    ("KZ-KUS-11", "Костанай", "KZ-KUS"),
    ("KZ-KUS-12", "Кушмурун", "KZ-KUS"),
    ("KZ-KUS-13", "Михайловка", "KZ-KUS"),
    ("KZ-KUS-14", "Пресногорьковка", "KZ-KUS"),
    ("KZ-KUS-15", "Рудный", "KZ-KUS"),
    ("KZ-KUS-16", "Сарыколь", "KZ-KUS"),
    ("KZ-KUS-17", "Тобол", "KZ-KUS"),
    ("KZ-KUS-18", "Торгай", "KZ-KUS"),

    ("KZ-SEV-01", "Благовещенка", "KZ-SEV"),
    ("KZ-SEV-02", "Возвышенка", "KZ-SEV"),
    ("KZ-SEV-03", "Дмитриевка", "KZ-SEV"),
    ("KZ-SEV-04", "Кишкенеколь", "KZ-SEV"),
    ("KZ-SEV-05", "Петропавловск", "KZ-SEV"),
    ("KZ-SEV-06", "Рузаевка", "KZ-SEV"),
    ("KZ-SEV-07", "Саумалколь", "KZ-SEV"),
    ("KZ-SEV-08", "Сергеевка", "KZ-SEV"),
    ("KZ-SEV-09", "Тайынша", "KZ-SEV"),
    ("KZ-SEV-10", "Тимирязево", "KZ-SEV"),
    ("KZ-SEV-11", "Чкалово", "KZ-SEV"),
    ("KZ-SEV-12", "Явленка", "KZ-SEV"),

    ("KZ-ZAP-01", "Аксай", "KZ-ZAP"),
    ("KZ-ZAP-02", "Джамбейты", "KZ-ZAP"),
    ("KZ-ZAP-03", "Джангала", "KZ-ZAP"),
    ("KZ-ZAP-04", "Джаныбек", "KZ-ZAP"),
    ("KZ-ZAP-05", "Жалпактал", "KZ-ZAP"),
    ("KZ-ZAP-06", "Каменка", "KZ-ZAP"),
    ("KZ-ZAP-07", "Каратюба", "KZ-ZAP"),
    ("KZ-ZAP-08", "Уральск", "KZ-ZAP"),
    ("KZ-ZAP-09", "Урда", "KZ-ZAP"),
    ("KZ-ZAP-10", "Чапаево", "KZ-ZAP"),
    ("KZ-ZAP-11", "Чингирлау", "KZ-ZAP"),
    ("KZ-ZAP-12", "Январцево", "KZ-ZAP")
]


station_df = pd.DataFrame(stations, columns=["stn_id", "stn_name", "region"])

df = df.merge(
    station_df,
    left_on="Станция",
    right_on="stn_name",
    how="left"
)

df["Регион"] = df["region"]
df["Станция_айди"] = df["stn_id"]

df = df.drop(columns=["stn_id", "stn_name", "region"])

with pd.ExcelWriter(file_path, engine="openpyxl", mode="w") as writer:
    df.to_excel(writer, index=False)

print("Файл успешно обновлён")
