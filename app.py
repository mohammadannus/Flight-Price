# -*- coding: utf-8 -*-
"""
Created on Thu Aug 22 18:15:36 2024

@author: Hp
"""

import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import time
from datetime import datetime, timedelta

# Set up the WebDriver using headless mode
def get_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run headless Chrome
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)

def select_airport(driver, input_element_id, airport_code):
    try:
        input_element = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.ID, input_element_id))
        )
        input_element.clear()
        input_element.send_keys(airport_code)
        time.sleep(2)  # Wait for suggestions to load
        input_element.send_keys(Keys.ENTER)  # Select the first suggestion
    except Exception as e:
        st.error(f"Exception during airport selection: {e}")

def select_date(driver, date_str):
    try:
        date_input = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.ID, 'ddate'))
        )
        date_input.click()
        driver.execute_script(f"document.getElementById('ddate').value = '{date_str}';")
        return True
    except Exception as e:
        st.error(f"Exception during date selection: {e}")
        return False

def click_search_button(driver):
    try:
        search_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.ID, 'btnSrch'))
        )
        search_button.click()
    except Exception as e:
        st.error(f"Click failed: {e}")

def extract_flight_data(driver):
    flight_data = []
    flights = driver.find_elements(By.CLASS_NAME, 'col-md-12.col-sm-12.main-bo-lis.pad-top-bot.ng-scope')
    for flight in flights:
        try:
            airline_name = flight.find_element(By.CLASS_NAME, 'txt-r4.ng-binding').text
            flight_number = flight.find_element(By.CLASS_NAME, 'txt-r5').text
            departure_time = flight.find_element(By.CLASS_NAME, 'txt-r2-n.ng-binding').text
            arrival_time = flight.find_elements(By.CLASS_NAME, 'txt-r2-n.ng-binding')[1].text
            
            price_element = flight.find_element(By.CSS_SELECTOR, 'div.txt-r6-n.exPrc span.ng-binding')
            price = price_element.text
            
            origin = flight.find_element(By.CLASS_NAME, 'txt-r3-n.ng-binding').text
            destination = flight.find_elements(By.CLASS_NAME, 'txt-r3-n.ng-binding')[1].text

            flight_data.append({
                'Airline Name': airline_name,
                'Flight Number': flight_number,
                'Departure Time': departure_time,
                'Arrival Time': arrival_time,
                'Price': price,
                'Origin': origin,
                'Destination': destination,
            })
        except Exception as e:
            st.error(f"Failed to extract data for a flight: {e}")
    return flight_data

def get_cheapest_flights(origin, destination, travel_date):
    driver = get_driver()
    url = "https://flight.easemytrip.com/FlightList/Index"
    driver.get(url)

    all_flight_data = []
    
    try:
        select_airport(driver, 'FromSector_show', origin)
        select_airport(driver, 'Editbox13_show', destination)
        if not select_date(driver, travel_date):
            driver.quit()
            return []

        click_search_button(driver)
        time.sleep(10)  # Allow time for the search results to load

        flight_data = extract_flight_data(driver)
        all_flight_data.extend(flight_data)
    except Exception as e:
        st.error(f"Exception during search: {e}")
    
    driver.quit()

    # Sort by price and return the top 3 cheapest flights
    sorted_flights = sorted(all_flight_data, key=lambda x: float(x['Price'].replace(',', '').replace('₹', '')))
    return sorted_flights[:3]

# Streamlit app
st.title("Cheapest Flight Finder")

origin_airport = st.text_input("Enter Origin Airport Code (e.g., DEL):", "DEL")
destination_airport = st.text_input("Enter Destination Airport Code (e.g., BLR):", "BLR")
travel_date = st.date_input("Enter Travel Date:", datetime(2024, 8, 24))

if st.button("Find Cheapest Flights"):
    travel_date_str = travel_date.strftime('%d/%m/%Y')
    st.write(f"Searching for flights from {origin_airport} to {destination_airport} on {travel_date_str}...")

    cheapest_flights = get_cheapest_flights(origin_airport, destination_airport, travel_date_str)

    if cheapest_flights:
        df = pd.DataFrame(cheapest_flights)
        st.write("The three cheapest flights are:")
        st.dataframe(df)
        df.to_excel('cheapest_flights.xlsx', index=False)
        st.download_button(label="Download Flights Data", data=open('cheapest_flights.xlsx', 'rb'), file_name='cheapest_flights.xlsx')
    else:
        st.write("No flights found for the given inputs.")
