
# ============================================================
# LONDON WEATHER AI AGENT
# File: agent.py
# ============================================================

# STEP 1: IMPORT REQUIRED LIBRARIES

import os
import json
import requests

from groq import Groq


# ============================================================
# STEP 2: INITIALIZE GROQ CLIENT
# ============================================================


# ============================================================
# STEP 2: INITIALIZE GROQ CLIENT
# ============================================================


# ============================================================
# STEP 2: INITIALIZE GROQ CLIENT
# ============================================================

import streamlit as st

# First check environment variables
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

# If unavailable, check Streamlit Secrets
if not GROQ_API_KEY:

    try:
        GROQ_API_KEY = st.secrets["GROQ_API_KEY"]

    except (KeyError, FileNotFoundError):
        GROQ_API_KEY = None

# Validate API key
if not GROQ_API_KEY:

    raise ValueError(
        "GROQ_API_KEY is missing. "
        "Please configure it in Streamlit Cloud Settings > Secrets."
    )

# Initialize Groq client
client = Groq(api_key=GROQ_API_KEY)

MODEL = "openai/gpt-oss-20b"



# ============================================================
# STEP 3: CREATE WEATHER TOOL
# ============================================================

def get_weather(city):

    """
    Retrieves current weather and a two-day forecast
    using Open-Meteo APIs.
    """

    try:

        # ----------------------------------------------------
        # A. GEOCODING API
        # Find latitude and longitude of the city
        # ----------------------------------------------------

        geocoding_url = (
            "https://geocoding-api.open-meteo.com/v1/search"
        )

        geo_params = {
            "name": city,
            "count": 1,
            "language": "en",
            "format": "json"
        }

        geo_response = requests.get(
            geocoding_url,
            params=geo_params,
            timeout=15
        )

        geo_response.raise_for_status()

        geo_data = geo_response.json()

        if not geo_data.get("results"):

            return json.dumps({
                "error": f"City '{city}' was not found."
            })

        location = geo_data["results"][0]

        latitude = location["latitude"]
        longitude = location["longitude"]

        city_name = location["name"]
        country = location.get("country", "Unknown")


        # ----------------------------------------------------
        # B. WEATHER API
        # Retrieve current weather and forecast
        # ----------------------------------------------------

        weather_url = (
            "https://api.open-meteo.com/v1/forecast"
        )

        weather_params = {

            "latitude": latitude,
            "longitude": longitude,

            "current": (
                "temperature_2m,"
                "relative_humidity_2m,"
                "apparent_temperature,"
                "precipitation,"
                "rain,"
                "showers,"
                "weather_code,"
                "wind_speed_10m"
            ),

            "daily": (
                "weather_code,"
                "temperature_2m_max,"
                "temperature_2m_min,"
                "precipitation_probability_max,"
                "wind_speed_10m_max"
            ),

            "forecast_days": 2,
            "timezone": "auto"
        }

        weather_response = requests.get(
            weather_url,
            params=weather_params,
            timeout=15
        )

        weather_response.raise_for_status()

        weather_data = weather_response.json()


        # ----------------------------------------------------
        # C. ORGANIZE WEATHER INFORMATION
        # ----------------------------------------------------

        result = {

            "city": city_name,

            "country": country,

            "timezone": weather_data.get("timezone"),

            "current_weather": weather_data.get("current"),

            "daily_forecast": weather_data.get("daily")

        }

        return json.dumps(result, indent=2)


    except requests.exceptions.RequestException as error:

        return json.dumps({
            "error": f"Weather API request failed: {str(error)}"
        })

    except Exception as error:

        return json.dumps({
            "error": str(error)
        })


# ============================================================
# STEP 4: DEFINE WEATHER TOOL FOR THE LLM
# ============================================================

tools = [

    {
        "type": "function",

        "function": {

            "name": "get_weather",

            "description": (
                "Retrieve current weather information "
                "and a two-day forecast for a given city. "
                "Use this tool whenever the user asks "
                "about current weather or weather forecasts."
            ),

            "parameters": {

                "type": "object",

                "properties": {

                    "city": {

                        "type": "string",

                        "description": (
                            "Name of the city, for example London"
                        )

                    }

                },

                "required": ["city"]
            }
        }
    }
]


# ============================================================
# STEP 5: DEFINE SYSTEM PROMPT
# ============================================================

SYSTEM_PROMPT = """
You are a helpful AI Weather Assistant.

Your job is to answer questions about weather.

RULES:

1. Always use the get_weather tool when the user
   asks about current weather or weather forecasts.

2. Never invent weather information.

3. Use the actual information returned by the
   weather API.

4. Explain weather conditions in simple language.

5. If precipitation probability is high, advise
   the user whether carrying an umbrella is useful.

6. If the user asks a follow-up question, use the
   previous conversation to understand the context.

7. Provide clear and concise answers.

8. Mention the city and country in your answer.

9. If the user asks about a city that is not specified,
   ask which city they mean instead of guessing.

10. Distinguish current conditions from forecast data.
"""


# ============================================================
# STEP 6: BUILD THE AGENT HARNESS
# ============================================================

def run_agent(user_question, chat_history=None):

    """
    Coordinates:

    1. User input
    2. LLM
    3. Tool calling
    4. Weather API execution
    5. Tool response
    6. Final LLM response
    """

    # --------------------------------------------------------
    # STEP 1: PREPARE CONVERSATION HISTORY
    # --------------------------------------------------------

    messages = [

        {
            "role": "system",
            "content": SYSTEM_PROMPT
        }

    ]

    if chat_history is not None:

        messages.extend(chat_history)

    else:

        messages.append({

            "role": "user",

            "content": user_question

        })


    # --------------------------------------------------------
    # STEP 2: SEND CONVERSATION TO THE LLM
    # --------------------------------------------------------

    max_iterations = 5

    for iteration in range(max_iterations):

        response = client.chat.completions.create(

            model=MODEL,

            messages=messages,

            tools=tools,

            tool_choice="auto"

        )

        response_message = response.choices[0].message


        # ----------------------------------------------------
        # STEP 3: CHECK WHETHER LLM REQUESTED A TOOL
        # ----------------------------------------------------

        if not response_message.tool_calls:

            return response_message.content or (
                "I could not generate a response."
            )


        # Add assistant's tool-call message to history.

        messages.append(
            response_message.model_dump(exclude_none=True)
        )


        # ----------------------------------------------------
        # STEP 4: EXECUTE REQUESTED TOOLS
        # ----------------------------------------------------

        for tool_call in response_message.tool_calls:

            function_name = tool_call.function.name

            function_args = json.loads(
                tool_call.function.arguments
            )

            if function_name == "get_weather":

                city = function_args["city"]

                print(
                    f"\n[Agent Harness] Executing tool: "
                    f"get_weather({city})"
                )

                tool_result = get_weather(city)

            else:

                tool_result = json.dumps({

                    "error": "Unknown tool requested."

                })


            # ------------------------------------------------
            # STEP 5: SEND TOOL RESULT BACK TO THE LLM
            # ------------------------------------------------

            messages.append({

                "role": "tool",

                "tool_call_id": tool_call.id,

                "content": tool_result

            })


    # --------------------------------------------------------
    # STEP 6: HANDLE MAXIMUM ITERATION LIMIT
    # --------------------------------------------------------

    return (
        "The agent reached its maximum tool execution "
        "limit. Please try asking your question again."
    )


# ============================================================
# END OF AGENT HARNESS
# ============================================================
