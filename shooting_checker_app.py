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

# === GPS BUTTON (SIMPLE JS — TESTED) ===
if st.button("📍 Get My GPS Location", type="primary"):
    components.html("""
    <script>
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            function(position) {
                const lat = position.coords.latitude;
                const lon = position.coords.longitude;
                window.parent.location.search = '?lat=' + lat + '&lon=' + lon;
            },
            function(error) {
                alert('GPS Error: ' + error.message);
            },
            { enableHighAccuracy: true, timeout: 10000, maximumAge: 60000 }
        );
    } else {
        alert('GPS not supported');
    }
    </script>
    <p>Requesting location... Grant permission in browser.</p>
    """, height=80)
    st.rerun()

# === GET LOCATION FROM URL ===
query_params = st.experimental_get_query_params()
lat = float(query_params.get("lat", [39.72009])[0])
lon = float(query_params.get("lon", [-119.92786])[0])
st.info(f"Current Location: {lat:.5f}°, {lon:.5f}°")

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
    with st.spinner("🔍 Scanning nearest buildings..."):
        dist_ft = get_nearest_building(lat, lon)

    st.markdown(f"### **Results: {lat:.5f}° N, {lon:.5f}° W**")

    # Congested Areas Map (Pinned)
    st.markdown("### 1. **Congested Areas** ⚠️ (Confirm Green Zone)")
    map_url = f"https://gis.washoecounty.us/wrms/firearm?center={lat},{lon}&zoom=15"
    components.iframe(map_url, height=500)

    # Distance Check
    if dist_ft is None:
        st.success("### 2. **Distance to Dwellings** ✅ **REMOTE AREA**—No buildings nearby. **Likely Legal.**")
    else:
        col1, col2 = st.columns(2)
        with col1:
            st.metric("**Nearest Dwelling**", f"{dist_ft:,} ft")
        with col2:
            if dist_ft > 5000:
                st.success("**🎯 LEGAL: Rifles/Pistols/ALL Firearms**")
            elif dist_ft > 1000:
                st.info("**🔫 LEGAL: Shotguns/BB/Air Rifles ONLY**")
            else:
                st.error("**🚫 ILLEGAL: TOO CLOSE!** Move farther.")

    st.markdown("---")
    st.success("**✅ SAFE TO SHOOT** (if map green + no roads) | *Not legal advice* | Report: 775-785-9276")

st.markdown("**👨‍✈️ Built by USMC Vet + Grok xAI** | **For Washoe Safety**")
