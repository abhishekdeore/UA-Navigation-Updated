import os
import sys
import pandas as pd
import numpy as np
import requests
import difflib
import re
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
# Remove the LLM import since we won't use it
# from vision_api.text_llm import generate_llm_response

# --- Setup ---
if sys.platform.startswith('win'):
    import asyncio
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

load_dotenv()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Load Data ---
# Load only a single Excel file with all needed data
geo_df = pd.read_excel("geocoded_addresses.xlsx")
building_names_list = geo_df["Name"].str.lower().tolist()

print(f"Loaded {len(geo_df)} buildings from geocoded_addresses.xlsx")
print(f"First few building names: {geo_df['Name'].head().tolist()}")

# --- Helper Functions ---
def normalize(text):
    """Remove all non-alphanumeric characters and convert to lowercase"""
    if not isinstance(text, str):
        return ""
    return re.sub(r'[^a-z0-9]', '', text.lower())

def clean_building_name(name):
    """Remove distance portion if present"""
    if not isinstance(name, str):
        return ""
    return name.split(" (")[0].strip()

def geocode_address(address):
    """Get lat/lon coordinates from Google Geocoding API"""
    GOOGLE_API_KEY  = "AIzaSyBrR1JKgtYcbaosJnEqGMmGgQETO2V4y7g"
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={GOOGLE_API_KEY}"
    try:
        resp = requests.get(url)
        data = resp.json()
        if data.get("status") != "OK":
            print(f"Geocoding failed with status: {data.get('status')}")
            return None, None
        pos = data["results"][0]["geometry"]["location"]
        return pos["lat"], pos["lng"]
    except Exception as e:
        print(f"Error geocoding address: {e}")
        return None, None

def haversine(lat1, lon1, lat2, lon2):
    """Calculate the great circle distance between two points in meters"""
    R = 6371000  # Earth radius in meters
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    dphi = np.radians(lat2 - lat1)
    dlambda = np.radians(lon2 - lon1)
    a = np.sin(dphi/2)**2 + np.cos(phi1)*np.cos(phi2)*np.sin(dlambda/2)**2
    return R * 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))

def clean_html(raw_html):
    """Remove HTML tags from text"""
    cleanr = re.compile('<.*?>')
    return re.sub(cleanr, '', raw_html).strip()

def find_building_match(building_name, df):
    """Find a building in dataframe using multiple matching strategies"""
    if not building_name or not isinstance(building_name, str):
        return None
    
    # Clean the input name
    clean_name = clean_building_name(building_name)
    norm_name = normalize(clean_name)
    
    print(f"Looking for building match: '{building_name}' -> '{clean_name}' -> '{norm_name}'")
    
    # Try exact match
    exact_match = df[df["Name"] == clean_name]
    if not exact_match.empty:
        print(f"Found exact match for '{clean_name}'")
        return exact_match
    
    # Try case-insensitive match
    case_match = df[df["Name"].str.lower() == clean_name.lower()]
    if not case_match.empty:
        print(f"Found case-insensitive match for '{clean_name}'")
        return case_match
    
    # Try normalized match
    df["Name_norm"] = df["Name"].apply(normalize)
    norm_match = df[df["Name_norm"] == norm_name]
    if not norm_match.empty:
        print(f"Found normalized match for '{norm_name}'")
        return norm_match
    
    # Try containment match
    df["Contains"] = df["Name_norm"].apply(lambda x: norm_name in x or x in norm_name)
    contains_match = df[df["Contains"]]
    if not contains_match.empty:
        print(f"Found containment match for '{norm_name}'")
        return contains_match.head(1)  # Take the first match if multiple
    
    # Try fuzzy matching as a last resort
    try:
        match = difflib.get_close_matches(clean_name.lower(), df["Name"].str.lower(), n=1, cutoff=0.6)
        if match:
            fuzzy_match = df[df["Name"].str.lower() == match[0]]
            if not fuzzy_match.empty:
                print(f"Found fuzzy match: '{match[0]}' for '{clean_name}'")
                return fuzzy_match
    except Exception as e:
        print(f"Error in fuzzy matching: {e}")
    
    print(f"No match found for '{clean_name}'")
    return None

