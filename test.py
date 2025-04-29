import asyncio
from accessibility import capture_building_screenshot

# Replace "MLK Center" with the exact text you see in the map’s suggestion list
async def test():
    path = await capture_building_screenshot("Martin Luther King")
    print("Got screenshot at", path)

asyncio.run(test())
