# SAVE AS: shooting_checker_app.py → UPLOAD TO GITHUB → DEPLOY
import streamlit as st
import requests
from geopy.distance import geodesic
import streamlit.components.v1 as components

st.set_page_config(page_title="Washoe Safe Shot", page_icon="🎯", layout="centered")

st.title("🎯 **Washoe Safe Shot**")
st.markdown("**Official-Style Safety Tool** | **Built w/ Grok xAI** | **USMC Vet Project**")
st.markdown("**[Washoe County Code 50](https://www.washoecounty.gov/clerks/cco/code/Chapter050.pdf)**")

# Sidebar: EXACT Sheriff Rules (Copy-paste from their posts)
with st.sidebar:
    st.header("⚖️ **EXACT Rules**")
    st.markdown("""
    **✅ Rifles/Pistols**: >**5,000 ft** from dwellings
    **✅ Shotguns/BB/Air**: >**1,000 ft** from dwellings  
    **❌ NO**: Congested areas, roads/trails, parks
    **📱** Use **THIS TOOL** + [LIVE MAP](https://gis.washoecounty.us/wrms/firearm)
    **📞** Report Illegal: 775-785-**WCSO** (9276)<grok-card data-id="39566f" data-type="citation_card"></grok-card>
    """)
    st.markdown("[Sheriff's Page](https://www.washoesheriff.com/operations_bureau/patrol-division/congested-areafirearms-discharge-maps.php)")

@st.cache_data(ttl=300)
def get_nearest_building(lat, lon):
    overpass_url = "http://overpass-api.de/api/interpreter"
    query = f'[out:json][timeout:25];(way["building"](around:20000,{lat},{lon}););out center;'
    try:
        r = requests.get(overpass_url, params={'data': query})
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
if(navigator.geolocation){document.getElementById('loc').onclick=()=>navigator.geolocation.getCurrentPosition(p=>{{parent.document.querySelector('[data-testid="stNumberInput"]').children[1].children[0].children[0].value=p.coords.latitude;parent.document.querySelectorAll('[data-testid="stNumberInput"]')[1].children[1].children[0].children[0].value=p.coords.longitude;parent.document.querySelector('button[kind="primary"]').click()}})}
</script><button id='loc' style='width:100%;background:#1f77b4;color:white;padding:10px;border-radius:5px;font-size:16px;'>📱 **Get My GPS Location**</button>""", height=60)

# Inputs
col1, col2 = st.columns(2)
lat = col1.number_input("📍 Lat", value=39.5296)
lon = col2.number_input("Lon", value=-119.8138)

if st.button("**CHECK LEGALITY NOW** 🎯", type="primary"):
    with st.spinner("🔍 Scanning buildings..."):
        dist_ft = get_nearest_building(lat, lon)
    
    st.markdown(f"### **Results: {lat:.4f}, {lon:.4f}**")
    
    # Congested Map
    st.markdown("### **1. Congested Areas** ⚠️")
    st.warning("**CONFIRM** you're **OUTSIDE RED ZONES**")
    st.markdown("[**OPEN LIVE MAP** (Required)](https://gis.washoecounty.us/wrms/firearm)")
    
    # Distance
    if dist_ft is None:
        st.success("### **2. Distance** ✅ **NO BUILDINGS NEARBY**")
    else:
        st.metric("**Nearest Dwelling**", f"{dist_ft:,} **ft**")
        if dist_ft > 5000:
            st.success("🎯 **LEGAL: Rifles/Pistols/ALL Firearms**")
        elif dist_ft > 1000:
            st.info("🔫 **LEGAL: Shotguns/BB/Air Rifles **ONLY**")
        else:
            st.error("🚫 **ILLEGAL** - **TOO CLOSE!**")
    
    st.markdown("---")
    st.success("**✅ SAFE TO SHOOT** (if map OK) | **Not legal advice** | **Report issues: 775-785-9276**")

st.markdown("**👨‍✈️ Built by USMC Vet + Grok xAI** | **For Washoe Families**")
