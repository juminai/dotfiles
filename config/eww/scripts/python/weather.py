#!/usr/bin/env python3
# juminai @ github

import requests
import json
import time
import os
from utils import update_eww, WEATHER_DIR

api_key = '56bfec39d45f284396f7e099cf4d150e'
city_id = '3466537'
units = 'metric'
exclude = 'minute'


def get_weather(city_id, api_key, units):
    url = f"http://api.openweathermap.org/data/2.5/weather?id={city_id}&appid={api_key}&units={units}"

    req = requests.get(url)
    data = req.json()

    city = data["name"]
    lon = data["coord"]["lon"]
    lat = data["coord"]["lat"]

    current = {
        "temp": data["main"]["temp"],
        "feels_like": data["main"]["feels_like"],
        "temp_min": data["main"]["temp_min"],
        "temp_max": data["main"]["temp_max"],
        "humidity": data["main"]["humidity"],
        "description": data["weather"][0]["description"],
        "icon": get_icon(data["weather"][0]["icon"]),
        "icon_image": get_icon_image(data["weather"][0]["icon"]),
    }

    url2 = f"https://api.openweathermap.org/data/2.5/onecall?lat={lat}&lon={lon}&exclude={exclude}&appid={api_key}&units={units}"

    req2 = requests.get(url2)
    data2 = req2.json()

    daily_data = []

    for i in data2["daily"][1:8]:
        min_temp = i["temp"]["min"]
        max_temp = i["temp"]["max"]
        description = i['weather'][0]['description']
        icon = get_icon(i['weather'][0]['icon'])
        icon_image = get_icon_image(i['weather'][0]['icon'])

        dt = i['dt']

        day = {
            "dt": dt,
            "temp_min": min_temp,
            "temp_max": max_temp,
            "description": description,
            "icon": icon,
            "icon_image": icon_image,
        }

        daily_data.append(day)

    hourly_data = []

    for i in data2["hourly"][1:8]:
        temp = i["temp"]
        description = i['weather'][0]['description']
        icon = get_icon(i['weather'][0]['icon'])
        icon_image = get_icon_image(i['weather'][0]['icon'])
        dt = i['dt']

        hour = {
            "dt": dt,
            "temp": temp,
            "description": description,
            "icon": icon,
            "icon_image": icon_image,
        }

        hourly_data.append(hour)

    return {
        "city": city, 
        "current": current, 
        "daily": daily_data,
        "hourly": hourly_data
    }


def get_icon_image(icon_code):
    icon_path = f"{WEATHER_DIR}/{icon_code}.png"
    
    if not os.path.exists(icon_path):
        base_url = "http://openweathermap.org/img/wn/"
        icon_url = f"{base_url}{icon_code}@4x.png"

        response = requests.get(icon_url)
        with open(icon_path, 'wb') as icon:
            icon.write(response.content)

    return icon_path


def get_icon(icon_code):
    icon_map = {
        "01d": "",
        "01n": "",
        "02d": "",
        "02n": "",
        "03d": "",
        "03n": "",
        "04d": "",
        "04n": "",
        "09d": "",
        "09n": "",
        "10d": "",
        "10n": "",
        "11d": "",
        "11n": "",
        "13d": "",
        "13n": "",
        "40d": "",
        "40n": "",
    }
    return icon_map.get(icon_code, "")


if __name__ == "__main__":
    while True:
        weather = get_weather(city_id, api_key, units)
        
        if weather:
            update_eww("weather", weather)
        time.sleep(1800)