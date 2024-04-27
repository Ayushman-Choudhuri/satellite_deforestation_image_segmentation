import openai
from groq import Groq

# import matplotlib.pyplot as plt
# import numpy as np
# import pandas as pd

import json

from dotenv import load_dotenv
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

### Loading the keys

# my keys are in ~/Documents/TUMai-hackathon/openai-key

load_dotenv()
client = Groq(api_key=os.getenv('GROQ_API_KEY'))

GROQ_API_KEY = os.getenv('GROQ_API_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

assert GROQ_API_KEY is not None
assert OPENAI_API_KEY is not None

print(f'OpenAI key length: {len(OPENAI_API_KEY)}')
print(f'Groq key length: {len(GROQ_API_KEY)}')

### API request

client = Groq(api_key=GROQ_API_KEY)

def response(text, temperature=0.0,max_tokens=1024,json=False):
    text = text + "\nReturn a JSON object." if json else text
    res = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": text,
            }
        ],
        model="llama3-70b-8192",
        # model="llama3-8b-8192",
        temperature=temperature,
        max_tokens=max_tokens,
        response_format= {"type": "json_object"} if json else None
    )
    return res.choices[0].message.content

def lat_long(lat, long):
    prompt = f"""
        You are a helpful weather assistant.
        You present helpful geospatial data.
        Double-check the correctness of the data you provide.

        The location is:
        Latitude: {lat}
        Longitude: {long}
        
        Generate the following data for this location:
        * country: string
        * type of biome: string
        * type of vegetation (if any): string
        * type of forest (if any): string
        * average weather conditions (temperature): two numbers (summer/winter in Celsius, set variable names accordingly)
        * precipitation: one number (mm on average)
        
        Don't deviate from this format.
        If you deviate, you will be penalized.
    """
    return response(prompt, json=True)

# print("This is a regular request to the model:")
# print(response("Give me a random number between 1 and 42.", temperature=2.0))
# print("This is a request for a latitude and longitude:")
# print(lat_long(45.1, 11.4))

### FastAPI

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/llm/{lat}/{long}")
def llm_request(lat, long):
    response = lat_long(lat, long)
    return json.loads(response)

# work in progress
@app.get("/image")
def image_request():
    res = client.chat.completions.create(
      model="llama3-70b-8192",
      messages=[
        {
          "role": "user",
          "content": [
            {"type": "text", "text": "What’s in this image?"},
            {
              "type": "image_url",
              "image_url": {
                "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Gfp-wisconsin-madison-the-nature-boardwalk.jpg/2560px-Gfp-wisconsin-madison-the-nature-boardwalk.jpg",
              },
            },
          ],
        }
      ],
      max_tokens=300,
    )
    print(type(res))

    return res.choices[0].message.content