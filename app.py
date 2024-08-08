import os
import time
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from flask import Flask, jsonify, render_template
from io import BytesIO
import base64
from threading import Thread
from datetime import datetime, timedelta

app = Flask(__name__)

TICKER = 'GOOG'
MA1 = 10
MA2 = 21

price_image = ""
oscillator_image = ""
cumulative_profit = 0.0

rsi_cumulative_profit = 0.0
rsi_image = ""
rsi_price_image = ""

start_date = datetime(2024, 1, 1)

def macd(signals, ma1, ma2):
    signals['ma1'] = signals['Close'].rolling(window=ma1, min_periods=1, center=False).mean()
    signals['ma2'] = signals['Close'].rolling(window=ma2, min_periods=1, center=False).mean()
    return signals

def smma(series, n):
    if len(series) == 0:
        raise ValueError("The input series is empty")
    output = [series[0]]
    for i in range(1, len(series)):
        temp = output[-1] * (n - 1) + series[i]
        output.append(temp / n)
    return output

def rsi(data, n=14):
    delta = data.diff().dropna()
    up = np.where(delta > 0, delta, 0)
    down = np.where(delta < 0, -delta, 0)
    rs = np.divide(smma(up, n), smma(down, n))
    output = 100 - 100 / (1 + rs)
    return output[n-1:]

def signal_generation(df, ma1, ma2):
    global cumulative_profit
    signals = macd(df, ma1, ma2)
    signals['positions'] = 0
    signals['positions'][ma1:] = np.where(signals['ma1'][ma1:] >= signals['ma2'][ma1:], 1, 0)
    signals['signals'] = signals['positions'].diff()
    signals['oscillator'] = signals['ma1'] - signals['ma2']
    signals['profit'] = 0.0
    buy_price = 0.0
    for i in range(1, len(signals)):
        if signals['signals'].iloc[i] == 1:
            buy_price = signals['Close'].iloc[i]
        elif signals['signals'].iloc[i] == -1 and buy_price != 0.0:
            sell_price = signals['Close'].iloc[i]
            signals['profit'].iloc[i] = sell_price - buy_price
            buy_price = 0.0
    signals['cumulative_profit'] = signals['profit'].cumsum()
    cumulative_profit = signals['cumulative_profit'].iloc[-1]
    return signals

def rsi_signal_generation(df, method, n=14):
    global rsi_cumulative_profit
    if 'Close' not in df or len(df['Close']) == 0:
        raise ValueError("The dataframe does not have a valid 'Close' column or it is empty")
    df['rsi'] = 0.0
    df['rsi'][n:] = method(df['Close'], n=14)
    df['positions'] = np.select([df['rsi'] < 30, df['rsi'] > 70], [1, -1], default=0)
    df['signals'] = df['positions'].diff()
    df['profit'] = 0.0
    buy_price = 0.0
    for i in range(1, len(df)):
        if df['signals'].iloc[i] == 1:
            buy_price = df['Close'].iloc[i]
        elif df['signals'].iloc[i] == -1 and buy_price != 0.0:
            sell_price = df['Close'].iloc[i]
            df['profit'].iloc[i] = sell_price - buy_price
            buy_price = 0.0
    df['cumulative_profit'] = df['profit'].cumsum()
    rsi_cumulative_profit = df['cumulative_profit'].iloc[-1]
    return df

