from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from typing import List, Optional
import requests
import os
from fastapi.templating import Jinja2Templates
import logging
from fastapi.middleware.cors import CORSMiddleware

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all domains (change this in production)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory="templates")

# Google API Key (Replace with your actual API Key if not set in environment variables)
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "AIzaSyCwentK-0B51TzTNvmV8qlb619a2_wKDKc")

class Restaurant(BaseModel):
    name: str
    rating: float
    cuisine: Optional[str] = None
    price_level: Optional[int] = None
    address: str
    place_id: str

def get_restaurants_from_google(location: str) -> List[Restaurant]:
    """ Fetch restaurants using Google Places API """
    logger.info(f"Fetching restaurants from Google Places for: {location}")
    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {
        "query": f"restaurants in {location}",
        "key": GOOGLE_API_KEY,
        "type": "restaurant"
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error(f"Google API request failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch restaurants")

    results = response.json().get("results", [])
    if not results:
        logger.warning(f"No restaurants found for location: {location}")
        return []

    restaurants_list = [
        Restaurant(
            name=r["name"],
            rating=float(r.get("rating", 0.0)),
            price_level=r.get("price_level"),
            address=r.get("formatted_address"),
            place_id=r["place_id"]
        ) for r in results
    ]

    return restaurants_list

@app.get("/")
def index(request: Request):
    return templates.TemplateResponse(
        name="index.html",
        context={"request": request}
    )

@app.get("/restaurants/{location}", response_model=List[Restaurant])
async def get_all_restaurants(location: str):
    """ Fetch restaurants directly from Google Places API """
    return get_restaurants_from_google(location)
