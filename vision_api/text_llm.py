import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

def generate_llm_response(directions_text):
    """
    Enhances navigation directions using Google's Gemini API to make them more
    accessible for people with disabilities.
    
    Args:
        directions_text (str): The raw directions from Google Maps API
    
    Returns:
        str: Enhanced, more accessible directions
    """
    # Get API key from environment or use hardcoded key
    gemini_api_key = os.getenv("GEMINI_API_KEY", "AIzaSyBrR1JKgtYcbaosJnEqGMmGgQETO2V4y7g")
    
    # Use the simpler, more focused prompt
    prompt = f"""
    You are a friendly, helpful guide giving walking directions to someone who may have a disability. 
    Rewrite the directions in a calm, clear, and human tone — like you're speaking to someone in person, not a machine.

    Use numbered steps (1., 2., 3., etc.) to make the instructions easy to follow. Keep each step short, natural, and a little descriptive — not robotic, not overly detailed.

    Mention things like turning left/right, street names, or landmarks only if they're in the original directions. Do not add extra info or guess anything. 
    Avoid technical terms and keep it simple and kind.

    Here are the original directions:
    {directions_text}
    """



    
    try:
        # Configure the Gemini API
        genai.configure(api_key=gemini_api_key)
        
        # Initialize the model
        model = genai.GenerativeModel(model_name="gemini-1.5-flash")
        
        # Generate the enhanced directions
        response = model.generate_content(prompt)
        
        # Return the enhanced directions
        if response.text:
            return response.text
        else:
            print("No response text from Gemini API")
            return directions_text
            
    except Exception as e:
        print(f"Exception when calling Gemini API: {str(e)}")
        # Fall back to the original directions if exception occurs
        return directions_text