# api_server.py

# ==============================================================================
# 1. IMPORTS
# ==============================================================================
# We import all the necessary libraries for our API.
# FastAPI is the web framework.
# HTTPException is for sending back error messages.
# CORSMiddleware allows our web app to talk to this API (critical for web browsers).
# HTMLResponse allows us to send back our HTML file directly.
# yfinance is for getting stock data.
# pandas is used by yfinance to handle the data.
# uvicorn is the server that runs our app.
# ------------------------------------------------------------------------------
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import yfinance as yf
import pandas as pd
import uvicorn
import os

# ==============================================================================
# 2. APP INITIALIZATION
# ==============================================================================
# We create an instance of the FastAPI application.
# The title and description will show up in the automatic API docs.
# ------------------------------------------------------------------------------
app = FastAPI(
    title="Trading Signal Data API",
    description="A backend API to serve financial data for the Integrated Trading Signal Generator.",
    version="1.0.0",
)

# ==============================================================================
# 3. MIDDLEWARE SETUP (CORS)
# ==============================================================================
# This is a security feature that web browsers enforce.
# By setting allow_origins=["*"], we are telling the browser that it's okay
# for ANY website (including the one served by Codespaces) to make requests
# to this API. This is safe for this type of application.
# ------------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==============================================================================
# 4. API ENDPOINTS
# ==============================================================================

# ------------------------------------------------------------------------------
# Endpoint 1: The Data Provider
# This is the core of our API. The frontend will call this URL to get data.
# It lives at the path: /api/market_data
# ------------------------------------------------------------------------------
@app.get("/api/market_data")
def get_market_data(symbol: str, interval: str, period: str):
    """
    Fetches historical market data for a given stock ticker using yfinance.
    This endpoint takes the symbol, interval, and period as query parameters.
    """
    try:
        # Use yfinance to download the data. It's stable and handles all the hard work.
        stock_data = yf.download(
            tickers=symbol,
            period=period,
            interval=interval,
            auto_adjust=True,  # Automatically adjusts for stock splits and dividends
            progress=False,    # Hides the download progress bar in the console
            timeout=10         # Set a timeout for the request
        )

        # yfinance returns an empty DataFrame if the ticker is invalid or no data exists.
        if stock_data.empty:
            # We send a 404 "Not Found" error back to the frontend.
            raise HTTPException(
                status_code=404,
                detail=f"No data found for symbol '{symbol}' with the given parameters. It may be an invalid ticker."
            )

        # --- Data Formatting ---
        # The frontend JavaScript expects a very specific JSON format.
        # We will transform the yfinance data to match it perfectly.

        # 1. The 'Date' or 'Datetime' is the index; move it to a regular column.
        stock_data.reset_index(inplace=True)

        # 2. Find the correct date column name ('Datetime' for intraday, 'Date' for daily).
        date_column_name = 'Datetime' if 'Datetime' in stock_data.columns else 'Date'
        
        # 3. Convert the date objects to a standardized string format (ISO 8601).
        # JSON cannot handle Python datetime objects, but it handles strings perfectly.
        stock_data[date_column_name] = stock_data[date_column_name].dt.strftime('%Y-%m-%dT%H:%M:%S')

        # 4. Rename the columns to lowercase to match exactly what the JavaScript code expects.
        # This prevents any errors in the frontend chart rendering.
        stock_data.rename(columns={
            date_column_name: "date",
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Volume": "volume"
        }, inplace=True)
        
        # 5. Convert the cleaned-up pandas DataFrame to a list of dictionaries.
        # e.g., [{'date': '...', 'open': 150.0}, {'date': '...', 'open': 151.0}]
        data_in_json_format = stock_data.to_dict(orient='records')

        # FastAPI automatically converts this Python list into a JSON response.
        return data_in_json_format

    except Exception as e:
        # If any other error occurs (like a network issue), send a 500 "Server Error".
        print(f"An error occurred: {e}") # Log the error to the console for debugging.
        raise HTTPException(status_code=500, detail=f"An internal server error occurred: {str(e)}")

# ------------------------------------------------------------------------------
# Endpoint 2: The HTML File Server
# This is a huge convenience. It serves your main web application file when
# someone visits the root URL of your Codespace.
# It lives at the path: /
# ------------------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    """
    Serves the main HTML file of the trading application.
    """
    html_file_path = 'code (58)_AI M.html'
    if not os.path.exists(html_file_path):
        return HTMLResponse(content="<h1>Error: Frontend file not found</h1><p>Please make sure 'code (58)_AI M.html' is in the root directory.</p>", status_code=404)
    
    with open(html_file_path, "r") as f:
        return HTMLResponse(content=f.read())


# ==============================================================================
# 5. SERVER RUNNER
# ==============================================================================
# This block allows you to run the server by simply typing `python api_server.py`
# in the terminal. However, for development, it's still better to use the
# `uvicorn` command directly for features like auto-reloading.
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",  # This is crucial for Codespaces/Docker/cloud environments
        port=8000,
        reload=True      # Automatically restart the server when you save changes
    )