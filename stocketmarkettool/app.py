import yfinance as yf
from flask import Flask, render_template, jsonify, request, send_from_directory
from multiprocessing import Pool, cpu_count, current_process
import threading
import numpy as np
from sklearn.linear_model import LinearRegression
from datetime import datetime, timedelta
import os

# Initialize Flask app
app = Flask(__name__)

# Serve the index.html file
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/discussion')
def discussion():
    return render_template('discussion.html')

# Custom route for serving static files
@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

# Fetch stock data using Yahoo Finance
def fetch_stock_data(symbol, results, index):
    try:
        stock = yf.Ticker(symbol)
        data = stock.history(period="1y")  # Fetch 1 year of historical data
        if data.empty:
            raise ValueError(f"No data found for {symbol}")
        results[index] = data
    except Exception as e:
        print(f"Error fetching data for {symbol}: {e}")
        results[index] = None

# Predict future stock prices using linear regression
def predict_future_prices(prices, days_ahead=5):
    closing_prices = prices['Close'].values.reshape(-1, 1)
    dates = np.array([(date.replace(tzinfo=None) - datetime(1970, 1, 1)).days for date in prices.index]).reshape(-1, 1)

    # Fit the linear regression model
    model = LinearRegression()
    model.fit(dates, closing_prices)

    # Predict future prices
    future_dates = np.array([(datetime.now() + timedelta(days=i) - datetime(1970, 1, 1)).days for i in range(1, days_ahead + 1)]).reshape(-1, 1)
    predicted_prices = model.predict(future_dates)

    return predicted_prices.flatten().tolist()

# Calculate trends using a moving average
def calculate_trend(prices, window_size=5):
    if prices.empty:  # Check if the DataFrame is empty
        return []
    closing_prices = prices['Close'].values
    trend = np.convolve(closing_prices, np.ones(window_size), 'valid') / window_size
    return trend.tolist()

# Log the CPU core usage for each process
def log_cpu_usage(symbol, process_id):
    try:
        if os.name == 'posix':
            core = os.sched_getaffinity(0)
            print(f"Process {process_id} for symbol {symbol} is running on CPU cores: {core}")
        elif os.name == 'nt':
            num_cores = os.cpu_count()
            print(f"Process {process_id} for symbol {symbol} (Windows) is using {num_cores} cores.")
    except Exception as e:
        print(f"Error logging CPU usage for {symbol}: {e}")

# Process multiple stock data requests in parallel using multiprocessing and multithreading
def process_stocks(symbols):
    # Create a list to store results for stock data
    results = [None] * len(symbols)
    threads = []

    # Use threading to fetch stock data concurrently
    for i, symbol in enumerate(symbols):
        thread = threading.Thread(target=fetch_stock_data, args=(symbol, results, i))
        threads.append(thread)
        thread.start()

    # Wait for all threads to finish
    for thread in threads:
        thread.join()

    # Now process the stock data and generate trends and predictions using multiprocessing
    with Pool(processes=cpu_count()) as pool:
        trends_predictions = pool.starmap(process_data, [(data, symbol) for data, symbol in zip(results, symbols)])

    trends, predictions = zip(*trends_predictions)
    return list(trends), list(predictions)

# Helper function to process data (used in multiprocessing pool)
def process_data(data, symbol):
    if data is not None:
        trend = calculate_trend(data)
        predicted_prices = predict_future_prices(data)
    else:
        trend = []
        predicted_prices = []
    
    log_cpu_usage(symbol, current_process().pid)
    return trend, predicted_prices

# Get CPU cores information
def get_cpu_cores():
    if os.name == 'posix':
        core_count = len(os.sched_getaffinity(0))  # Number of CPU cores in use
    elif os.name == 'nt':
        core_count = os.cpu_count()  # Number of CPU cores in total
    else:
        core_count = cpu_count()  # Default to the available cores in multiprocessing
    return core_count

# Endpoint to fetch trends, predictions, and CPU core info
@app.route('/get_trends', methods=['POST'])
def get_trends():
    symbols = request.json.get('symbols', [])
    if not symbols:
        return jsonify({'error': 'No symbols provided'}), 400
    
    # Process stocks in parallel and get trends and predictions
    trends, predictions = process_stocks(symbols)
    
    # Get CPU core count information
    cpu_cores = get_cpu_cores()
    
    response = {
        'trends': trends,
        'predictions': predictions,
        'cpu_cores': cpu_cores,  # Include CPU cores info
        'status': 'success',
        'message': 'Trends and predictions calculated successfully',
    }
    return jsonify(response)

# Main entry point to run the Flask app
if __name__ == '__main__':
    # Avoid debug mode for multiprocessing
    app.run(debug=False, host='0.0.0.0', port=5000)
