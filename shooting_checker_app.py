import streamlit as st
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

# VISIBLE GPS BUTTON — NO ALERTS, WORKS ON MOBILE
st.markdown("### Get My Location")
components.html("""
<button onclick="getLocation()" style="
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
function getLocation() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(showPosition, showError, {
            enableHighAccuracy: true,
            timeout: 10000,
            maximumAge: 60000
        });
    } else {
        parent.stAlert("GPS not supported");
    }
}
function showPosition(position) {
    const lat = position.coords.latitude.toFixed(5);
    const lon = position.coords.longitude.toFixed(5);
    const inputs = parent.document.querySelectorAll('input[step="0.0001"]');
    if (inputs.length >= 2) {
        inputs[0].value = lat;
        inputs[1].value = lon;
        inputs[0].dispatchEvent(new Event('input', {bubbles: true}));
        inputs[1].dispatchEvent(new Event('input', {bubbles: true}));
        setTimeout(() => {
            parent.document.querySelector('button[kind="primary"]').click();
        }, 300);
    }
}
function showError(error) {
    let msg = "";
    if (error.code === 1) msg = "Location access denied.";
    else if (error.code === 2) msg = "Location unavailable.";
    else if (error.code === 3) msg = "GPS timeout—try again.";
    else msg = "GPS error.";
    parent.document.getElementById('gps-status') && 
        parent.document.getElementById('gps-status').remove();
    const status = parent.document.createElement('div');
    status.id = 'gps-status';
    status.innerHTML = `<p style="color:red; font-weight:bold;">${msg}</p>`;
    parent.document.body.insertBefore(status, parent.document.body.firstChild);
}
</script>
""", height=100)

# GPS STATUS (visible feedback)
st.markdown("<div id='gps-status'></div>", unsafe_allow_html=True)

# YOUR SAFE ZONE
col1, col2 = st.columns(2)
lat = col1.number_input("Lat", value=39.72009, step=0.0001, format="%.5f")
lon = col2.number_input("Lon", value=-119.92786, step=0.0001, format="%.5f")

if st.button("**CHECK LEGALITY NOW** Target", type="primary"):
    with st.spinner("Scanning..."):
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
            st.success("**LEGAL: Rifles/Pistols/ALL**")
        elif dist_ft > 1000:
            st.info("**LEGAL: Shotguns/BB/Air Rifles ONLY**")
        else:
            st.error("**ILLEGAL — TOO CLOSE!**")

    st.success("**SAFE TO SHOOT** (if map green) | Not legal advice")
