from geopy.geocoders import Nominatim
import overpy

# Set up with user agent and extended timeout
geolocator = Nominatim(user_agent="ua_navigation_bot", timeout=10)
overpass_api = overpy.Overpass()

def geocode_address(address):
    """Returns latitude and longitude for an address"""
    location = geolocator.geocode(address)
    if location:
        return {"lat": location.latitude, "lon": location.longitude}
    return None

def get_nearby_places(lat, lon, radius=200):
    """Query Overpass API for nearby buildings using lat/lon"""
    query = f"""
    [out:json];
    (
      node(around:{radius},{lat},{lon})["building"];
      way(around:{radius},{lat},{lon})["building"];
      relation(around:{radius},{lat},{lon})["building"];
    );
    out center;
    """
    result = overpass_api.query(query)

    places = []
    for element in result.nodes + result.ways + result.relations:
        name = element.tags.get("name", "Unnamed Building")
        lat = getattr(element, 'lat', getattr(element, 'center_lat', None))
        lon = getattr(element, 'lon', getattr(element, 'center_lon', None))
        if lat and lon:
            places.append({
                "name": name,
                "lat": lat,
                "lon": lon
            })
    return places
