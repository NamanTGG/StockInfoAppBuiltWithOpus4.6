from flask import Flask, jsonify, render_template, request
import yfinance as yf
from datetime import datetime, timedelta
import json

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/stock/<symbol>")
def get_stock(symbol):
    try:
        ticker = yf.Ticker(symbol.upper())
        info = ticker.info

        if not info or info.get("trailingPegRatio") is None and info.get("currentPrice") is None and info.get("regularMarketPrice") is None:
            # Try to get at least basic price data
            hist = ticker.history(period="5d")
            if hist.empty:
                return jsonify({"error": f"No data found for symbol '{symbol.upper()}'"}), 404

        # Current price info
        current_price = info.get("currentPrice") or info.get("regularMarketPrice") or info.get("navPrice")
        previous_close = info.get("previousClose") or info.get("regularMarketPreviousClose")

        if current_price and previous_close:
            change = current_price - previous_close
            change_percent = (change / previous_close) * 100
        else:
            change = None
            change_percent = None

        # Build response
        data = {
            "symbol": symbol.upper(),
            "name": info.get("longName") or info.get("shortName", symbol.upper()),
            "price": {
                "current": current_price,
                "previousClose": previous_close,
                "open": info.get("open") or info.get("regularMarketOpen"),
                "dayHigh": info.get("dayHigh") or info.get("regularMarketDayHigh"),
                "dayLow": info.get("dayLow") or info.get("regularMarketDayLow"),
                "change": round(change, 2) if change is not None else None,
                "changePercent": round(change_percent, 2) if change_percent is not None else None,
                "currency": info.get("currency", "USD"),
            },
            "volume": {
                "current": info.get("volume") or info.get("regularMarketVolume"),
                "average": info.get("averageVolume"),
                "average10Day": info.get("averageDailyVolume10Day"),
            },
            "marketCap": info.get("marketCap"),
            "company": {
                "sector": info.get("sector"),
                "industry": info.get("industry"),
                "website": info.get("website"),
                "description": info.get("longBusinessSummary"),
                "employees": info.get("fullTimeEmployees"),
                "country": info.get("country"),
                "city": info.get("city"),
                "state": info.get("state"),
            },
            "financials": {
                "peRatio": info.get("trailingPE"),
                "forwardPE": info.get("forwardPE"),
                "pegRatio": info.get("pegRatio"),
                "priceToBook": info.get("priceToBook"),
                "priceToSales": info.get("priceToSalesTrailing12Months"),
                "earningsPerShare": info.get("trailingEps"),
                "forwardEPS": info.get("forwardEps"),
                "bookValue": info.get("bookValue"),
                "revenue": info.get("totalRevenue"),
                "revenuePerShare": info.get("revenuePerShare"),
                "grossProfit": info.get("grossProfits"),
                "ebitda": info.get("ebitda"),
                "netIncome": info.get("netIncomeToCommon"),
                "profitMargin": info.get("profitMargins"),
                "operatingMargin": info.get("operatingMargins"),
                "grossMargin": info.get("grossMargins"),
                "returnOnEquity": info.get("returnOnEquity"),
                "returnOnAssets": info.get("returnOnAssets"),
                "debtToEquity": info.get("debtToEquity"),
                "currentRatio": info.get("currentRatio"),
                "quickRatio": info.get("quickRatio"),
                "freeCashflow": info.get("freeCashflow"),
                "operatingCashflow": info.get("operatingCashflow"),
            },
            "dividends": {
                "dividendRate": info.get("dividendRate"),
                "dividendYield": info.get("dividendYield"),
                "exDividendDate": info.get("exDividendDate"),
                "payoutRatio": info.get("payoutRatio"),
            },
            "targets": {
                "targetHigh": info.get("targetHighPrice"),
                "targetLow": info.get("targetLowPrice"),
                "targetMean": info.get("targetMeanPrice"),
                "targetMedian": info.get("targetMedianPrice"),
                "recommendation": info.get("recommendationKey"),
                "numberOfAnalysts": info.get("numberOfAnalystOpinions"),
            },
            "ranges": {
                "fiftyTwoWeekHigh": info.get("fiftyTwoWeekHigh"),
                "fiftyTwoWeekLow": info.get("fiftyTwoWeekLow"),
                "fiftyDayAverage": info.get("fiftyDayAverage"),
                "twoHundredDayAverage": info.get("twoHundredDayAverage"),
                "beta": info.get("beta"),
            },
        }

        return jsonify(data)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/stock/<symbol>/history")
def get_stock_history(symbol):
    try:
        period = request.args.get("period", "1mo")
        interval = request.args.get("interval", "1d")

        valid_periods = ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "max"]
        valid_intervals = ["1m", "5m", "15m", "30m", "1h", "1d", "1wk", "1mo"]

        if period not in valid_periods:
            period = "1mo"
        if interval not in valid_intervals:
            interval = "1d"

        # For intraday intervals, limit the period
        if interval in ["1m", "5m", "15m", "30m"]:
            if period not in ["1d", "5d"]:
                period = "5d"
        elif interval == "1h":
            if period in ["1y", "2y", "5y", "max"]:
                period = "6mo"

        ticker = yf.Ticker(symbol.upper())
        hist = ticker.history(period=period, interval=interval)

        if hist.empty:
            return jsonify({"error": f"No history data for '{symbol.upper()}'"}), 404

        history = []
        for date, row in hist.iterrows():
            timestamp = date.isoformat()
            history.append({
                "date": timestamp,
                "open": round(row["Open"], 2),
                "high": round(row["High"], 2),
                "low": round(row["Low"], 2),
                "close": round(row["Close"], 2),
                "volume": int(row["Volume"]),
            })

        return jsonify({
            "symbol": symbol.upper(),
            "period": period,
            "interval": interval,
            "history": history,
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5001)

