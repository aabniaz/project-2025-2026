# https://flymeteo.org/synop/station_index.php -> i took coordinates from this website

import pandas as pd
import folium
import webbrowser

df = pd.read_csv("stations_flood_regions.csv", encoding="utf-8")
center_lat = 47.5
center_lon = 67.0
m = folium.Map(location=[center_lat, center_lon], zoom_start=5)

colors = {
    "KZ-ATY": "blue",
    "KZ-AKT": "green",
    "KZ-KUS": "purple",
    "KZ-SEV": "orange",
    "KZ-ZAP": "pink"
}

for _, row in df.iterrows():
    popup_text = f"""
    <b>Станция:</b> {row['stn']}<br>
    <b>Регион:</b> {row['region']}<br>
    <b>Широта:</b> {row['latitude']}<br>
    <b>Долгота:</b> {row['longitude']}
    """

    folium.CircleMarker(
        location=[row["latitude"], row["longitude"]],
        radius=6,
        color=colors.get(row["region"], "gray"),
        fill=True,
        fill_color=colors.get(row["region"], "gray"),
        fill_opacity=0.85,
        tooltip=row["stn"],
        popup=popup_text
    ).add_to(m)

legend_html = """
<div style="
    position: fixed; 
    bottom: 40px; left: 40px; 
    width: 220px; 
    background-color: white; 
    border:2px solid grey; 
    z-index:9999; 
    font-size:14px;
    padding: 10px;
">
<b>Регионы паводков 2024 КЗ</b><br>
<div style="margin-top:5px">
    <i style="background: blue; width: 12px; height: 12px; float: left; margin-right: 6px; opacity: 0.9"></i>KZ-ATY<br>
    <i style="background: green; width: 12px; height: 12px; float: left; margin-right: 6px; opacity: 0.9"></i>KZ-AKT<br>
    <i style="background: purple; width: 12px; height: 12px; float: left; margin-right: 6px; opacity: 0.9"></i>KZ-KUS<br>
    <i style="background: orange; width: 12px; height: 12px; float: left; margin-right: 6px; opacity: 0.9"></i>KZ-SEV<br>
    <i style="background: pink; width: 12px; height: 12px; float: left; margin-right: 6px; opacity: 0.9"></i>KZ-ZAP<br>
</div>
</div>
"""

m.get_root().html.add_child(folium.Element(legend_html))
m.save("kaz_flood_2024.html")
webbrowser.open("kaz_flood_2024.html")