def format_directions(steps):
    """Format Google Directions API steps into clean text"""
    if not steps:
        return "No directions available."
    
    formatted = []
    formatted.append("🚶‍♂️ Walking Directions:")
    
    for i, step in enumerate(steps, 1):
        # Clean up the instruction
        instruction = clean_html(step)
        # Add step number
        formatted.append(f"{i}. {instruction}")
    
    # Add a final message
    formatted.append("\n🎯 You have arrived at your destination!")
    
    return "\n".join(formatted)

# --- API Routes ---
@app.post("/start")
async def start():
    return {"message": "👋 Hi! Please type the name of the building you want to navigate to."}

@app.post("/lookup")
async def lookup_building(req: Request):
    try:
        data = await req.json()
        user_input = data.get("building_name", "").strip()
        
        if not user_input:
            return JSONResponse(content={"message": "⚠️ Please enter a building name."}, status_code=400)
        
        # Find building using our matcher
        match = find_building_match(user_input, geo_df)
        
        if match is None or match.empty:
            return JSONResponse(content={"message": "⚠️ Building not found."}, status_code=404)
        
        row = match.iloc[0]
        building_number = row.get("Alpha", "N/A") if "Alpha" in row else "N/A"
        
        return {
            "building_name": row["Name"],
            "building_number": building_number,
            "address": row["Address"],
            "prompt_nearby": "Would you like to see nearby buildings? (yes/no)"
        }
    except Exception as e:
        print(f"Error in lookup_building: {e}")
        return JSONResponse(content={"message": f"⚠️ Error looking up building: {str(e)}"}, status_code=500)

@app.post("/nearby")
async def nearby_buildings(req: Request):
    try:
        data = await req.json()
        address = data.get("address", "")
        
        if not address:
            return JSONResponse(content={"message": "⚠️ No address provided."}, status_code=400)
        
        # Find source coordinates
        match_row = geo_df[geo_df["Address"].str.lower() == address.lower()]
        if not match_row.empty:
            src_lat = match_row.iloc[0]["Latitude"]
            src_lon = match_row.iloc[0]["Longitude"]
            print(f"Found coordinates for '{address}' from database")
        else:
            print(f"Geocoding address: '{address}'")
            src_lat, src_lon = geocode_address(address)
            if src_lat is None:
                return JSONResponse(content={"message": f"⚠️ Failed to geocode address: {address}"}, status_code=400)
        
        # Calculate distances to all other buildings
        valid = geo_df.dropna(subset=["Latitude", "Longitude"]).copy()
        valid["Distance_m"] = valid.apply(
            lambda row: haversine(src_lat, src_lon, row["Latitude"], row["Longitude"]), 
            axis=1
        )
        
        # Filter to buildings within 500 meters
        nearby_df = valid[valid["Distance_m"] <= 200].sort_values("Distance_m")
        
        if nearby_df.empty:
            return JSONResponse(content={"message": "⚠️ No nearby buildings found."}, status_code=404)
        
        # Format response
        nearby_list = [
            {"name": row["Name"], "distance_m": round(row["Distance_m"], 1)}
            for _, row in nearby_df.iterrows()
        ]
        
        print(f"Found {len(nearby_list)} nearby buildings")
        
        return {
            "nearby_buildings": nearby_list,
            "prompt_direction": "Please type the name of the building you want directions to."
        }
    except Exception as e:
        print(f"Error in nearby_buildings: {e}")
        return JSONResponse(content={"message": f"⚠️ Error finding nearby buildings: {str(e)}"}, status_code=500)

# First, add the import at the top of the file
from vision_api.text_llm import generate_llm_response

# Then update the navigate endpoint to use the LLM
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
            "key": "AIzaSyBrR1JKgtYcbaosJnEqGMmGgQETO2V4y7g"
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
        
        # Format the basic directions first
        basic_directions = format_directions(steps)
        
        # Add distance and duration if available
        try:
            distance = data["routes"][0]["legs"][0]["distance"]["text"]
            duration = data["routes"][0]["legs"][0]["duration"]["text"]
            basic_directions = f"Total Distance: {distance} | Est. Time: {duration}\n\n{basic_directions}"
        except:
            pass
        
        # Use LLM to enhance the directions for universal accessibility
        enhanced_directions = generate_llm_response(basic_directions)
        
        return {"directions": enhanced_directions}
    except Exception as e:
        print(f"Error in navigate: {e}")
        return JSONResponse(content={"message": f"⚠️ Failed to get directions: {str(e)}"}, status_code=500)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)