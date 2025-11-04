import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
from geopy.distance import geodesic
import streamlit.components.v1 as components
from folium.plugins import LocateControl

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

# === GET GPS FROM URL OR SESSION STATE ===
# Check if GPS coordinates are in URL parameters first
if "lat" in st.query_params and "lon" in st.query_params:
    try:
        lat = float(st.query_params["lat"])
        lon = float(st.query_params["lon"])
        # Store in session state
        st.session_state.lat = lat
        st.session_state.lon = lon
        st.session_state.gps_obtained = True
    except:
        lat = 39.72009
        lon = -119.92786
        st.session_state.gps_obtained = False
# Otherwise check session state
elif "lat" in st.session_state and "lon" in st.session_state:
    lat = st.session_state.lat
    lon = st.session_state.lon
# Default to Washoe County
else:
    lat = 39.72009
    lon = -119.92786
    st.session_state.gps_obtained = False

# Show different messages based on whether GPS was obtained
if st.session_state.get("gps_obtained", False):
    st.success(f"📍 **Your GPS Location**: {lat:.6f}°, {lon:.6f}°")
else:
    st.warning(f"📍 **Default Location** (Washoe County): {lat:.6f}°, {lon:.6f}° - Click button below to use your location")

# === GPS BUTTON WITH BETTER APPROACH ===
st.markdown("### 📡 Get Your Location")
st.info("💡 **Tip:** Allow location access in your browser when prompted. The page will reload with your coordinates.")

# JavaScript that communicates back to Streamlit via query params
gps_html = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
</head>
<body>
<div style="text-align:center; margin:20px;">
    <button onclick="getGPS()" id="gpsBtn" style="
        width:90%; max-width:400px;
        background:#007bff; color:white;
        padding:18px; border:none; border-radius:12px;
        font-size:18px; font-weight:bold; cursor:pointer;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        transition: background 0.3s;
    ">
        📍 Get My GPS Location
    </button>
    <p id="status" style="margin-top:15px; color:#555; font-weight:500; font-size:14px;"></p>
</div>

<script>
function getGPS() {
    const btn = document.getElementById('gpsBtn');
    const status = document.getElementById('status');
    btn.innerHTML = "🔄 Getting Location...";
    btn.disabled = true;
    btn.style.background = '#6c757d';
    status.innerHTML = "";

    if (!navigator.geolocation) {
        btn.disabled = false;
        btn.style.background = '#007bff';
        btn.innerHTML = "📍 Get My GPS Location";
        status.innerHTML = "❌ GPS not supported by your browser";
        return;
    }

    navigator.geolocation.getCurrentPosition(
        (pos) => {
            const lat = pos.coords.latitude.toFixed(6);
            const lon = pos.coords.longitude.toFixed(6);
            status.innerHTML = "✅ Location found! Reloading...";
            
            // Get the parent window URL (Streamlit app URL)
            const currentUrl = window.location.href;
            const baseUrl = currentUrl.split('?')[0];
            
            // Create new URL with GPS parameters
            const newUrl = baseUrl + '?lat=' + lat + '&lon=' + lon;
            
            // Try multiple methods to reload
            setTimeout(() => {
                // Method 1: Try to navigate parent
                if (window.parent) {
                    window.parent.location.href = newUrl;
                }
                // Method 2: Try to navigate top window
                if (window.top && window.top !== window) {
                    window.top.location.href = newUrl;
                }
                // Method 3: Navigate current window as fallback
                window.location.href = newUrl;
            }, 500);
        },
        (err) => {
            btn.innerHTML = "📍 Get My GPS Location";
            btn.disabled = false;
            btn.style.background = '#007bff';
            let errMsg = "";
            if (err.code === 1) {
                errMsg = "❌ Permission denied. Please allow location access in browser settings.";
            } else if (err.code === 2) {
                errMsg = "❌ Location unavailable. Check your device GPS settings.";
            } else if (err.code === 3) {
                errMsg = "❌ Timeout. Please try again.";
            } else {
                errMsg = "❌ Error: " + err.message;
            }
            status.innerHTML = errMsg;
        },
        {enableHighAccuracy: true, timeout: 20000, maximumAge: 0}
    );
}

