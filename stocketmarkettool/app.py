import yfinance as yf
from flask import Flask, render_template, jsonify, request, send_from_directory
from multiprocessing import Pool, cpu_count, current_process
import numpy as np
from sklearn.linear_model import LinearRegression
from datetime import datetime, timedelta
import os

app = Flask(__name__)

# Serve the index.html file
@app.route('/')
def index():
    return render_template('index.html')

# Custom route for serving static files
@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

# Function to fetch stock data using Yahoo Finance
def fetch_stock_data(symbol):
    try:
        stock = yf.Ticker(symbol)
        data = stock.history(period="1y")  # Fetching 1 year of historical data
        if data.empty:
            raise ValueError(f"No data found for {symbol}")
        return data
    except Exception as e:
        print(f"Error fetching data for {symbol}: {e}")
        return None

# Function to predict future prices using linear regression
def predict_future_prices(prices, days_ahead=5):
    closing_prices = prices['Close'].values.reshape(-1, 1)
    
    # Ensure the dates are timezone-naive before performing subtraction
    dates = np.array([(date.replace(tzinfo=None) - datetime(1970, 1, 1)).days for date in prices.index]).reshape(-1, 1)  # Convert dates to days

    # Fit a Linear Regression model
    model = LinearRegression()
    model.fit(dates, closing_prices)

    # Predict future values
    future_dates = np.array([(datetime.now() + timedelta(days=i) - datetime(1970, 1, 1)).days for i in range(1, days_ahead + 1)]).reshape(-1, 1)
    predicted_prices = model.predict(future_dates)

    return predicted_prices.flatten().tolist()

# Simple moving average function to calculate trends
def calculate_trend(prices, window_size=5):
    if prices.empty:  # Check if the DataFrame is empty
        return []
    closing_prices = prices['Close'].values
    trend = np.convolve(closing_prices, np.ones(window_size), 'valid') / window_size
    return trend.tolist()

# Function to log and display CPU core usage
def log_cpu_usage(symbol, process_id):
    try:
        # Check if running on Unix-like system (Linux/macOS)
        if os.name == 'posix':
            core = os.sched_getaffinity(0)  # Get the CPU core the process is using
            print(f"Process {process_id} for symbol {symbol} is running on CPU cores: {core}")
        elif os.name == 'nt':  # Windows
            # Log the process ID and the number of available CPUs
            num_cores = os.cpu_count()  # Windows doesn't expose core affinity, but we can log available CPUs
            print(f"Process {process_id} for symbol {symbol} (Windows) is using {num_cores} cores.")
    except Exception as e:
        print(f"Error logging CPU usage for {symbol}: {e}")

# Function to process multiple stock data requests in parallel
def process_stocks(symbols):
    # Create a pool of workers based on the number of CPU cores
    with Pool(processes=cpu_count()) as pool:
        # Fetch stock data concurrently
        stock_data = pool.map(fetch_stock_data, symbols)
        
        # Log which process is using which core
        for i, symbol in enumerate(symbols):
            log_cpu_usage(symbol, current_process().pid)

    trends = []
    predictions = []

    for data in stock_data:
        if data is not None:
            # Calculate trends using moving average
            trend = calculate_trend(data)
            trends.append(trend)
            
            # Predict future prices
            predicted_prices = predict_future_prices(data)
            predictions.append(predicted_prices)
        else:
            trends.append([])
            predictions.append([])

    return trends, predictions

@app.route('/get_trends', methods=['POST'])
def get_trends():
    symbols = request.json.get('symbols', [])
    if not symbols:
        return jsonify({'error': 'No symbols provided'}), 400
    
    # Process stocks in parallel and get trends and predictions
    trends, predictions = process_stocks(symbols)
    
    response = {
        'trends': trends,
        'predictions': predictions,
        'status': 'success',
        'message': 'Trends and predictions calculated successfully',
    }
    return jsonify(response)

if __name__ == '__main__':
    # Avoid debug mode for multiprocessing
    app.run(debug=False, host='0.0.0.0', port=5000)
