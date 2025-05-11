from flask import Flask, render_template
import requests
import pandas as pd

app = Flask(__name__) 

# Dhan API key (don't expose this publicly in production)
DHAN_API_KEY = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJkaGFuIiwicGFydG5lcklkIjoiIiwiZXhwIjoxNzQ5NTQ1MTg2LCJ0b2tlbkNvbnN1bWVyVHlwZSI6IlNFTEYiLCJ3ZWJob29rVXJsIjoiIiwiZGhhbkNsaWVudElkIjoiMTEwMjQ3OTcwNyJ9.xT1SoPLGfWdNlzPLWtD6l0DO3ZNcTPyUDHdbICmWbUijIgMaROG7rFmrE-XOrq_oumeOQqoTEai2ZZ8gWAosJQ"

# Stocks to analyze
STOCKS = ["NSE_EQ|RELIANCE", "NSE_EQ|INFY", "NSE_EQ|TCS", "NSE_EQ|HDFCBANK"]


def fetch_option_chain(symbol):
    url = f"https://api.dhan.co/option-chain?symbol={symbol}"
    headers = {
        "Content-Type": "application/json",
        "Access-Token": DHAN_API_KEY
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()  # Raise error for HTTP issues
    data = response.json()
    return data.get("data", [])


@app.route("/")
def index():
    ranking = []

    for symbol in STOCKS:
        try:
            option_data = fetch_option_chain(symbol)
            oi_changes = []
            for entry in option_data:
                ce_oi = entry.get("CE", {}).get("change_oi", 0)
                pe_oi = entry.get("PE", {}).get("change_oi", 0)
                total_oi_change = ce_oi + pe_oi
                oi_changes.append(total_oi_change)

            total_change = sum(oi_changes)
            ranking.append({"symbol": symbol.split("|")[1], "total_oi_change": total_change})
        except Exception as e:
            print(f"Error for {symbol}: {e}")

    ranked = sorted(ranking, key=lambda x: x["total_oi_change"], reverse=True)
    return render_template("index.html", ranked=ranked)


@app.route("/details/<stock>")
def stock_details(stock):
    full_symbol = f"NSE_EQ|{stock}"
    try:
        option_data = fetch_option_chain(full_symbol)
    except Exception as e:
        return f"Error fetching data for {stock}: {e}"

    strikes = []
    for entry in option_data:
        strike = entry.get("strike_price")
        ce_oi = entry.get("CE", {}).get("change_oi", 0)
        pe_oi = entry.get("PE", {}).get("change_oi", 0)
        strikes.append({
            "strike": strike,
            "ce_oi_change": ce_oi,
            "pe_oi_change": pe_oi,
            "total_oi_change": ce_oi + pe_oi
        })

    sorted_strikes = sorted(strikes, key=lambda x: x["total_oi_change"], reverse=True)
    return render_template("details.html", stock=stock, strikes=sorted_strikes)


if __name__ == "__main__":
    app.run(debug=True)

