import streamlit as st
import pandas as pd
import json
import pydeck as pdk
from shapely.geometry import shape
import os

st.set_page_config(page_title="Peta 2 Kelompok Titik + 2 Batas Wilayah", layout="wide")

st.title("Peta Perbandingan 2 Kelompok Titik Koordinat")
st.markdown("""
Bandingkan dua kelompok titik (misal: survei lama vs baru, atau dua jenis data)  
dengan batas wilayah dari dua file GeoJSON berbeda.
""")

# ────────────────────────────────────────────────
# Konfigurasi path file (sesuaikan dengan struktur folder Anda)
# ────────────────────────────────────────────────
BASE_DIR = "Map"

# File batas wilayah 1 (contoh: Kabupaten Gresik)
GEOJSON_A = os.path.join(BASE_DIR, "Kabupaten_Gresik.geojson")
COLOR_A_FILL = [59, 130, 246, 60]    # biru muda semi-transparan
COLOR_A_LINE = [30, 80, 200, 220]
COLOR_A_POINT = [59, 130, 246, 240]  # biru cerah untuk titik

# File batas wilayah 2 (contoh: Kabupaten Lamongan atau lain)
GEOJSON_B = os.path.join(BASE_DIR, "Kabupaten_Lamongan.geojson")
COLOR_B_FILL = [239, 68, 68, 60]     # merah muda semi-transparan
COLOR_B_LINE = [180, 40, 40, 220]
COLOR_B_POINT = [239, 68, 68, 240]   # merah cerah untuk titik

# ────────────────────────────────────────────────
# Fungsi bantu: hitung centroid
# ────────────────────────────────────────────────
def extract_centroids(geojson_data, group_name, color):
    points = []
    for idx, feature in enumerate(geojson_data.get("features", [])):
        geom = feature.get("geometry")
        props = feature.get("properties", {})
        
        if geom and geom.get("type") in ["Polygon", "MultiPolygon"]:
            try:
                geom_shape = shape(geom)
                centroid = geom_shape.centroid
                points.append({
                    "lon": centroid.x,
                    "lat": centroid.y,
                    "nama": props.get("nm_kecamatan", props.get("KECAMATAN", f"{group_name} {idx+1}")),
                    "group": group_name,
                    "id": f"{group_name}_{idx+1}"
                })
            except:
                continue
        elif geom and geom.get("type") == "Point":
            coords = geom["coordinates"]
            if len(coords) >= 2:
                points.append({
                    "lon": coords[0],
                    "lat": coords[1],
                    "nama": props.get("nm_kecamatan", props.get("name", f"{group_name} {idx+1}")),
                    "group": group_name,
                    "id": f"{group_name}_{idx+1}"
                })
    return points

# ────────────────────────────────────────────────
# Load & proses GeoJSON A
# ────────────────────────────────────────────────
data_a = None
points_a = []
if os.path.exists(GEOJSON_A):
    try:
        with open(GEOJSON_A, 'r', encoding='utf-8') as f:
            data_a = json.load(f)
        points_a = extract_centroids(data_a, "Kelompok A", COLOR_A_POINT)
        st.success(f"Berhasil memuat {GEOJSON_A} → {len(points_a)} titik centroid")
    except Exception as e:
        st.error(f"Gagal memproses {GEOJSON_A}: {e}")
else:
    st.warning(f"File tidak ditemukan: {GEOJSON_A}")

# ────────────────────────────────────────────────
# Load & proses GeoJSON B
# ────────────────────────────────────────────────
data_b = None
points_b = []
if os.path.exists(GEOJSON_B):
    try:
        with open(GEOJSON_B, 'r', encoding='utf-8') as f:
            data_b = json.load(f)
        points_b = extract_centroids(data_b, "Kelompok B", COLOR_B_POINT)
        st.success(f"Berhasil memuat {GEOJSON_B} → {len(points_b)} titik centroid")
    except Exception as e:
        st.error(f"Gagal memproses {GEOJSON_B}: {e}")
else:
    st.warning(f"File tidak ditemukan: {GEOJSON_B}")