def fetch_and_generate_chart():
    global price_image, oscillator_image
    while True:
        try:
            end_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            df = yf.download(TICKER, start=start_date, end=end_date)
            signals = signal_generation(df, MA1, MA2)
            
            # Generate the price image
            fig, ax = plt.subplots()
            df['Close'].plot(label=TICKER, ax=ax)
            ax.plot(signals.loc[signals['signals'] == 1].index, signals['Close'][signals['signals'] == 1], '^', markersize=10, color='g', lw=0, label='LONG')
            ax.plot(signals.loc[signals['signals'] == -1].index, signals['Close'][signals['signals'] == -1], 'v', markersize=10, color='r', lw=0, label='SHORT')
            plt.legend(loc='best')
            plt.grid(True)
            plt.title('Positions')
            figfile = BytesIO()
            plt.savefig(figfile, format='png')
            figfile.seek(0)
            price_image = base64.b64encode(figfile.getvalue()).decode()
            plt.close(fig)

            # Generate the oscillator image
            fig, (cx, bx) = plt.subplots(nrows=2, ncols=1)
            signals['oscillator'].plot(kind='bar', color='r', ax=cx)
            cx.legend(loc='best')
            cx.grid(True)
            cx.set_xticks([])
            cx.set_title('MACD Oscillator')

            signals['ma1'].plot(label='ma1', ax=bx)
            signals['ma2'].plot(label='ma2', linestyle=':', ax=bx)
            bx.legend(loc='best')
            bx.grid(True)
            figfile1 = BytesIO()
            plt.savefig(figfile1, format='png')
            figfile1.seek(0)
            oscillator_image = base64.b64encode(figfile1.getvalue()).decode()
            plt.close(fig)
        except Exception as e:
            print(f"Error fetching or generating MACD chart: {e}")

        # Fetch and update every 10 minutes
        time.sleep(600000)

def fetch_and_generate_rsi_chart():
    global rsi_price_image, rsi_image
    while True:
        try:
            end_date = datetime.today().strftime('%Y-%m-%d')
            df = yf.download(TICKER, start=start_date, end=end_date)
         
            new = rsi_signal_generation(df, rsi, n=14)
            # Generate and save the price image
            fig, ax = plt.subplots()
            new['Close'].plot(label=TICKER, ax=ax)
            ax.plot(new.loc[new['signals'] == 1].index, new['Close'][new['signals'] == 1], '^', markersize=10, color='g', lw=0, label='LONG')
            ax.plot(new.loc[new['signals'] == -1].index, new['Close'][new['signals'] == -1], 'v', markersize=10, color='r', lw=0, label='SHORT')
            plt.legend(loc='best')
            plt.grid(True)
            plt.title('Positions')
            figfile2 = BytesIO()
            plt.savefig(figfile2, format='png')
            figfile2.seek(0)
            rsi_price_image = base64.b64encode(figfile2.getvalue()).decode()
            plt.close(fig)
        
            # Plot and save the RSI image
            fig, bx = plt.subplots()
            new['rsi'][14:].plot(label='relative strength index', c='#522e75', ax=bx)
            bx.fill_between(new.index, 30, 70, alpha=0.5, color='#f22f08')
            bx.text(new.index[-45], 75, 'overbought', color='#594346', size=12.5)
            bx.text(new.index[-45], 25, 'oversold', color='#594346', size=12.5)
            plt.xlabel('Date')
            plt.ylabel('value')
            plt.title('RSI')
            plt.legend(loc='best')
            plt.grid(True)
            figfile3 = BytesIO()
            plt.savefig(figfile3, format='png')
            figfile3.seek(0)
            rsi_image = base64.b64encode(figfile3.getvalue()).decode()
            plt.close(fig)
        except Exception as e:
            print(f"Error fetching or generating RSI chart: {e}")

        # Fetch and update every 10 minutes
        time.sleep(600000)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/get_profit')
def get_profit():
    return jsonify({
        'cumulative_profit': cumulative_profit,
        'cumulative_rsi_profit': rsi_cumulative_profit
    })

@app.route('/get_price_image')
def get_price_image_route():
    return jsonify({'image': price_image})

@app.route('/get_oscillator_image')
def get_oscillator_image_route():
    return jsonify({'image': oscillator_image})

@app.route('/get_rsi_price_image')
def get_rsi_price_image_route():
    return jsonify({'image': rsi_price_image})

@app.route('/get_rsi_image')
def get_rsi_image_route():
    return jsonify({'image': rsi_image})

if __name__ == '__main__':
    Thread(target=fetch_and_generate_chart, daemon=True).start()
    Thread(target=fetch_and_generate_rsi_chart, daemon=True).start()
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
