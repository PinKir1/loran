### LORAN

Completed

---

## Project Overview

This application provides a visualization tool for an emulated LORAN (Long Range Navigation) system. By connecting to a WebSocket server, it processes signal arrival times at base stations, calculates the object's position using the Time Difference of Arrival (TDOA) method, and visualizes the results in real time.
![image](https://github.com/user-attachments/assets/859720c6-80fc-4035-91ee-7e4b43066b91)

---

## Features

- **Real-Time Data Integration**: Connects to a WebSocket server to receive LORAN data dynamically.
- **Position Estimation**: Implements multilateration using TDOA with optimization techniques such as Least Squares and Gradient Descent.
- **Interactive Visualization**: Displays the object's estimated position and base station locations on a 2D Cartesian graph.
- **User Configuration**: Provides an interface to adjust system parameters, like object speed, for flexible testing and experimentation.

---

## Usage

1. **Prepare the LORAN Emulation Service**:
   - Pull the LORAN emulation service Docker image:
     ```bash
     docker pull iperekrestov/university:loran-emulation-service
     ```
   - Start the LORAN emulation service:
     ```bash
     docker run --name loran-emulator -p 4002:4000 iperekrestov/university:loran-emulation-service
     ```

2. **Set Up the Visualization Tool**:
   - Clone the repository:
     ```bash
     git clone https://github.com/PinKir1/loran.git
     ```
   - Navigate to the project directory:
     ```bash
     cd loran
     ```
   - Install the required dependencies:
     ```bash
     pip install -r requirements.txt
     ```

3. **Launch the Application**:
   - Run the script:
     ```bash
     python app.py
     ```
