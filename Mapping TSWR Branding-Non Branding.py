# app.py
import streamlit as st
import pandas as pd

st.title("Peta Titik Koordinat di Mapbox via Streamlit")

st.markdown("""
Masukkan daftar koordinat (longitude, latitude) di bawah ini.  
Format: satu baris per titik, dipisah koma atau spasi.  
Contoh:  
112.7368, -7.2575  
112.7680, -7.2650  
""")

# Input teks multi-line
raw_input = st.text_area("Masukkan koordinat (lng, lat)", height=150, value="""112.7368, -7.2575
112.7680, -7.2650
112.7200, -7.2900
112.7500, -7.2500""")

# Parsing input menjadi list of [lng, lat]
points = []
for line in raw_input.strip().split("\n"):
    line = line.strip()
    if not line:
        continue
    try:
        parts = [float(x.strip()) for x in line.replace(";", ",").split(",") if x.strip()]
        if len(parts) >= 2:
            lng, lat = parts[0], parts[1]
            points.append({"lon": lng, "lat": lat})
    except:
        st.warning(f"Baris salah format → dilewati: {line}")

if points:
    df = pd.DataFrame(points)

    st.subheader("Peta Titik Koordinat")
    st.map(
        df,
        latitude="lat",
        longitude="lon",
        zoom=10,                # sesuaikan zoom awal
        use_container_width=True,
        height=600
    )

    st.subheader("Data Koordinat")
    st.dataframe(df)

    # Opsional: tampilkan juga dalam format GeoJSON sederhana
    geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [row.lon, row.lat]},
                "properties": {"id": i+1}
            }
            for i, row in df.iterrows()
        ]
    }
    st.json(geojson)
else:
    st.info("Belum ada koordinat yang valid. Masukkan di atas.")