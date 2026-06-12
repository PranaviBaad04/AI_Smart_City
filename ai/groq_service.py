# ai/groq_service.py
import json
import os
from groq import Groq
from config import Config

def get_groq_client():
    if not Config.GROQ_API_KEY:
        print("[Warning] GROQ_API_KEY not found in configuration.")
        return None
    try:
        return Groq(api_key=Config.GROQ_API_KEY)
    except Exception as e:
        print(f"[Error] Failed to initialize Groq Client: {e}")
        return None

def get_smart_city_recommendations(category, data_summary):
    """
    Get structured recommendations from Groq API for Traffic, Pollution, or Public Services.
    data_summary: dictionary or text describing current conditions.
    Returns: A dict with keys "risk_level", "issues", "recommendations".
    """
    client = get_groq_client()
    
    # Standard fallback response
    fallback = {
        "risk_level": "Medium",
        "issues": "Unable to connect to AI engine to analyze details.",
        "recommendations": "Check local monitoring dashboards and perform manual inspections of municipal equipment."
    }
    
    if not client:
        return fallback

    system_prompt = (
        "You are an expert AI Smart City Planner. You analyze urban data and provide actionable recommendations. "
        "You must respond ONLY with a valid JSON object matching the following structure:\n"
        "{\n"
        "  \"risk_level\": \"Low / Medium / High\",\n"
        "  \"issues\": \"A concise summary of the active issues identified (1-2 sentences).\",\n"
        "  \"recommendations\": \"A bulleted list of 3-4 specific, actionable strategies to resolve the issues.\"\n"
        "}\n"
        "Do not include any chat prefix or suffix. Return only the JSON object."
    )
    
    if category == "traffic":
        user_prompt = (
            f"Analyze the following traffic data and suggest congestion reduction measures:\n"
            f"{json.dumps(data_summary, indent=2)}\n\n"
            f"Focus on vehicle count, average speed, congestion levels, bottlenecks, and peak flow periods."
        )
    elif category == "pollution":
        user_prompt = (
            f"Analyze the following air quality and noise pollution metrics and suggest mitigation measures:\n"
            f"{json.dumps(data_summary, indent=2)}\n\n"
            f"Focus on AQI score, PM2.5, PM10, CO2 levels, and noise decibels."
        )
    elif category == "services":
        user_prompt = (
            f"Analyze the following municipal public services efficiency log and suggest resource allocation improvements:\n"
            f"{json.dumps(data_summary, indent=2)}\n\n"
            f"Focus on average response times, active issues, and resource distribution between utilities like Water, Electricity, Waste, and Roads."
        )
    else:
        user_prompt = f"Analyze the following smart city metrics:\n{json.dumps(data_summary, indent=2)}"

    try:
        completion = client.chat.completions.create(
            model=Config.GROQ_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            max_tokens=600,
            temperature=0.2
        )
        
        response_text = completion.choices[0].message.content.strip()
        print(f"[Groq AI API Response] {response_text}")
        return json.loads(response_text)
    except Exception as e:
        print(f"[Groq API Error] {e}")
        # Secondary parsing attempt in case JSON format wasn't strictly returned
        try:
            if 'response_text' in locals() and '{' in response_text:
                start = response_text.find('{')
                end = response_text.rfind('}') + 1
                return json.loads(response_text[start:end])
        except Exception:
            pass
        return fallback

def chat_assistant(messages):
    """
    Handles conversational interactions for the AI Chatbot Assistant.
    messages: list of objects like [{"role": "user", "content": "hello"}]
    """
    client = get_groq_client()
    if not client:
        return "I am currently running in offline demo mode. Please configure your GROQ_API_KEY to enable smart chat functionality."
        
    system_prompt = (
        "You are 'MetroBot', the official AI Assistant of the Smart City Administration. "
        "You help city administrators, traffic officers, and citizens monitor urban utilities, "
        "solve congestion issues, report pollution, and navigate municipal programs. "
        "Be professional, clear, and highly helpful. Keep your answers concise and structured."
    )
    
    full_messages = [{"role": "system", "content": system_prompt}] + messages
    
    try:
        completion = client.chat.completions.create(
            model=Config.GROQ_MODEL,
            messages=full_messages,
            max_tokens=500,
            temperature=0.7
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        print(f"[Groq Chat Error] {e}")
        return "Sorry, I am currently having trouble connecting to my AI processor. Please try again in a moment."
