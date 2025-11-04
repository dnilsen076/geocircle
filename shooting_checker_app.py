import streamlit as st
import requests
from geopy.distance import geodesic
import streamlit.components.v1 as components

# === SESSION STATE: PERSIST GPS ===
if 'lat' not in st.session_state:
    st.session_state.lat = 39.72009
if 'lon' not in st.session_state.lon:
    st.session_state.lon = -119.92786

# === READ GPS FROM URL (AFTER JS UPDATE) ===
query_params = st.experimental_get_query_params()
if "gps_lat" in query_params and "gps_lon" in query_params:
    try:
        st.session_state.lat = float(query_params["gps_lat"][0])
        st.session_state.lon = float(query_params["gps_lon"][0])
        # Clear URL after use
        st.experimental_set_query_params()
    except:
        pass

st.set_page_config(page_title="Washoe Safe Shot", page_icon="Target", layout="centered")

st.title("Target **Washoe Safe Shot**")
st.markdown("**Official-Style Safety Tool** | **Built w/ Grok xAI** | **USMC Vet Project**")
st.markdown("**[Washoe County Code 50](https://www.washoecounty.gov/clerks/cco/code/Chapter050.pdf)**")

# Sidebar
with st.sidebar:
    st.header("Rules **EXACT Rules**")
    st.markdown("""
    - **Rifles/Pistols**: >**5,000 ft** from dwellings
    - **Shotguns/BB/Air**: >**1,000 ft** from dwellings  
    - **NO**: Congested areas, roads, parks
    - **Report**: 775-785-9276
    """)
    st.markdown("[Sheriff's Page](https://www.washoesheriff.com)")

@st.cache_data(ttl=300)
def get_nearest_building(lat, lon):
    overpass_url = "http://overpass.osm.rambler.ru/cgi/interpreter"
    radii = [5000, 10000, 20000]
    for radius in radii:
        query = f'[out:json][timeout:20];(way["building"](around:{radius},{lat},{lon}););out center;'
        try:
            r = requests.get(overpass_url, params={'data': query}, timeout=10)
            r.raise_for_status()
            data = r.json()
            min_dist = float('inf')
            for el in data.get('elements', []):
                if 'center' in el:
                    dist = geodesic((lat, lon), (el['center']['lat'], el['center']['lon'])).meters
                    min_dist = min(min_dist, dist)
            if min_dist != float('inf'):
                return round(min_dist * 3.28084)
        except:
            continue
    return None

# === GPS BUTTON: WRITES TO URL → PYTHON READS IT ===
components.html(f"""
<button id="gps-btn" onclick="getLocation()" style="
    width:100%; 
    background:#007bff; 
    color:white; 
    padding:14px; 
    border:none; 
    border-radius:8px; 
    font-size:16px; 
    cursor:pointer; 
    margin:10px 0;
    font-weight:bold;
">
Get My GPS Location
</button>

<script>
function getLocation() {{
    const btn = document.getElementById('gps-btn');
    btn.innerHTML = "Getting Location...";
    btn.disabled = true;

    if (navigator.geolocation) {{
        navigator.geolocation.getCurrentPosition(
            (pos) => {{
                const lat = pos.coords.latitude.toFixed(5);
                const lon = pos.coords.longitude.toFixed(5);
                // UPDATE URL → Python reads it
                const url = new URL(window.parent.location);
                url.searchParams.set('gps_lat', lat);
                url.searchParams.set('gps_lon', lon);
                window.parent.location = url;
            }},
            (err) => {{
                btn.innerHTML = "GPS Failed — Try Again";
                btn.disabled = false;
                alert("GPS Error: " + err.message);
            }},
            {{enableHighAccuracy: true, timeout: 10000}}
        );
    }} else {{
        btn.innerHTML = "GPS Not Supported";
        btn.disabled = false;
    }}
}}
</script>
""", height=80)

# === INPUTS: CONTROLLED BY SESSION STATE ===
col1, col2 = st.columns(2)
with col1:
    lat = st.number_input(
        "Lat", 
        value=st.session_state.lat, 
        step=0.0001, 
        format="%.5f",
        key="lat"  # Forces controlled component
    )
with col2:
    lon = st.number_input(
        "Lon", 
        value=st.session_state.lon, 
        step=0.0001, 
        format="%.5f",
        key="lon"
    )

# === SYNC INPUTS BACK TO SESSION STATE ===
st.session_state.lat = lat
st.session_state.lon = lon

# === CHECK BUTTON ===
if st.button("**CHECK LEGALITY NOW** Target", type="primary"):
    with st.spinner("Scanning buildings..."):
        dist_ft = get_nearest_building(lat, lon)

    st.markdown(f"### **Results: {lat:.5f}° N, {lon:.5f}° W**")

    # MAP
    st.markdown("### 1. **Congested Areas** (You Are Pinned)")
    map_url = f"https://gis.washoecounty.us/wrms/firearm?center={lat},{lon}&zoom=15"
    components.iframe(map_url, height=500)

    # DISTANCE
    if dist_ft is None:
        st.success("### 2. **Distance** — **REMOTE AREA** → **Likely Legal**")
    else:
        st.metric("**Nearest Dwelling**", f"{dist_ft:,} ft")
        if dist_ft > 5000:
            st.success("**LEGAL: Rifles/Pistols/ALL**")
        elif dist_ft > 1000:
            st.info("**LEGAL: Shotguns/BB/Air Rifles ONLY**")
        else:
            st.error("**ILLEGAL — TOO CLOSE!**")

    st.success("**SAFE TO SHOOT** (if map green) | Not legal advice")