# Gabungkan semua titik
all_points = points_a + points_b
if not all_points:
    st.error("Tidak ada titik yang berhasil diekstrak dari kedua file GeoJSON.")
    st.stop()

df = pd.DataFrame(all_points)

# ────────────────────────────────────────────────
# Layer Peta
# ────────────────────────────────────────────────

# Batas wilayah A
boundary_a = None
if data_a:
    boundary_a = pdk.Layer(
        "GeoJsonLayer",
        data=data_a,
        opacity=0.18,
        stroked=True,
        filled=True,
        get_fill_color=COLOR_A_FILL,
        get_line_color=COLOR_A_LINE,
        line_width_min_pixels=1.8,
        pickable=True
    )

# Batas wilayah B
boundary_b = None
if data_b:
    boundary_b = pdk.Layer(
        "GeoJsonLayer",
        data=data_b,
        opacity=0.18,
        stroked=True,
        filled=True,
        get_fill_color=COLOR_B_FILL,
        get_line_color=COLOR_B_LINE,
        line_width_min_pixels=1.8,
        pickable=True
    )

# Titik gabungan (warna berdasarkan group)
points_layer = pdk.Layer(
    "ScatterplotLayer",
    data=df,
    get_position=["lon", "lat"],
    get_radius=900,
    get_fill_color=[
        pdk.types.pdk.functions.color_to_rgb(COLOR_A_POINT) if x == "Kelompok A" else pdk.types.pdk.functions.color_to_rgb(COLOR_B_POINT)
        for x in df["group"]
    ],
    get_line_color=[255, 255, 255, 180],
    line_width_min_pixels=2,
    radius_min_pixels=7,
    radius_max_pixels=22,
    pickable=True
)

# Label teks (nama kecamatan / feature)
text_layer = pdk.Layer(
    'TextLayer',
    data=df,
    get_position=['lon', 'lat'],
    get_text='nama',
    get_size=13,
    get_color=[0, 0, 0, 220],
    get_angle=0,
    get_text_anchor='Middle',
    get_alignment_baseline='Bottom',
    size_scale=0.9,
    background=True,
    background_padding=[2, 1],
    background_color=[255, 255, 255, 180]
)

# Hitung pusat view
if not df.empty:
    center_lat = df['lat'].mean()
    center_lon = df['lon'].mean()
    zoom = 10.2
else:
    center_lat, center_lon, zoom = -7.15, 112.65, 9.5

view_state = pdk.ViewState(
    latitude=center_lat,
    longitude=center_lon,
    zoom=zoom,
    pitch=0
)

# Tooltip
tooltip = {
    "html": """
    <b>{nama}</b><br>
    <b>Kelompok:</b> {group}<br>
    Lon: {lon:.6f} | Lat: {lat:.6f}
    """,
    "style": {
        "backgroundColor": "rgba(255,255,255,0.94)",
        "color": "#000",
        "padding": "8px 12px",
        "borderRadius": "5px",
        "boxShadow": "2px 4px 10px rgba(0,0,0,0.25)"
    }
}

# Gabungkan layer (batas A & B + titik + label)
layers = []
if boundary_a: layers.append(boundary_a)
if boundary_b: layers.append(boundary_b)
layers.extend([points_layer, text_layer])

deck = pdk.Deck(
    layers=layers,
    initial_view_state=view_state,
    tooltip=tooltip,
    map_style='road'
)

st.subheader("Perbandingan 2 Kelompok Titik & Batas Wilayah")
st.pydeck_chart(deck, use_container_width=True, height=750)

# Ringkasan data
col1, col2 = st.columns(2)
with col1:
    st.subheader("Kelompok A")
    st.dataframe(df[df["group"] == "Kelompok A"][["nama", "lon", "lat"]])
with col2:
    st.subheader("Kelompok B")
    st.dataframe(df[df["group"] == "Kelompok B"][["nama", "lon", "lat"]])

st.caption("Catatan: Warna biru = Kelompok A, Warna merah = Kelompok B")
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
