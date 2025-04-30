@app.post("/navigate")
async def navigate(req: Request):
    try:
        data = await req.json()
        src_address = data.get("source_address")
        dest_name = data.get("destination_building", "").strip()
        
        print(f"Navigate request from '{src_address}' to '{dest_name}'")
        
        if not src_address or not dest_name:
            return JSONResponse(content={"message": "⚠️ Missing source or destination."}, status_code=400)
        
        # Find destination building
        clean_dest_name = clean_building_name(dest_name)
        match = find_building_match(clean_dest_name, geo_df)
        
        if match is None or match.empty:
            return JSONResponse(content={"message": f"⚠️ Destination building '{clean_dest_name}' not found."}, status_code=404)
        
        # Get destination coordinates
        dest_lat, dest_lon = match.iloc[0]["Latitude"], match.iloc[0]["Longitude"]
        
        # Get source coordinates
        src_match = geo_df[geo_df["Address"].str.lower() == src_address.lower()]
        if not src_match.empty:
            src_lat, src_lon = src_match.iloc[0]["Latitude"], src_match.iloc[0]["Longitude"]
            print(f"Found source coordinates from database")
        else:
            print(f"Geocoding source address: '{src_address}'")
            src_lat, src_lon = geocode_address(src_address)
        
        if not all([src_lat, src_lon, dest_lat, dest_lon]):
            return JSONResponse(content={"message": "⚠️ Coordinates missing."}, status_code=400)
        
        # Call Google Directions API
        url = f"https://maps.googleapis.com/maps/api/directions/json"
        params = {
            "origin": f"{src_lat},{src_lon}",
            "destination": f"{dest_lat},{dest_lon}",
            "mode": "walking",
            "key": os.getenv("GOOGLE_API_KEY") or "AIzaSyBrR1JKgtYcbaosJnEqGMmGgQETO2V4y7g"
        }
        
        print(f"Calling Directions API with params: {params}")
        
        response = requests.get(url, params=params)
        data = response.json()
        
        if data.get("status") != "OK":
            print(f"Directions API returned status: {data.get('status')}")
            return JSONResponse(content={"message": f"⚠️ Google Directions API error: {data.get('status')}"}, status_code=500)
        
        # Extract walking directions
        steps = []
        for leg in data.get("routes", [])[0].get("legs", []):
            for step in leg.get("steps", []):
                instructions = step.get("html_instructions", "")
                steps.append(instructions)
        
        if not steps:
            return JSONResponse(content={"message": "⚠️ No directions found."}, status_code=500)
        
        # Format the directions instead of using LLM
        directions = format_directions(steps)
        
        # Add distance and duration if available
        try:
            distance = data["routes"][0]["legs"][0]["distance"]["text"]
            duration = data["routes"][0]["legs"][0]["duration"]["text"]
            directions = f"Total Distance: {distance} | Est. Time: {duration}\n\n{directions}"
        except:
            pass
        
        return {"directions": directions}
    except Exception as e:
        print(f"Error in navigate: {e}")
        return JSONResponse(content={"message": f"⚠️ Failed to get directions: {str(e)}"}, status_code=500)