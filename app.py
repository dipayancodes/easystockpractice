import yfinance as yf
from flask import Flask, render_template, request, redirect, url_for, session
import json, os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'secret_key'

DATA_FILE = 'users.json'

# Helper function to read/write JSON data
def load_users():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, 'r') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def save_users(users):
    with open(DATA_FILE, 'w') as f:
        json.dump(users, f, indent=4)

# Fetch real-time stock price using Yahoo Finance API
def get_stock_price(stock_symbol):
    try:
        stock = yf.Ticker(stock_symbol)
        stock_info = stock.history(period="1d")
        return stock_info['Close'].iloc[0]  # Latest closing price
    except Exception as e:
        print(f"Error fetching stock data: {e}")
        return None

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        users = load_users()

        if email in users:
            return "Email already exists."

        users[email] = {
            'password': generate_password_hash(password),
            'balance': 100000,  # Assign ₹1,00,000 virtual money
            'portfolio': {},
            'transactions': []
        }
        save_users(users)
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        users = load_users()

        if email in users and check_password_hash(users[email]['password'], password):
            session['user'] = email
            return redirect(url_for('dashboard'))
        return "Invalid credentials"
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))

    users = load_users()
    user = users[session['user']]

    # Handle stock search
    stock_symbol = None
    stock_price = None
    if request.method == 'POST' and 'search' in request.form:
        stock_symbol = request.form['symbol'].upper()
        stock_price = get_stock_price(stock_symbol)

    return render_template('dashboard.html', 
                           balance=user['balance'], 
                           portfolio=user['portfolio'],
                           transactions=user['transactions'],
                           stock_symbol=stock_symbol,
                           stock_price=stock_price)

@app.route('/buy', methods=['POST'])
def buy_stock():
    if 'user' not in session:
        return redirect(url_for('login'))

    users = load_users()
    user = users[session['user']]

    stock_symbol = request.form['symbol'].upper()
    shares = int(request.form['shares'])
    stop_loss = float(request.form['stop_loss'])
    stock_price = get_stock_price(stock_symbol)

    if not stock_price:
        return "Stock not found."

    total_price = shares * stock_price

    if user['balance'] < total_price:
        return "Insufficient balance."

    # Update user portfolio and balance
    if stock_symbol in user['portfolio']:
        user['portfolio'][stock_symbol]['shares'] += shares
    else:
        user['portfolio'][stock_symbol] = {'shares': shares, 'price': stock_price, 'stop_loss': stop_loss}
    
    user['balance'] -= total_price
    user['transactions'].append(f"Bought {shares} shares of {stock_symbol} at ₹{stock_price} each with stop-loss ₹{stop_loss}")

    save_users(users)
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(debug=True)

