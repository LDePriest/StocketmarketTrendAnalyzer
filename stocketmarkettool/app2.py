from celery import Celery
from flask import Flask, render_template, jsonify, request
import yfinance as yf
import numpy as np
from sklearn.linear_model import LinearRegression
from datetime import datetime, timedelta
import os

# Initialize Flask app
app = Flask(__name__)

# Initialize Celery with Redis as the broker
app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'
celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

# Serve the index.html file
@app.route('/')
def index():
    return render_template('index.html')

# Fetch stock data using Yahoo Finance
def fetch_stock_data(symbol):
    try:
        stock = yf.Ticker(symbol)
        data = stock.history(period="1y")  # Fetch 1 year of historical data
        if data.empty:
            raise ValueError(f"No data found for {symbol}")
        return data
    except Exception as e:
        print(f"Error fetching data for {symbol}: {e}")
        return None

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

# Task for fetching stock data and calculating trends and predictions
@celery.task
def process_stock(symbol):
    data = fetch_stock_data(symbol)
    if data is not None:
        trend = calculate_trend(data)
        predicted_prices = predict_future_prices(data)
    else:
        trend = []
        predicted_prices = []
    return {'symbol': symbol, 'trend': trend, 'predictions': predicted_prices}

# Calculate trends using a moving average
def calculate_trend(prices, window_size=5):
    if prices.empty:  # Check if the DataFrame is empty
        return []
    closing_prices = prices['Close'].values
    trend = np.convolve(closing_prices, np.ones(window_size), 'valid') / window_size
    return trend.tolist()

# Endpoint to fetch trends and predictions
@app.route('/get_trends', methods=['POST'])
def get_trends():
    symbols = request.json.get('symbols', [])
    if not symbols:
        return jsonify({'error': 'No symbols provided'}), 400
    
    # Send tasks to Celery workers for parallel processing
    results = []
    for symbol in symbols:
        result = process_stock.apply_async(args=[symbol])
        results.append(result)

    # Gather results once all tasks are finished
    final_results = []
    for result in results:
        final_results.append(result.get())

    return jsonify({'results': final_results, 'status': 'success', 'message': 'Trends and predictions calculated successfully'})

# Main entry point to run the Flask app
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
