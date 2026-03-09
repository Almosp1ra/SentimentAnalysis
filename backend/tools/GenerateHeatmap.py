from geopy.geocoders import Nominatim
from functools import lru_cache
import folium
from folium.plugins import HeatMap

"""
热力图模块，包括地点转经纬度和生成热力图函数
地点转经纬度，使用缓存加速 API 查询
"""

geolocator = Nominatim(user_agent="geopy_app", timeout=5)

# 地点转经纬度
@lru_cache(maxsize=10000)   # 缓存结果，避免重复查询
def GetLatLong(location):
    if not location:
        return None, None
    try:
        loc = geolocator.geocode(location)
        if loc:
            return loc.latitude, loc.longitude
    except Exception:
        return None, None
    return None, None

# 生成热力图
def GenerateHeatmap(heatData, radius=15, gradient={0.0: 'red', 0.5: 'yellow', 1.0: 'blue'}):
    avg_lat = sum([d[0] for d in heatData])/len(heatData)
    avg_lon = sum([d[1] for d in heatData])/len(heatData)
    m = folium.Map(location=[avg_lat, avg_lon], zoom_start=2)
    HeatMap(heatData, radius=radius, gradient=gradient).add_to(m)
    return m

if __name__ == "__main__":
    location = 'Victoria Australia'
    print(GetLatLong(location))
    location = 'fukuoka, japan'
    print(GetLatLong(location))
    location = 'Florida, USA'
    print(GetLatLong(location))
    