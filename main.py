import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import json
import os

# File path for storing portfolio data
PORTFOLIO_FILE = 'portfolio.json'

# Function to fetch stock data
def fetch_stock_data(stock_symbol, period='1d', interval='1d'):
    try:
        stock = yf.Ticker(stock_symbol)
        data = stock.history(period=period, interval=interval)
        return data
    except Exception as e:
        st.error(f"Error fetching data for {stock_symbol}: {e}")
        return pd.DataFrame()  # Return an empty DataFrame

# Function to get the latest price of a stock
def get_latest_price(stock_symbol):
    data = fetch_stock_data(stock_symbol)
    if not data.empty:
        return data['Close'].iloc[-1]
    return None

# Function to load portfolio from file
def load_portfolio():
    if os.path.exists(PORTFOLIO_FILE):
        with open(PORTFOLIO_FILE, 'r') as file:
            return json.load(file)
    return []

# Function to save portfolio to file
def save_portfolio(portfolio):
    with open(PORTFOLIO_FILE, 'w') as file:
        json.dump(portfolio, file, indent=4)

# Function to calculate total invested amount and profit/loss
def calculate_totals(portfolio):
    total_invested = 0
    total_profit_loss = 0
    stock_totals = []

    for stock in set(item['Stock'] for item in portfolio):
        stock_entries = [entry for entry in portfolio if entry['Stock'] == stock]
        total_quantity = sum(entry['Quantity'] for entry in stock_entries)
        total_invested_stock = sum(entry['Buy Price'] * entry['Quantity'] for entry in stock_entries)
        latest_price = get_latest_price(stock)
        if latest_price is not None:
            total_current_value = total_quantity * latest_price
            profit_loss = total_current_value - total_invested_stock
        else:
            total_current_value = total_invested_stock
            profit_loss = 0
        
        stock_totals.append({
            'Stock': stock,
            'Quantity': total_quantity,
            'Total Invested': f"₹{total_invested_stock:.2f}",
            'Current Value': f"₹{total_current_value:.2f}",
            'Profit/Loss': f"₹{profit_loss:.2f}"
        })

        total_invested += total_invested_stock
        total_profit_loss += profit_loss

    return stock_totals, total_invested, total_profit_loss

# Main application
def main():
    st.title("Paper Trading App")

    # Initialize or load portfolio
    if 'portfolio' not in st.session_state:
        st.session_state.portfolio = load_portfolio()

    # Display initial portfolio
    if len(st.session_state.portfolio) > 0:
        st.subheader("Your Portfolio")
        stock_totals, total_invested, total_profit_loss = calculate_totals(st.session_state.portfolio)
        portfolio_df = pd.DataFrame(stock_totals)
        st.table(portfolio_df)
        st.markdown(f"**Total Invested:** ₹{total_invested:.2f}")
        st.markdown(f"**Total Profit/Loss:** ₹{total_profit_loss:.2f}")

    # Search bar for stock symbol
    stock_symbol = st.text_input("Enter stock symbol (e.g., INFY.NS):").upper()

    if stock_symbol:
        # Fetch stock data for the last 6 months
        stock_data = fetch_stock_data(stock_symbol, period='6mo', interval='1d')

        if not stock_data.empty:
            # Display latest price with custom styling
            latest_price = get_latest_price(stock_symbol)
            if latest_price is not None:
                st.markdown(
                    f"<h2 style='text-align: center; font-weight: bold; font-size: 36px;'>Latest Price of {stock_symbol}: ₹{latest_price:.2f}</h2>",
                    unsafe_allow_html=True
                )

            # Plot stock data (last 6 months)
            st.line_chart(stock_data['Close'])

            # Buy section
            st.subheader("Buy Stock")
            quantity_to_buy = st.number_input("Enter quantity to buy:", min_value=1, value=1, step=1)
            if st.button("Buy"):
                # Record purchase details
                st.session_state.portfolio.append({
                    'Stock': stock_symbol,
                    'Quantity': quantity_to_buy,
                    'Buy Price': latest_price,
                    'Buy Date': datetime.now().strftime("%Y-%m-%d")
                })
                save_portfolio(st.session_state.portfolio)  # Save after updating the portfolio
                st.success(f"Bought {quantity_to_buy} shares of {stock_symbol} at ₹{latest_price:.2f} each.")

            # Display portfolio after buying
            st.subheader("Your Portfolio")
            if len(st.session_state.portfolio) > 0:
                stock_totals, total_invested, total_profit_loss = calculate_totals(st.session_state.portfolio)
                portfolio_df = pd.DataFrame(stock_totals)
                st.table(portfolio_df)
                st.markdown(f"**Total Invested:** ₹{total_invested:.2f}")
                st.markdown(f"**Total Profit/Loss:** ₹{total_profit_loss:.2f}")

                # Sell section
                st.subheader("Sell Stock")
                stocks_to_sell = portfolio_df['Stock'].unique()
                stock_to_sell = st.selectbox("Select stock to sell:", stocks_to_sell)
                quantity_to_sell = st.number_input("Enter quantity to sell:", min_value=1, value=1, step=1)

                if st.button("Sell"):
                    # Fetch the latest price when selling
                    sell_price = get_latest_price(stock_to_sell)

                    if sell_price is not None:
                        # Process sale
                        for entry in st.session_state.portfolio:
                            if entry['Stock'] == stock_to_sell:
                                if entry['Quantity'] >= quantity_to_sell:
                                    # Calculate profit/loss
                                    buy_price = entry['Buy Price']
                                    profit_loss = (sell_price - buy_price) * quantity_to_sell
                                    entry['Quantity'] -= quantity_to_sell
                                    if entry['Quantity'] == 0:
                                        # Optionally, remove entry if quantity is zero
                                        # st.session_state.portfolio.remove(entry)
                                        pass
                                    save_portfolio(st.session_state.portfolio)  # Save after updating the portfolio
                                    st.success(f"Sold {quantity_to_sell} shares of {stock_to_sell} at ₹{sell_price:.2f} each. Profit/Loss: ₹{profit_loss:.2f}")
                                    break
                                else:
                                    st.error("Not enough quantity in the portfolio to sell.")
                                    break

                        # Refresh portfolio display
                        stock_totals, total_invested, total_profit_loss = calculate_totals(st.session_state.portfolio)
                        portfolio_df = pd.DataFrame(stock_totals)
                        st.table(portfolio_df)
                        st.markdown(f"**Total Invested:** ₹{total_invested:.2f}")
                        st.markdown(f"**Total Profit/Loss:** ₹{total_profit_loss:.2f}")
                    else:
                        st.error("Failed to fetch the latest price for selling.")

    # Clear Portfolio button
    if st.button("Clear Portfolio"):
        st.session_state.portfolio = []
        save_portfolio(st.session_state.portfolio)  # Save after clearing the portfolio
        st.success("Portfolio cleared.")
        # Clear portfolio display
        st.empty()

# Run the app
if __name__ == "__main__":
    main()