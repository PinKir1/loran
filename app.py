import numpy as np
import dash
from dash import dcc, html, Input, Output, State
import plotly.graph_objects as go
import asyncio
import websockets
import json
import requests
import threading

app = dash.Dash(__name__)

STATION_X_COORDS = [0, 100000, 0]
STATION_Y_COORDS = [0, 0, 100000]
SPEED_OF_LIGHT = 3e8 / 10e8 
INITIAL_POSITION = [50000, 50000]
DELTA = 1e-6

plot_figure = go.Figure()
plot_figure.add_trace(go.Scatter(
    x=STATION_X_COORDS,
    y=STATION_Y_COORDS,
    mode='markers',
    name='Stations',
    marker=dict(size=10, color='blue')
))
plot_figure.add_trace(go.Scatter(
    x=[None],
    y=[None],
    mode='markers',
    name='Estimated Receiver',
    marker=dict(size=10, color='red')
))

def compute_tdoa_error(params, x1, y1, x2, y2, x3, y3, delta_t12, delta_t13, speed_of_light):
    x, y = params
    distances = [np.sqrt((x - xi) ** 2 + (y - yi) ** 2) for xi, yi in zip([x1, x2, x3], [y1, y2, y3])]
    delta_t12_calc = (distances[0] - distances[1]) / speed_of_light
    delta_t13_calc = (distances[0] - distances[2]) / speed_of_light
    return [delta_t12_calc - delta_t12, delta_t13_calc - delta_t13]

def calculate_loss(params, error_func, args):
    return sum(err ** 2 for err in error_func(params, *args))

def custom_optimizer(error_func, initial_position, args, learning_rate=0.01, max_iterations=10000, tolerance=1e-12):
    x, y = initial_position
    prev_loss = float('inf')
    for _ in range(max_iterations):
        curr_loss = calculate_loss([x, y], error_func, args)
        if abs(prev_loss - curr_loss) < tolerance:
            break
        prev_loss = curr_loss
        grad_x = (calculate_loss([x + DELTA, y], error_func, args) - curr_loss) / DELTA
        grad_y = (calculate_loss([x, y + DELTA], error_func, args) - curr_loss) / DELTA
        x -= learning_rate * grad_x
        y -= learning_rate * grad_y
    return x, y

def fetch_config():
    return requests.get("http://localhost:4002/config").json()

def change_object_speed(new_speed):
    return requests.post("http://localhost:4002/config", json={"objectSpeed": new_speed}).json()

async def websocket_listener():
    uri = "ws://localhost:4002"
    received_times = {}
    try:
        async with websockets.connect(uri) as websocket:
            while True:
                data = await websocket.recv()
                json_data = json.loads(data)
                received_times[json_data['sourceId']] = json_data['receivedAt']
                if len(received_times) == 3:
                    try:
                        deltas = [(received_times[f"source{i+1}"] - received_times[f"source{j+1}"]) / 1000 * 10e8
                                  for i, j in [(0, 1), (0, 2)]]
                        x, y = custom_optimizer(
                            compute_tdoa_error, INITIAL_POSITION,
                            args=(STATION_X_COORDS[0], STATION_Y_COORDS[0],
                                  STATION_X_COORDS[1], STATION_Y_COORDS[1],
                                  STATION_X_COORDS[2], STATION_Y_COORDS[2],
                                  *deltas, SPEED_OF_LIGHT)
                        )
                        update_plot(x, y)
                        received_times.clear()
                    except Exception as e:
                        print(f"Error in TDOA calculation: {e}")
    except Exception as e:
        print(f"WebSocket error: {e}")

def update_plot(x, y):
    plot_figure.data[1].x = [x]
    plot_figure.data[1].y = [y]

@app.callback(Output('live-graph', 'figure'), Input('interval-component', 'n_intervals'))
def refresh_graph(_):
    return plot_figure

@app.callback(
    Output('speed-response', 'children'),
    Input('submit-speed', 'n_clicks'),
    State('speed-input', 'value')
)
def adjust_speed(n_clicks, speed):
    if not n_clicks or speed is None:
        return "Enter a speed value"
    try:
        response = change_object_speed(float(speed))
        return f"Object speed updated to: {response.get('objectSpeed', 'unknown')} km/h"
    except ValueError:
        return "Invalid speed value"

app.layout = html.Div(
    style={'fontFamily': 'Arial', 'padding': '20px', 'backgroundColor': '#f4f4f4'},
    children=[
        html.H1("TDOA Positioning", style={'textAlign': 'center', 'color': '#333'}),
        dcc.Graph(id='live-graph', animate=True, style={'height': '70vh'}),
        dcc.Interval(id='interval-component', interval=1000, n_intervals=0),
        html.Div(
            style={'display': 'flex', 'justifyContent': 'center', 'marginTop': '20px'},
            children=[
                dcc.Input(
                    id='speed-input',
                    type='number',
                    placeholder='Enter speed (km/h)',
                    style={'marginRight': '10px'}
                ),
                html.Button('Change Speed', id='submit-speed', style={'backgroundColor': '#0d1B1F', 'color': '#fff'})
            ]
        ),
        html.Div(id='speed-response', style={'textAlign': 'center', 'marginTop': '10px', 'color': '#333'})
    ]
)

def start_websocket_thread():
    asyncio.run(websocket_listener())

if __name__ == "__main__":
    print(f"Current configuration: {fetch_config()}")
    threading.Thread(target=start_websocket_thread, daemon=True).start()
    app.run_server(debug=True)
