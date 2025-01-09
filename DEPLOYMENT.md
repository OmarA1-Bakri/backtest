# Deployment Plan

This document outlines the steps for deploying the BACKTEST application.

## Environment Setup

1.  **Python Environment:**
    *   Ensure you have Python 3.8 or higher installed.
    *   Create a virtual environment:

        ```bash
        python -m venv venv
        ```
    *   Activate the virtual environment:

        ```bash
        # On Windows
        venv\Scripts\activate
        # On macOS and Linux
        source venv/bin/activate
        ```
    *   Install dependencies:

        ```bash
        pip install -r requirements.txt
        ```
2.  **Node.js Environment:**
    *   Ensure you have Node.js and npm installed.
    *   Navigate to the `Frontend` directory:

        ```bash
        cd Frontend
        ```
    *   Install dependencies:

        ```bash
        npm install
        ```

## Deployment Steps

1.  **Build the Frontend:**
    *   Navigate to the `Frontend` directory:

        ```bash
        cd Frontend
        ```
    *   Build the frontend application:

        ```bash
        npm run build
        ```
    *   Copy the contents of the `Frontend/dist` directory to a suitable location for serving static files.
2.  **Run the Backend:**
    *   Navigate to the project root directory:

        ```bash
        cd ..
        ```
    *   Set environment variables in a `.env` file (e.g., `DATA_FILE`, `INITIAL_CASH`, `COMMISSION`, `SLIPPAGE`, `LOG_LEVEL`, `MODEL_DIR`).
    *   Run the backend application:

        ```bash
        python main.py --data_file <path_to_data_file> --initial_cash <initial_cash>
        ```
        Replace `<path_to_data_file>` with the path to your CSV data file and `<initial_cash>` with the initial capital for the backtest.
3.  **Serve the Frontend:**
    *   Configure a web server (e.g., Nginx, Apache) to serve the static files from the `Frontend/dist` directory.
    *   Ensure that the web server is configured to proxy requests to the backend API (e.g., `http://localhost:5000/api`).

## Monitoring

1.  **Logging:**
    *   The backend application logs to `backtest.log` file. Monitor this file for any errors or warnings.
2.  **Performance Metrics:**
    *   The backtesting results include performance metrics such as Sharpe Ratio, Sortino Ratio, Calmar Ratio, Max Drawdown, Win Rate, Profit Factor, and Expectancy. Monitor these metrics to evaluate the performance of the trading strategies.
3.  **System Monitoring:**
    *   Use system monitoring tools (e.g., htop, top) to monitor CPU, memory, and disk usage.