// Show success message if we just got GPS
const urlParams = new URLSearchParams(window.location.search);
if (urlParams.has('lat') && urlParams.has('lon')) {
    document.getElementById('status').innerHTML = "✅ GPS coordinates loaded!";
}
</script>
</body>
</html>
"""

components.html(gps_html, height=180, scrolling=False)

# Manual input option as backup
with st.expander("📝 Or Enter Coordinates Manually"):
    col1, col2 = st.columns(2)
    with col1:
        manual_lat = st.number_input("Latitude", value=lat, format="%.6f", step=0.000001)
    with col2:
        manual_lon = st.number_input("Longitude", value=lon, format="%.6f", step=0.000001)
    
    if st.button("📍 Use These Coordinates", type="secondary"):
        st.session_state.lat = manual_lat
        st.session_state.lon = manual_lon
        st.session_state.gps_obtained = True
        st.rerun()

# === FUNCTION TO GET NEARBY BUILDINGS FOR MAP ===
@st.cache_data(ttl=300)
def get_nearby_buildings_for_map(lat, lon, radius_meters=500):
    """Get building coordinates for visualization on map"""
    overpass_url = "https://overpass-api.de/api/interpreter"
    query = f'''
    [out:json][timeout:25];
    (
      way["building"](around:{radius_meters},{lat},{lon});
    );
    out geom;
    '''
    
    try:
        r = requests.get(overpass_url, params={'data': query}, timeout=30)
        r.raise_for_status()
        data = r.json()
        
        buildings = []
        for el in data.get('elements', []):
            if 'geometry' in el and len(el['geometry']) > 0:
                # Get the building outline
                coords = [(node['lat'], node['lon']) for node in el['geometry'] 
                         if 'lat' in node and 'lon' in node]
                if coords:
                    buildings.append(coords)
        
        return buildings
    except:
        return []

# === MAP WITH GPS PIN ===
st.markdown("### 🗺️ Your Location on Map")

# Add a map with location plugin that can also get GPS
m = folium.Map(location=[lat, lon], zoom_start=17)

# Add marker with custom icon - different color based on if GPS was obtained
marker_color = 'red' if st.session_state.get("gps_obtained", False) else 'blue'
marker_text = "Your GPS Location" if st.session_state.get("gps_obtained", False) else "Default Location (Click GPS button above)"

folium.Marker(
    [lat, lon],
    popup=f"<b>{marker_text}</b><br>Lat: {lat:.6f}<br>Lon: {lon:.6f}",
    tooltip=f"📍 {marker_text}",
    icon=folium.Icon(color=marker_color, icon='info-sign')
).add_to(m)

# Add circle to show 1000ft radius
folium.Circle(
    [lat, lon],
    radius=304.8,  # 1000 feet in meters
    color='orange',
    fill=True,
    fillColor='orange',
    fillOpacity=0.15,
    popup='<b>1000 ft radius</b><br>(Shotgun minimum)',
    tooltip='1000 ft radius'
).add_to(m)

# Add circle to show 5000ft radius
folium.Circle(
    [lat, lon],
    radius=1524,  # 5000 feet in meters
    color='red',
    fill=True,
    fillColor='red',
    fillOpacity=0.08,
    popup='<b>5000 ft radius</b><br>(Rifle/Pistol minimum)',
    tooltip='5000 ft radius'
).add_to(m)

# Show nearby buildings on map for debugging
if st.session_state.get("show_buildings", False):
    with st.spinner("Loading nearby buildings on map..."):
        buildings = get_nearby_buildings_for_map(lat, lon, 500)
        for building_coords in buildings:
            folium.Polygon(
                locations=building_coords,
                color='purple',
                weight=2,
                fill=True,
                fillColor='purple',
                fillOpacity=0.3,
                popup='Building'
            ).add_to(m)
        if buildings:
            st.caption(f"🏘️ Showing {len(buildings)} nearby buildings on map")

# Add the Locate Control plugin for GPS
LocateControl(auto_start=False, position='topleft').add_to(m)

st_folium(m, width=700, height=500, key="main_map")

st.caption("💡 **Map Tip:** Click the crosshair icon (📍) in the top-left of the map to center on your location!")

# Add checkbox to show buildings
show_buildings_checkbox = st.checkbox("🏘️ Show nearby buildings on map (debug)", value=st.session_state.get("show_buildings", False))
if show_buildings_checkbox != st.session_state.get("show_buildings", False):
    st.session_state.show_buildings = show_buildings_checkbox
    st.rerun()

# === LEGALITY CHECK ===
@st.cache_data(ttl=300)
def get_nearest_building(lat, lon):
    overpass_url = "https://overpass-api.de/api/interpreter"
    
    # Start with smaller radius (1 mile = 1609 meters) for faster, more accurate results
    # Query for buildings and houses within radius
    query = f'''
    [out:json][timeout:30];
    (
      way["building"](around:1609,{lat},{lon});
      relation["building"](around:1609,{lat},{lon});
    );
    out geom;
    '''
    
    try:
        r = requests.get(overpass_url, params={'data': query}, timeout=35)
        r.raise_for_status()
        data = r.json()
        
        min_dist = float('inf')
        buildings_found = 0
        
        for el in data.get('elements', []):
            buildings_found += 1
            
            # For ways with geometry
            if 'geometry' in el and len(el['geometry']) > 0:
                # Calculate distance to each node in the building outline
                for node in el['geometry']:
                    if 'lat' in node and 'lon' in node:
                        dist = geodesic((lat, lon), (node['lat'], node['lon'])).meters
                        min_dist = min(min_dist, dist)
            
            # For elements with center point
            elif 'center' in el:
                building_lat = el['center']['lat']
                building_lon = el['center']['lon']
                dist = geodesic((lat, lon), (building_lat, building_lon)).meters
                min_dist = min(min_dist, dist)
            
            # For nodes with direct lat/lon
            elif 'lat' in el and 'lon' in el:
                building_lat = el['lat']
                building_lon = el['lon']
                dist = geodesic((lat, lon), (building_lat, building_lon)).meters
                min_dist = min(min_dist, dist)
        
        # If no buildings found in 1 mile, try larger search
        if buildings_found == 0:
            st.info("🔍 No buildings found nearby, searching wider area...")
            query = f'''
            [out:json][timeout:30];
            (
              way["building"](around:8000,{lat},{lon});
              relation["building"](around:8000,{lat},{lon});
            );
            out geom;
            '''
            r = requests.get(overpass_url, params={'data': query}, timeout=35)
            r.raise_for_status()
            data = r.json()
            
            for el in data.get('elements', []):
                buildings_found += 1
                
                if 'geometry' in el and len(el['geometry']) > 0:
                    for node in el['geometry']:
                        if 'lat' in node and 'lon' in node:
                            dist = geodesic((lat, lon), (node['lat'], node['lon'])).meters
                            min_dist = min(min_dist, dist)
                elif 'center' in el:
                    dist = geodesic((lat, lon), (el['center']['lat'], el['center']['lon'])).meters
                    min_dist = min(min_dist, dist)
                elif 'lat' in el and 'lon' in el:
                    dist = geodesic((lat, lon), (el['lat'], el['lon'])).meters
                    min_dist = min(min_dist, dist)
        
        if buildings_found > 0:
            st.caption(f"📊 Found {buildings_found} buildings in search area")
        
        return round(min_dist * 3.28084) if min_dist != float('inf') else None
        
    except requests.exceptions.Timeout:
        st.error("⏱️ Query timeout. The mapping service is slow. Try again.")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"🌐 Network error: {str(e)}")
        return None
    except Exception as e:
        st.error(f"❌ Error querying buildings: {str(e)}")
        return None

st.markdown("### 🔍 Check Shooting Legality")

if not st.session_state.get("gps_obtained", False):
    st.warning("⚠️ **Using default location.** For accurate results: Click 'Get My GPS Location' above OR use the 📍 button on the map OR enter coordinates manually.")

if st.button("**🎯 CHECK LEGALITY NOW**", type="primary", use_container_width=True):
    with st.spinner("🔍 Scanning for nearby buildings..."):
        dist_ft = get_nearest_building(lat, lon)

    st.markdown(f"### 📊 **Results for: {lat:.6f}°, {lon:.6f}°**")

    if dist_ft is None:
        st.success("✅ **REMOTE AREA** — No buildings found within 5 miles. Likely Legal (verify conditions)")
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

# Debug info (optional - can remove in production)
with st.expander("🔧 Debug Info"):
    st.write("**Query Params:**", dict(st.query_params))
    st.write("**Current Coordinates:**", f"Lat: {lat}, Lon: {lon}")
    st.write("**GPS Obtained:**", st.session_state.get("gps_obtained", False))
    st.write("**Session State Keys:**", list(st.session_state.keys()))
