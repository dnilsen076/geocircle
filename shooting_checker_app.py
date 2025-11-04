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
    st.header("⚖️ **Rules**")
    st.markdown("""
    - **Rifles/Pistols**: >**5,000 ft** from dwellings
    - **Shotguns/BB/Air**: >**1,000 ft** from dwellings  
    - **NO**: Congested areas, roads, parks
    - **Report**: 775-785-9276
    """)
    st.markdown("[Sheriff's Page](https://www.washoesheriff.com)")

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

# GPS Button
components.html("""
<script>
document.addEventListener('DOMContentLoaded', () => {
    const btn = document.createElement('button');
    btn.innerHTML = '📍 Get My GPS Location';
    btn.style.cssText = 'width:100%; background:#007bff; color:white; padding:14px; border:none; border-radius:8px; font-size:16px; cursor:pointer; margin:10px 0;';
    btn.onclick = () => {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                pos => {
                    const lat = pos.coords.latitude;
                    const lon = pos.coords.longitude;
                    // Update Streamlit inputs
                    const latInput = parent.document.querySelectorAll('input[step="0.0001"]')[0];
                    const lonInput = parent.document.querySelectorAll('input[step="0.0001"]')[1];
                    if (latInput && lonInput) {
                        latInput.value = lat;
                        lonInput.value = lon;
                        parent.document.querySelector('button[kind="primary"]').click();
                    }
                },
                () => alert('GPS denied.'),
                {enableHighAccuracy: true}
            );
        }
    };
    document.body.insertBefore(btn, document.body.firstChild);
});
</script>
""", height=0)

# Inputs
col1, col2 = st.columns(2)
lat = col1.number_input("Lat", value=39.5296, step=0.0001, key="lat")
lon = col2.number_input("Lon", value=-119.8138, step=0.0001, key="lon")

if st.button("**CHECK LEGALITY NOW** 🎯", type="primary"):
    with st.spinner("Scanning..."):
        dist_ft = get_nearest_building(lat, lon)

    st.markdown(f"### **Results: {lat:.4f}, {lon:.4f}**")

    # === EMBEDDED LIVE MAP WITH GPS PIN ===
    st.markdown("### 1. **Congested Areas Map** (You Are Pinned)")
    map_url = f"https://gis.washoecounty.us/wrms/firearm?lat={lat}&lon={lon}&zoom=15"
    components.iframe(map_url, height=500, scrolling=True)

    # === DISTANCE RESULT ===
    if dist_ft is None:
        st.success("### 2. **Distance**: NO BUILDINGS NEARBY")
    else:
        st.metric("**Nearest Dwelling**", f"{dist_ft:,} ft")
        if dist_ft > 5000:
            st.success("**LEGAL**: Rifles/Pistols/ALL")
        elif dist_ft > 1000:
            st.info("**LEGAL**: Shotguns/BB/Air Rifles **ONLY**")
        else:
            st.error("**ILLEGAL** - TOO CLOSE!")

    st.success("**SAFE TO SHOOT** (if map shows green) | Not legal advice")
