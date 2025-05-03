import dash
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
from dash import dcc, html
import plotly.graph_objs as go
import plotly.express as px
import pandas as pd
import base64
import io

# Initialize the app with suppress_callback_exceptions=True
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY], suppress_callback_exceptions=True)
app.title = "Stock Dashboard"


# App layout
app.layout = html.Div([
    html.H1("Stock Analysis Dashboard", style={
        'textAlign': 'center', 'fontSize': '3rem', 'color': 'white',
        'marginTop': '20px', 'marginBottom': '20px', 'font-weight': 'bold'
    }),

    html.H4("Powered by: MHS Bytebits", style={
        'textAlign': 'center', 'color': 'white',
        'marginTop': '20px', 'marginBottom': '20px', 'font-weight': 'bold'
    }),

    dbc.Container([

        html.Br(),
        dcc.Upload(
            id='upload-data',
            children=html.Div([
                '📁 Drag and Drop or ',
                html.A('Select a CSV File')
            ]),
            style={
                'width': '100%',
                'height': '60px',
                'lineHeight': '60px',
                'borderWidth': '2px',
                'borderStyle': 'ridge',
                'borderRadius': '10px',
                'textAlign': 'center',
                'marginBottom': '30px',
                'color': 'white',
                'background-color': '#333',
            },
            multiple=False
        ),

        html.Div(id='output-dashboard')
    ], fluid=True)
])

def create_dashboard(df):
    # Data processing
    df.rename(columns={'Adj Close': 'Adj_Close'}, inplace=True)
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values('Date')
    df['Year'] = df['Date'].dt.year
    df['Month'] = df['Date'].dt.month
    df['Day'] = df['Date'].dt.day
    df["Volatility_30"] = df["Close"].rolling(window=30).std()
    df["Volatility_90"] = df["Close"].rolling(window=90).std()
    df["Daily Change (%)"] = df["Close"].pct_change() * 100

    layout = html.Div([
        dcc.Store(id='stored-data', data=df.to_dict('records')),
        dbc.Row([
            dbc.Col(
                dcc.DatePickerRange(
                    id="date-picker-range",
                    start_date=df['Date'].min(),
                    end_date=df['Date'].max(),
                    display_format='YYYY-MM-DD',
                    style={'width': '100%', 'fontWeight': 'bold'}
                ),
                width=6
            )
        ]),

        html.Br(),

        dbc.Row([
            dbc.Col([
                dbc.Card(dbc.CardBody([
                    html.H6("Open Price", className="card-title", style={"font-weight": "bold", "color": "#f8f9fa"}),
                    html.H1(f'{df["Open"].iloc[-1]:,.2f}', className="card-text", style={"font-size": "30px", "color": "#ffcc00"})
                ]), className="mb-4", style={"background-color": "black", "border-radius": "10px", "border": "2px solid white"}),

                dbc.Card(dbc.CardBody([
                    html.H6("Close Price", className="card-title", style={"font-weight": "bold", "color": "#f8f9fa"}),
                    html.H1(f'{df["Close"].iloc[-1]:,.2f}', className="card-text", style={"font-size": "30px", "color": "#28a745"})
                ]), className="mb-4", style={"background-color": "black", "border-radius": "10px", "border": "2px solid white"}),

                dbc.Card(dbc.CardBody([
                    html.H6("High Price", className="card-title", style={"font-weight": "bold", "color": "#f8f9fa"}),
                    html.H1(f'{df["High"].iloc[-1]:,.2f}', className="card-text", style={"font-size": "30px", "color": "#dc3545"})
                ]), className="mb-4", style={"background-color": "black", "border-radius": "10px", "border": "2px solid white"}),

                dbc.Card(dbc.CardBody([
                    html.H6("Low Price", className="card-title", style={"font-weight": "bold", "color": "#f8f9fa"}),
                    html.H1(f'{df["Low"].iloc[-1]:,.2f}', className="card-text", style={"font-size": "30px", "color": "#17a2b8"})
                ]), className="mb-4", style={"background-color": "black", "border-radius": "10px", "border": "2px solid white"}),
            ], width=3),

            dbc.Col(dcc.Graph(id='area-chart'), width=9),
        ]),

        html.Br(),

        dbc.Row([
            dbc.Col(dcc.Graph(id='price-graph'), width=6),
            dbc.Col(dcc.Graph(id='moving-avg-graph'), width=6),
        ]),

        html.Br(),

        dbc.Row([
            dbc.Col(dcc.Graph(id='candlestick-graph'), width=12),
        ]),

        html.Br(),

        dbc.Row([
            dbc.Col(dcc.Graph(id='volatility-graph'), width=12),
        ]),

        html.Br(),

        dbc.Row([
            dbc.Col(dcc.Graph(id='daily-change-graph'), width=12),
        ]),

        html.Br(),

        dbc.Row([
            dbc.Col(html.P("Developed by: Muhammad Hassan Saboor", className="text-center",
                           style={'font-size': '1.2rem', 'color': 'white'}), width=12)
        ])
    ])
    return layout


