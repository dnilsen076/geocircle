import streamlit as st
import requests
from geopy.distance import geodesic
import streamlit.components.v1 as components

st.set_page_config(page_title="Washoe Safe Shot", page_icon="🎯", layout="centered")

st.title("🎯 **Washoe Safe Shot**")
st.markdown("**Official-Style Safety Tool** | **Built w/ Grok xAI** | **USMC Vet Project**")
st.markdown("**[Washoe County Code 50](https://www.washoecounty.gov/clerks/cco/code/Chapter050.pdf)**")

# Sidebar
with st.sidebar:
    st.header("⚖️ **EXACT Rules**")
    st.markdown("""
    - **Rifles/Pistols**: >**5,000 ft** from dwellings
    - **Shotguns/BB/Air**: >**1,000 ft** from dwellings  
    - **NO**: Congested areas, roads, parks
    - **Report**: 775-785-9276
    """)
    st.markdown("[Sheriff's Page](https://www.washoesheriff.com/operations_bureau/patrol-division/congested-areafirearms-discharge-maps.php)")

# === OPEN IN NEW TAB (BYPASS IFRAME) ===
if st.button("📱 **OPEN IN FULL BROWSER (GPS Works Here)**", type="primary"):
    st.write("""
    <script>
    window.open(window.location.href, '_blank');
    </script>
    """, unsafe_allow_html=True)
    st.stop()

# === GPS FROM URL ===
query_params = st.experimental_get_query_params()
lat = float(query_params.get("lat", [39.72009])[0])
lon = float(query_params.get("lon", [-119.92786])[0])

st.success(f"📍 GPS Locked: {lat:.5f}°, {lon:.5f}°")

# === GPS BUTTON (ONLY IN FULL BROWSER) ===
components.html(f"""
<div style="text-align:center; margin:20px;">
    <button onclick="getGPS()" style="
        width:90%; max-width:400px;
        background:#007bff; color:white; 
        padding:18px; border:none; border-radius:12px; 
        font-size:18px; font-weight:bold; cursor:pointer;
    ">
        📍 Get My GPS Location
    </button>
    <p id="status" style="margin-top:10px; color:#555;"></p>
</div>

<script>
function getGPS() {
    const btn = document.querySelector('button');
    const status = document.getElementById('status');
    btn.innerHTML = "Getting Location...";
    status.innerHTML = "";

    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            (pos) => {
                const lat = pos.coords.latitude.toFixed(5);
                const lon = pos.coords.longitude.toFixed(5);
                const url = new URL(window.location);
                url.searchParams.set('lat', lat);
                url.searchParams.set('lon', lon);
                window.location = url;
            },
            (err) => {
                btn.innerHTML = "Try Again";
                status.innerHTML = "Failed: " + err.message;
            },
            {enableHighAccuracy: true, timeout: 15000}
        );
    } else {
        status.innerHTML = "GPS not supported";
    }
}
</script>
""", height=140)

@st.cache_data(ttl=300)
def get_nearest_building(lat, lon):
    overpass_url = "http://overpass-api.de/api/interpreter"
    query = f'[out:json][timeout:25];(way["building"](around:20000,{lat},{lon}););out center;'
    try:
        r = requests.get(overpass_url, params={'data': query})
        r.raise_for_status()
        data = r.json()
        min_dist = float('inf')
        for el in data.get('elements', []):
            if 'center' in el:
                dist = geodesic((lat, lon), (el['center']['lat'], el['center']['lon'])).meters
                min_dist = min(min_dist, dist)
        return round(min_dist * 3.28084) if min_dist != float('inf') else None
    except:
        return None

if st.button("**CHECK LEGALITY NOW** 🎯", type="primary"):
    with st.spinner("🔍 Scanning..."):
        dist_ft = get_nearest_building(lat, lon)

    st.markdown(f"### **Results: {lat:.5f}° N, {lon:.5f}° W**")

    st.markdown("### 1. **Congested Areas** (You Are Pinned)")
    map_url = f"https://gis.washoecounty.us/wrms/firearm?center={lat},{lon}&zoom=15"
    components.iframe(map_url, height=500)

    if dist_ft is None:
        st.success("### 2. **Distance** — **REMOTE AREA** → **Likely Legal**")
    else:
        st.metric("**Nearest Dwelling**", f"{dist_ft:,} ft")
        if dist_ft > 5000:
            st.success("**🎯 LEGAL: Rifles/Pistols/ALL**")
        elif dist_ft > 1000:
            st.info("**🔫 LEGAL: Shotguns/BB/Air Rifles ONLY**")
        else:
            st.error("**🚫 ILLEGAL — TOO CLOSE!**")

    st.success("**SAFE TO SHOOT** (if map green) | Not legal advice")
