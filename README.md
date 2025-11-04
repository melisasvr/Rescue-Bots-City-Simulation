# 🚨 Rescue Bots City Simulation 🤖
- A Python-based simulation with a web-based visualization demonstrating a fleet of autonomous robots fighting a city-wide fire outbreak.

## ✨ Features
- Dynamic City Simulation 🏙️: Simulates a large city with buildings, water refill stations, and spreading fires.
- Diverse Robot Fleet 🚒: Features Scout, Standard, and Heavy robot types, each with unique speed, water capacity, and extinguishing rates.
- Priority-Based Assignment 🎯: Robots use a greedy algorithm to target the highest-priority fires first, factoring in fire intensity and proximity to other buildings.
- Fire Dynamics 🔥: Fires spread to nearby buildings and cause building destruction if not extinguished quickly.
- Web Visualization 🌐: An accompanying index.html file provides a real-time, visual representation of the simulation state.
- Detailed Statistics 📊: Tracks key metrics like time elapsed, fires extinguished, buildings destroyed, and robot performance.

## ⚙️ How It Works
- The simulation is built in Python (rescue_bots_sim.py) and is designed to be run from the command line, with the ability to export its final state to a JSON file for external analysis/visualization.

### 🤖 Robot Types and Stats

| Type | Speed (m/s) | Max Water (units) | Extinguish Rate (units/s) | Role |
| :--- | :--- | :--- | :--- | :--- |
| **Scout** | High (14-18) | Low (50) | Low (3) | Fast response, short-duration fighting |
| **Standard** | Medium (8-12) | Medium (120) | Medium (6) | Balanced all-rounder |
| **Heavy** | Low (5-8) | High (250) | High (10) | Slow, high-impact fire fighting |

### 🧭 Target Assignment Logic (assign_targets)
- The logic for assigning tasks to robots prioritizes:
- Refilling 💧: If a robot's water is below 20% of its max capacity, it immediately heads to the nearest water station.
- Fighting 🔥: If a robot has water, it selects a non-destroyed, active fire based on a combined score:
- Priority (Higher is better, weighted heavily).
- Distance (Shorter is better, used as a tie-breaker).

## 🚀 Getting Started
- Prerequisites
- Python 3.6+
- ### Running the Simulation (Python)
1. Save the provided code as `rescue_bots_sim.py`.
2. Simulate your terminal:
- `python rescue_bots_sim.py`
3. The console will output real-time statistics and final detailed stats upon completion.
4. A file named simulation_state.json will be generated with the final state of the city and robots

- ### Running the Visualization (Web)
1. Ensure you have the `index.html` file.
2. The visualization currently has its own self-contained simulation logic in JavaScript for real-time interactivity (see the <script> block in index.html).
3. Open `index.html` in any modern web browser to view and control the city simulation visually.

## 📝 Code Structure Overview
- Data Classes: `Building`, `Robot`, `Fire`, and `WaterStation` define the state of all entities.
- `RobotType(Enum)`: Defines the three robot classes.
- `RescueBotsSimulation.__init__:` Initializes the city layout, water stations, buildings, and robot fleet distribution.
- `_start_fire` / `_calculate_fire_priority`: Implements the fire initiation and prioritization logic.
- `assign_targets`: Contains the core priority-based greedy task assignment logic.
- `update_robots` / `update_fires`: Handles movement, extinguishing, fire growth, spreading, and building destruction.
- `step / get_stats`: Runs a single time step and gathers performance metrics.

## Contributing
- Feel free to fork, improve, or submit issues/PRs!

## License
- MIT License: free to use/modify with attribution.
- Created by [Melisa Sever]–November 2025.