@app.callback(
    Output('output-dashboard', 'children'),
    [Input('upload-data', 'contents')],
    [State('upload-data', 'filename')]
)
def handle_file_upload(contents, filename):
    if contents is None:
        return html.Div(html.H5("Please upload a CSV file to get started!", style={"color": "white"}))

    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    try:
        df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
        return create_dashboard(df)
    except Exception as e:
        return html.Div(f"Error reading file: {str(e)}", style={'color': 'red'})


# ========== Callback Section for Interactive Charts ==========
def parse_df_from_store(data, start, end):
    df = pd.DataFrame(data)
    df['Date'] = pd.to_datetime(df['Date'])
    return df[(df['Date'] >= start) & (df['Date'] <= end)]

@app.callback(
    Output('area-chart', 'figure'),
    Input('date-picker-range', 'start_date'),
    Input('date-picker-range', 'end_date'),
    State('stored-data', 'data')
)
def update_area_chart(start, end, data):
    df = parse_df_from_store(data, start, end)
    fig = px.area(df, x='Date', y='Close', template='plotly_dark', color_discrete_sequence=['yellow'])
    fig.update_layout(title="Stock Price Overview", xaxis_title="Date", yaxis_title="Price (USD)")
    return fig

@app.callback(
    Output('price-graph', 'figure'),
    Input('date-picker-range', 'start_date'),
    Input('date-picker-range', 'end_date'),
    State('stored-data', 'data')
)
def update_price_graph(start, end, data):
    df = parse_df_from_store(data, start, end)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['Date'], y=df['Close'], mode='lines', name='Close', line=dict(color='green')))
    fig.add_trace(go.Scatter(x=df['Date'], y=df['Open'], mode='lines', name='Open', line=dict(color='blue')))
    fig.add_trace(go.Scatter(x=df['Date'], y=df['High'], mode='lines', name='High', line=dict(color='red')))
    fig.add_trace(go.Scatter(x=df['Date'], y=df['Low'], mode='lines', name='Low', line=dict(color='orange')))
    fig.update_layout(title="Stock Price Details", xaxis_title="Date", yaxis_title="Price", template='plotly_dark')
    return fig

@app.callback(
    Output('moving-avg-graph', 'figure'),
    Input('date-picker-range', 'start_date'),
    Input('date-picker-range', 'end_date'),
    State('stored-data', 'data')
)
def update_ma_chart(start, end, data):
    df = parse_df_from_store(data, start, end)
    df['50 MA'] = df['Close'].rolling(50).mean()
    df['100 MA'] = df['Close'].rolling(100).mean()
    df['200 MA'] = df['Close'].rolling(200).mean()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['Date'], y=df['50 MA'], name='50 MA', line=dict(color='blue')))
    fig.add_trace(go.Scatter(x=df['Date'], y=df['100 MA'], name='100 MA', line=dict(color='orange')))
    fig.add_trace(go.Scatter(x=df['Date'], y=df['200 MA'], name='200 MA', line=dict(color='red')))
    fig.update_layout(title="Moving Averages", xaxis_title="Date", yaxis_title="Price", template='plotly_dark')
    return fig

@app.callback(
    Output('candlestick-graph', 'figure'),
    Input('date-picker-range', 'start_date'),
    Input('date-picker-range', 'end_date'),
    State('stored-data', 'data')
)
def update_candle_chart(start, end, data):
    df = parse_df_from_store(data, start, end)
    fig = go.Figure(data=[go.Candlestick(x=df['Date'],
                                         open=df['Open'], high=df['High'],
                                         low=df['Low'], close=df['Close'],
                                         name="Candlestick")])
    fig.update_layout(title="Candlestick Chart", xaxis_title="Date", yaxis_title="Price", template='plotly_dark')
    return fig

@app.callback(
    Output('volatility-graph', 'figure'),
    Input('date-picker-range', 'start_date'),
    Input('date-picker-range', 'end_date'),
    State('stored-data', 'data')
)
def update_volatility_chart(start, end, data):
    df = parse_df_from_store(data, start, end)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['Date'], y=df['Volatility_30'], name='30-Day Volatility', line=dict(color='red')))
    fig.add_trace(go.Scatter(x=df['Date'], y=df['Volatility_90'], name='90-Day Volatility', line=dict(color='yellow')))
    fig.update_layout(title="Stock Price Volatility", xaxis_title="Date", yaxis_title="Volatility", template='plotly_dark')
    return fig

@app.callback(
    Output('daily-change-graph', 'figure'),
    Input('date-picker-range', 'start_date'),
    Input('date-picker-range', 'end_date'),
    State('stored-data', 'data')
)
def update_daily_change_chart(start, end, data):
    df = parse_df_from_store(data, start, end)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['Date'], y=df['Daily Change (%)'], mode='lines', name="Daily Change", line=dict(color='orange')))
    fig.update_layout(title="Daily Change (%)", xaxis_title="Date", yaxis_title="Change (%)", template='plotly_dark')
    return fig

if __name__ == '__main__':
    app.run_server(debug=True)
