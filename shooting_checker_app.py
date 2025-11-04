import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
from geopy.distance import geodesic
import streamlit.components.v1 as components

st.set_page_config(page_title="Washoe Safe Shot", page_icon="🎯", layout="centered")

st.title("🎯 **Washoe Safe Shot**")
st.markdown("**Official-Style Safety Tool** | **Built w/ Grok xAI** | **USMC Vet Project**")
st.markdown("**[Washoe County Code 50](https://www.washoecounty.gov/clerks/cco/code/Chapter050.pdf)**")

# Sidebar
with st.sidebar:
    st.header("📋 **Rules**")
    st.markdown("""
    - **Rifles/Pistols**: >**5,000 ft** from dwellings
    - **Shotguns/BB/Air**: >**1,000 ft** from dwellings  
    - **NO**: Congested areas, roads, parks
    - **Report**: 775-785-9276
    """)
    st.markdown("[Sheriff's Page](https://www.washoesheriff.com)")

# === GET GPS FROM URL ===
query_params = st.query_params  # Fixed: Updated API
lat = float(query_params.get("lat", "39.72009"))  # Fixed: Direct string access
lon = float(query_params.get("lon", "-119.92786"))  # Fixed: Direct string access

st.success(f"📍 Location: {lat:.5f}°, {lon:.5f}°")

# === GPS BUTTON (WORKS IN FULL BROWSER) ===
st.markdown("### 📡 Get Your Location")
st.info("💡 **Tip:** Allow location access in your browser when prompted. Works best in Chrome/Safari.")

components.html("""
<div style="text-align:center; margin:20px;">
    <button onclick="getGPS()" style="
        width:90%; max-width:400px;
        background:#007bff; color:white; 
        padding:18px; border:none; border-radius:12px; 
        font-size:18px; font-weight:bold; cursor:pointer;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        transition: background 0.3s;
    " onmouseover="this.style.background='#0056b3'" 
       onmouseout="this.style.background='#007bff'">
        📍 Get My GPS Location
    </button>
    <p id="status" style="margin-top:15px; color:#555; font-weight:500;"></p>
</div>

<script>
function getGPS() {
    const btn = document.querySelector('button');
    const status = document.getElementById('status');
    btn.innerHTML = "🔄 Getting Location...";
    btn.disabled = true;
    status.innerHTML = "";

    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            (pos) => {
                const lat = pos.coords.latitude.toFixed(5);
                const lon = pos.coords.longitude.toFixed(5);
                status.innerHTML = "✅ Location found! Updating...";
                
                // Update URL without reloading
                const url = new URL(window.location.href);
                url.searchParams.set('lat', lat);
                url.searchParams.set('lon', lon);
                window.location.href = url.toString();
            },
            (err) => {
                btn.innerHTML = "📍 Get My GPS Location";
                btn.disabled = false;
                let errMsg = "";
                if (err.code === 1) {
                    errMsg = "❌ Permission denied. Please allow location access.";
                } else if (err.code === 2) {
                    errMsg = "❌ Location unavailable. Check your device settings.";
                } else if (err.code === 3) {
                    errMsg = "❌ Timeout. Try again.";
                } else {
                    errMsg = "❌ Error: " + err.message;
                }
                status.innerHTML = errMsg;
            },
            {enableHighAccuracy: true, timeout: 15000, maximumAge: 0}
        );
    } else {
        btn.disabled = false;
        status.innerHTML = "❌ GPS not supported by your browser";
    }
}
</script>
""", height=150)

# === MAP WITH GPS PIN ===
st.markdown("### 🗺️ Your Location on Map")
m = folium.Map(location=[lat, lon], zoom_start=16)

# Add marker with custom icon
folium.Marker(
    [lat, lon],
    popup=f"<b>Your Location</b><br>Lat: {lat:.5f}<br>Lon: {lon:.5f}",
    tooltip="📍 Your Location",
    icon=folium.Icon(color='red', icon='info-sign')
).add_to(m)

# Add circle to show 1000ft radius
folium.Circle(
    [lat, lon],
    radius=304.8,  # 1000 feet in meters
    color='orange',
    fill=True,
    fillColor='orange',
    fillOpacity=0.1,
    popup='1000 ft radius (Shotgun minimum)'
).add_to(m)

# Add circle to show 5000ft radius
folium.Circle(
    [lat, lon],
    radius=1524,  # 5000 feet in meters
    color='red',
    fill=True,
    fillColor='red',
    fillOpacity=0.05,
    popup='5000 ft radius (Rifle/Pistol minimum)'
).add_to(m)

st_folium(m, width=700, height=500)

# === LEGALITY CHECK ===
@st.cache_data(ttl=300)
def get_nearest_building(lat, lon):
    overpass_url = "https://overpass-api.de/api/interpreter"  # Fixed: Use HTTPS
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
                building_lat = el['center']['lat']
                building_lon = el['center']['lon']
            elif 'lat' in el and 'lon' in el:
                building_lat = el['lat']
                building_lon = el['lon']
            else:
                continue
            
            dist = geodesic((lat, lon), (building_lat, building_lon)).meters
            min_dist = min(min_dist, dist)
        
        return round(min_dist * 3.28084) if min_dist != float('inf') else None
    except Exception as e:
        st.error(f"Error querying buildings: {str(e)}")
        return None

st.markdown("### 🔍 Check Shooting Legality")

if st.button("**🎯 CHECK LEGALITY NOW**", type="primary", use_container_width=True):
    with st.spinner("🔍 Scanning for nearby buildings..."):
        dist_ft = get_nearest_building(lat, lon)

    st.markdown(f"### 📊 **Results for: {lat:.5f}°, {lon:.5f}°**")

    if dist_ft is None:
        st.success("✅ **REMOTE AREA** — No buildings found within 12 miles. Likely Legal (verify conditions)")
    else:
        st.metric("🏠 **Nearest Dwelling**", f"{dist_ft:,} ft")
        
        if dist_ft > 5000:
            st.success("✅ **LEGAL: All firearms** (Rifles/Pistols/Shotguns/BB/Air)")
        elif dist_ft > 1000:
            st.warning("⚠️ **LEGAL: Shotguns/BB/Air Rifles ONLY** (No Rifles/Pistols)")
        else:
            st.error("🚫 **ILLEGAL — TOO CLOSE TO DWELLINGS!**")
        
        st.info(f"📏 Distance to 1000ft threshold: {1000 - dist_ft:+,} ft")
        st.info(f"📏 Distance to 5000ft threshold: {5000 - dist_ft:+,} ft")

    st.warning("⚠️ **Disclaimer:** This is informational only, not legal advice. Always verify local regulations and ensure safe shooting practices.")

# Footer
st.markdown("---")
st.markdown("**Note:** Ensure backstop safety, check fire restrictions, and respect private property. Stay safe! 🎯")
