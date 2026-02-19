import streamlit as st
import pandas as pd
import yfinance as yf
import requests
import datetime
import plotly.graph_objects as go
import base64

st.title('My S&P 500 Company Price Visualizer')

st.markdown("""
This app retrieves the list of the **S&P 500** (from Wikipedia) and its corresponding **stock closing price** (year-to-date)!

""")

# Web scraping of S&P 500 data
#
@st.cache_data
def load_data():
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(url, headers=headers)
    response.raise_for_status()  # will raise error if request fails

    html = pd.read_html(response.text, header=0)
    df = html[0]
    return df

df = load_data()
sector = df.groupby('Symbol')

st.header('Display All Companies')
st.dataframe(df)

st.write("#")


# Company selection
sorted_sector_unique = sorted( df['Symbol'].unique() )
selected_sector = st.selectbox('Search and select Company Symbol', sorted_sector_unique)

# Filtering data
df_selected_sector = df[ (df['Symbol']==(selected_sector)) ]

# Download S&P500 data
# https://discuss.streamlit.io/t/how-to-download-file-in-streamlit/1806
def filedownload(df):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()  # strings <-> bytes conversions
    href = f'<a href="data:file/csv;base64,{b64}" download="SP500.csv">Download CSV File</a>'
    return href

st.markdown(filedownload(df_selected_sector), unsafe_allow_html=True)

# https://pypi.org/project/yfinance/

data = yf.download(
        tickers = list(df_selected_sector.Symbol),
        period = "ytd",
        interval = "1d",
        group_by = 'ticker',
        auto_adjust = True,
        prepost = True,
        threads = True
    )
col1, col2 = st.columns(2)

with col1:
    # Default start date: 1 year ago
    default_start = datetime.date.today() - datetime.timedelta(days=365)
    start_date = st.date_input('Start Date', default_start)

with col2:
    # Default end date: Today
    end_date = st.date_input('End Date', datetime.date.today())


# 2. Refined Plotting Function with Date Parameters
import plotly.graph_objects as go

# ... [rest of your imports and data loading] ...
# ... [Keep your previous imports and data loading] ...

# 1. UI Control for Interactivity
st.sidebar.header("Chart Settings")
lock_chart = st.sidebar.toggle("Lock Chart (Disable Scaling/Moving)", value=True)

def price_plot(symbol, start, end, is_locked):
    stock = yf.Ticker(symbol)
    data = stock.history(start=start, end=end)

    if data.empty:
        st.warning(f"No market data available for {symbol}.")
        return

    data['20_Day_MA'] = data['Close'].rolling(window=20).mean()

    # Create the figure
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=data.index, y=data['Close'],
        mode='lines', name='Adjusted Close',
        line=dict(color='#1f77b4', width=2)
    ))

    fig.add_trace(go.Scatter(
        x=data.index, y=data['20_Day_MA'],
        mode='lines', name='20-Day MA',
        line=dict(color='#ff7f0e', width=1.5, dash='dash')
    ))

    # Configure Layout
    fig.update_layout(
        title=f"Market Analysis: {symbol}",
        template="plotly_white",
        hovermode="x unified",
        xaxis=dict(
            rangeslider=dict(visible=not is_locked), # Hide slider if locked
            fixedrange=is_locked # Disable zooming/panning on X axis
        ),
        yaxis=dict(
            fixedrange=is_locked # Disable zooming/panning on Y axis
        )
    )

    # 2. Apply Configuration to Disable the Toolbar
    # 'staticPlot': True removes all interactivity (hover, zoom, buttons)
    # 'displayModeBar': False removes the top menu bar
    config = {
        'staticPlot': is_locked,
        'displayModeBar': not is_locked
    }

    st.plotly_chart(fig, use_container_width=True, config=config)

# Execution
price_plot(selected_sector, start_date, end_date, lock_chart)