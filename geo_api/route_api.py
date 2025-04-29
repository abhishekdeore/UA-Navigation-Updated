import requests

def get_osm_route(start_coords, end_coords, profile="walking"):
    """Fetches route instructions between two coordinates using OSRM."""
    base_url = "https://router.project-osrm.org/route/v1"
    coords = f"{start_coords['lon']},{start_coords['lat']};{end_coords['lon']},{end_coords['lat']}"
    url = f"{base_url}/{profile}/{coords}?overview=full&steps=true"

    try:
        response = requests.get(url)
        data = response.json()

        if "routes" not in data or not data["routes"]:
            return ["[Route unavailable]"]

        steps = data["routes"][0]["legs"][0]["steps"]
        directions = []
        for step in steps:
            instruction = step.get("maneuver", {}).get("instruction")
            if instruction:
                directions.append(instruction)
            else:
                directions.append("[Step missing instruction]")
        return directions

    except Exception as e:
        print("[ERROR] Failed to fetch route:", e)
        return ["[Routing failed due to exception]"]
