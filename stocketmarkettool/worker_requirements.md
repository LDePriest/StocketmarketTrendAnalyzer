# Distributed Stock Analysis System Requirements

## 1. Overview

This system enables distributed processing of stock data using multiple machines within a network. By leveraging Flask for the web interface, Celery for task distribution, and Redis as the broker, this system processes stock data and generates predictions in parallel across machines, improving speed and scalability.

## 2. Functional Requirements

### 2.1 Web Interface

The system provides a simple web interface where users can input a list of stock symbols and request trend analysis and predictions.

**Input:** A list of stock symbols (e.g., ['AAPL', 'GOOG', 'MSFT'])

**Output:** The system returns the calculated trends (moving averages) and predicted future stock prices for each symbol.

**Endpoints:**
- `/`: Home page to serve the interface
- `/get_trends`: Accepts POST requests to process stock data. Requires a JSON body with a list of stock symbols

**Request Body:**
```json
{
  "symbols": ["AAPL", "GOOG", "MSFT"]
}
```

**Response:**
```json
{
  "results": [
    {
      "symbol": "AAPL",
      "trend": [1.23, 1.25, 1.30],
      "predictions": [1.31, 1.35, 1.40]
    },
    {
      "symbol": "GOOG",
      "trend": [2.34, 2.36, 2.40],
      "predictions": [2.45, 2.50, 2.55]
    }
  ],
  "status": "success",
  "message": "Trends and predictions calculated successfully"
}
```

### 2.2 Stock Data Fetching and Prediction

The system performs the following operations:
- Fetches stock data for the past year using Yahoo Finance (via the yfinance library)
- Calculates a moving average for the stock's closing prices
- Uses Linear Regression (via the scikit-learn library) to predict future prices for the next 5 days

### 2.3 Distributed Processing

**Task Distribution:**
The system distributes tasks across multiple machines using Celery. Each machine runs a Celery worker that processes tasks. The master machine running Flask sends tasks to Celery workers via Redis (acting as the broker).

**Concurrency:**
Each Celery worker can process tasks concurrently, utilizing multiple CPU cores of the worker machines.

## 3. Technical Requirements

### 3.1 Software Dependencies

Required software and libraries for both master and worker machines:

- Python 3.x (Recommended: Python 3.7+)
- Flask: For serving the web interface
- Celery: For distributed task processing
- Redis: For message brokering between the Flask app and Celery workers
- yfinance: For fetching stock data from Yahoo Finance
- scikit-learn: For performing linear regression and making predictions
- numpy: For handling numerical computations
- pandas: For handling stock data (optional, depending on how data is handled)

**Installation Command:**
```bash
pip install redis celery yfinance flask scikit-learn numpy pandas
```

### 3.2 Redis Setup

**Redis Server Installation:**
- Windows: Install Redis from the official website
- Linux: `sudo apt-get install redis-server`
- Mac: `brew install redis`

**Configuration:**
Redis must be accessible by all worker machines in the network. The master machine (running Flask) should point to the Redis server via `redis://localhost:6379/0`.

### 3.3 Celery Setup

**Starting a Celery Worker:**
```bash
celery -A app2.celery worker --loglevel=info
```

Workers can be distributed across multiple machines in the same network, with each machine contributing to task processing.

### 3.4 Flask Application Setup

**Configuration:**
- Exposes the `/get_trends` endpoint for user requests
- Runs on localhost or desired IP address on port 5000

**Starting Flask:**
```bash
python app2.py
```

## 4. System Architecture

### 4.1 Master Machine (Flask)
The Flask app (running app2.py) runs on the master machine, accepting HTTP requests and sending tasks to the Redis server.

### 4.2 Worker Machines (Celery)
Each worker machine runs a Celery worker that:
- Listens for tasks from the Redis server
- Fetches stock data
- Processes trends
- Makes predictions
- Returns results to the Flask app

### 4.3 Redis Server
Redis serves as the central message broker, enabling communication between the Flask app and Celery workers through a task queue system.

### 4.4 Data Flow
1. User sends a POST request to the `/get_trends` endpoint with stock symbols
2. Flask app sends tasks to the Redis server for each stock symbol
3. Celery worker(s) fetch stock data, process trends, and make predictions
4. Celery worker(s) return results to Flask
5. Flask app returns the processed results to the user

## 5. Hardware Requirements

### 5.1 Master Machine
- CPU: Any modern multi-core processor (e.g., Intel Core i5 or better)
- RAM: 8 GB or more
- Network: Connection to the Redis server

### 5.2 Worker Machines
- CPU: Any modern multi-core processor (e.g., Intel Core i5 or better)
- RAM: 8 GB or more per worker
- Network: Connection to the Redis server

### 5.3 Redis Server
- CPU: Multi-core server or cloud instance (2 CPU cores or more)
- RAM: At least 4 GB, depending on task volume
- Storage: Sufficient RAM for in-memory data storage

## 6. Performance Requirements

The system is designed to achieve:
- Horizontal scalability through additional worker machines
- Concurrent task processing based on available CPU cores

## 7. Security Considerations

- Redis Security: Implement authentication and ensure the instance is not publicly accessible without proper security measures
- Flask Security: Implement input validation and error handling to prevent malicious attacks

## 8. Testing and Quality Assurance

The testing strategy encompasses:
- Unit Tests: For individual functions, especially stock data fetching and prediction
- Integration Tests: For complete data flow verification
- Load Testing: To verify system performance under high traffic conditions

## 9. Deployment

The deployment process involves:
- Master Machine: Deploy Flask application on a user-accessible server
- Redis: Deploy on a dedicated server or cloud instance with appropriate security measures
- Worker Machines: Deploy Celery workers across multiple machines with Redis connectivity