import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
from geopy.distance import geodesic
import streamlit.components.v1 as components

st.set_page_config(page_title="Washoe Safe Shot", page_icon="Target", layout="centered")

st.title("Target **Washoe Safe Shot**")
st.markdown("**Official-Style Safety Tool** | **Built w/ Grok xAI** | **USMC Vet Project**")
st.markdown("**[Washoe County Code 50](https://www.washoecounty.gov/clerks/cco/code/Chapter050.pdf)**")

# Sidebar
with st.sidebar:
    st.header("Rules **Rules**")
    st.markdown("""
    - **Rifles/Pistols**: >**5,000 ft** from dwellings
    - **Shotguns/BB/Air**: >**1,000 ft** from dwellings  
    - **NO**: Congested areas, roads, parks
    - **Report**: 775-785-9276
    """)
    st.markdown("[Sheriff's Page](https://www.washoesheriff.com)")

# === GET GPS FROM URL ===
query_params = st.experimental_get_query_params()
lat = float(query_params.get("lat", [39.72009])[0])
lon = float(query_params.get("lon", [-119.92786])[0])

st.success(f"Location: {lat:.5f} degrees, {lon:.5f} degrees")

# === GPS BUTTON — WORKS IN IFRAME BY USING window.parent ===
components.html("""
<div style="text-align:center; margin:20px;">
    <button onclick="getGPS()" style="
        width:90%; max-width:400px;
        background:#007bff; color:white; 
        padding:18px; border:none; border-radius:12px; 
        font-size:18px; font-weight:bold; cursor:pointer;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    ">
        Get My GPS Location
    </button>
    <p id="status" style="margin-top:15px; color:#555; font-weight:500;"></p>
</div>

<script>
function getGPS() {
    const btn = document.querySelector('button');
    const status = document.getElementById('status');
    btn.innerHTML = "Getting Location...";
    btn.disabled = true;
    status.innerHTML = "";

    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            (pos) => {
                const lat = pos.coords.latitude.toFixed(5);
                const lon = pos.coords.longitude.toFixed(5);
                status.innerHTML = "GPS Locked! Reloading...";
                const url = new URL(window.parent.location);
                url.searchParams.set('lat', lat);
                url.searchParams.set('lon', lon);
                window.parent.location.href = url.toString();
            },
            (err) => {
                btn.innerHTML = "Try Again";
                btn.disabled = false;
                let msg = "Failed: ";
                if (err.code === 1) msg += "Permission denied";
                else if (err.code === 2) msg += "Location unavailable";
                else if (err.code === 3) msg += "Timeout";
                else msg += err.message;
                status.innerHTML = msg;
            },
            {enableHighAccuracy: true, timeout: 15000}
        );
    } else {
        status.innerHTML = "GPS not supported";
        btn.disabled = false;
    }
}
</script>
""", height=150)

# === MAP WITH GPS PIN ===
st.markdown("### Your Location on Map")
m = folium.Map(location=[lat, lon], zoom_start=16)
folium.Marker(
    [lat, lon],
    popup=f"<b>Your Location</b><br>Lat: {lat:.5f}<br>Lon: {lon:.5f}",
    tooltip="Your Location",
    icon=folium.Icon(color='red', icon='info-sign')
).add_to(m)
folium.Circle([lat, lon], radius=304.8, color='orange', fill=True, fillOpacity=0.1, popup='1000 ft').add_to(m)
folium.Circle([lat, lon], radius=1524, color='red', fill=True, fillOpacity=0.05, popup='5000 ft').add_to(m)
st_folium(m, width=700, height=500)

# === LEGALITY CHECK ===
@st.cache_data(ttl=300)
def get_nearest_building(lat, lon):
    overpass_url = "https://overpass-api.de/api/interpreter"
    query = f'''
    [out:json][timeout:25];
    (
      way["building"](around:20000,{lat},{lon});
      node["building"](around:20000,{lat},{lon});
    );
    out center;
    '''
    try:
        r = requests.get(overpass_url, params={'data': query}, timeout=30)
        r.raise_for_status()
        data = r.json()
        min_dist = float('inf')
        for el in data.get('elements', []):
            if 'center' in el:
                b_lat = el['center']['lat']
                b_lon = el['center']['lon']
            elif 'lat' in el:
                b_lat = el['lat']
                b_lon = el['lon']
            else:
                continue
            dist = geodesic((lat, lon), (b_lat, b_lon)).meters
            min_dist = min(min_dist, dist)
        return round(min_dist * 3.28084) if min_dist != float('inf') else None
    except Exception as e:
        st.error(f"Error: {e}")
        return None

st.markdown("### Check Shooting Legality")
if st.button("**CHECK LEGALITY NOW**", type="primary", use_container_width=True):
    with st.spinner("Scanning..."):
        dist_ft = get_nearest_building(lat, lon)
    st.markdown(f"### **Results for: {lat:.5f}°, {lon:.5f}°**")
    if dist_ft is None:
        st.success("**REMOTE AREA** — Likely Legal")
    else:
        st.metric("**Nearest Dwelling**", f"{dist_ft:,} ft")
        if dist_ft > 5000:
            st.success("**LEGAL: All firearms**")
        elif dist_ft > 1000:
            st.warning("**LEGAL: Shotguns/BB/Air Rifles ONLY**")
        else:
            st.error("**ILLEGAL — TOO CLOSE!**")
    st.warning("**Disclaimer:** Informational only. Verify local laws.")
