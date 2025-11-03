import random
import math
import json
from dataclasses import dataclass, asdict
from typing import List, Tuple, Optional
from enum import Enum
import time

class RobotType(Enum):
    SCOUT = "scout"          # Fast but low water capacity
    STANDARD = "standard"    # Balanced
    HEAVY = "heavy"         # Slow but high water capacity

@dataclass
class Building:
    id: int
    x: float
    y: float
    on_fire: bool = False
    fire_intensity: float = 0.0
    fire_start_time: float = 0.0
    destroyed: bool = False
    
@dataclass
class Robot:
    id: int
    x: float
    y: float
    robot_type: RobotType = RobotType.STANDARD
    speed: float = 10.0
    target_building: Optional[int] = None
    target_station: Optional[int] = None
    extinguishing: bool = False
    water_capacity: float = 100.0
    max_water_capacity: float = 100.0
    extinguish_rate: float = 5.0
    fires_extinguished: int = 0
    distance_traveled: float = 0.0
    
@dataclass
class Fire:
    building_id: int
    intensity: float
    spread_rate: float
    priority: int = 1  # 1-5, higher is more urgent

@dataclass
class WaterStation:
    id: int
    x: float
    y: float
    refill_rate: float = 50.0  # water units per second

class RescueBotsSimulation:
    def __init__(self, city_size=200, num_robots=50, num_buildings=1000, 
                 num_fires=100, num_stations=5):
        self.city_size = city_size
        self.num_robots = num_robots
        self.num_buildings = num_buildings
        self.num_fires = num_fires
        self.num_stations = num_stations
        
        self.buildings: List[Building] = []
        self.robots: List[Robot] = []
        self.fires: List[Fire] = []
        self.water_stations: List[WaterStation] = []
        
        self.time = 0.0
        self.dt = 0.1  # time step in seconds
        
        # Statistics
        self.total_fires_started = 0
        self.total_fires_extinguished = 0
        self.total_buildings_destroyed = 0
        self.response_times: List[float] = []
        
        self._initialize_city()
        
    def _initialize_city(self):
        """Initialize all city components"""
        # Create buildings with random positions
        for i in range(self.num_buildings):
            self.buildings.append(Building(
                id=i,
                x=random.uniform(0, self.city_size),
                y=random.uniform(0, self.city_size)
            ))
        
        # Create water refill stations strategically placed
        grid_size = int(math.sqrt(self.num_stations))
        for i in range(self.num_stations):
            row = i // grid_size
            col = i % grid_size
            x = (col + 0.5) * (self.city_size / grid_size)
            y = (row + 0.5) * (self.city_size / grid_size)
            self.water_stations.append(WaterStation(
                id=i,
                x=x + random.uniform(-10, 10),
                y=y + random.uniform(-10, 10)
            ))
        
        # Create robots with different types
        robot_types_distribution = {
            RobotType.SCOUT: 0.2,    # 20% scouts
            RobotType.STANDARD: 0.5,  # 50% standard
            RobotType.HEAVY: 0.3      # 30% heavy
        }
        
        for i in range(self.num_robots):
            # Determine robot type
            rand = random.random()
            if rand < 0.2:
                robot_type = RobotType.SCOUT
                speed = random.uniform(14, 18)
                water = 50.0
                extinguish = 3.0
            elif rand < 0.7:
                robot_type = RobotType.STANDARD
                speed = random.uniform(8, 12)
                water = 120.0  # Increased from 100
                extinguish = 6.0  # Increased from 5.0
            else:
                robot_type = RobotType.HEAVY
                speed = random.uniform(5, 8)
                water = 250.0  # Increased from 200
                extinguish = 10.0  # Increased from 8.0
            
            self.robots.append(Robot(
                id=i,
                x=random.uniform(0, self.city_size),
                y=random.uniform(0, self.city_size),
                robot_type=robot_type,
                speed=speed,
                water_capacity=water,
                max_water_capacity=water,
                extinguish_rate=extinguish
            ))
        
        # Start fires in random buildings
        fire_buildings = random.sample(range(self.num_buildings), self.num_fires)
        for building_id in fire_buildings:
            self._start_fire(building_id)
        
        self.total_fires_started = self.num_fires
    
    def _start_fire(self, building_id: int):
        """Start a fire at a specific building"""
        intensity = random.uniform(50, 100)
        priority = self._calculate_fire_priority(building_id, intensity)
        
        self.buildings[building_id].on_fire = True
        self.buildings[building_id].fire_intensity = intensity
        self.buildings[building_id].fire_start_time = self.time
        
        self.fires.append(Fire(
            building_id=building_id,
            intensity=intensity,
            spread_rate=random.uniform(0.5, 2.0),
            priority=priority
        ))
    
    def _calculate_fire_priority(self, building_id: int, intensity: float) -> int:
        """Calculate fire priority based on intensity and nearby buildings"""
        building = self.buildings[building_id]
        
        # Count nearby buildings
        nearby_count = sum(1 for b in self.buildings 
                          if self.distance(building.x, building.y, b.x, b.y) < 15 
                          and not b.destroyed)
        
        # Priority based on intensity and density
        if intensity > 80 and nearby_count > 10:
            return 5  # Critical
        elif intensity > 60 or nearby_count > 7:
            return 4  # High
        elif intensity > 40 or nearby_count > 4:
            return 3  # Medium
        elif intensity > 20:
            return 2  # Low
        else:
            return 1  # Very low
    
    def distance(self, x1: float, y1: float, x2: float, y2: float) -> float:
        """Calculate Euclidean distance between two points"""
        return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
    
    def assign_targets(self):
        """Assign robots to fires or water stations using priority-based greedy algorithm"""
        # Get available robots (not currently assigned)
        available_robots = [r for r in self.robots 
                           if r.target_building is None and r.target_station is None]
        
        for robot in available_robots:
            # If low on water, go to nearest water station
            if robot.water_capacity < robot.max_water_capacity * 0.2:
                nearest_station = min(self.water_stations,
                                    key=lambda s: self.distance(robot.x, robot.y, s.x, s.y))
                robot.target_station = nearest_station.id
                continue
            
            # Otherwise, find highest priority fire that needs help
            if robot.water_capacity > 0:
                # FIXED: Only consider fires in buildings that are NOT destroyed
                fires_needing_help = [f for f in self.fires 
                                     if f.intensity > 0 
                                     and not self.buildings[f.building_id].destroyed
                                     and self.buildings[f.building_id].on_fire]
                
                if not fires_needing_help:
                    continue
                
                # Find best fire to target
                best_fire = min(fires_needing_help,
                              key=lambda f: (
                                  -f.priority * 100,  # Negative for descending priority
                                  self.distance(robot.x, robot.y,
                                              self.buildings[f.building_id].x,
                                              self.buildings[f.building_id].y)
                              ))
                
                robot.target_building = best_fire.building_id
    
    def update_robots(self):
        """Move robots towards their targets and perform actions"""
        for robot in self.robots:
            last_x, last_y = robot.x, robot.y
            
            # Handle water station targeting
            if robot.target_station is not None:
                station = self.water_stations[robot.target_station]
                dist = self.distance(robot.x, robot.y, station.x, station.y)
                
                if dist < 2.0:  # At the station
                    # Refill water
                    refill_amount = min(station.refill_rate * self.dt,
                                      robot.max_water_capacity - robot.water_capacity)
                    robot.water_capacity += refill_amount
                    
                    if robot.water_capacity >= robot.max_water_capacity * 0.95:
                        robot.target_station = None  # Fully refilled
                else:
                    # Move towards station
                    dx = station.x - robot.x
                    dy = station.y - robot.y
                    move_dist = min(robot.speed * self.dt, dist)
                    robot.x += (dx / dist) * move_dist
                    robot.y += (dy / dist) * move_dist
            
            # Handle fire targeting
            elif robot.target_building is not None:
                building = self.buildings[robot.target_building]
                
                if building.destroyed or not building.on_fire:
                    robot.target_building = None
                    continue
                
                dist = self.distance(robot.x, robot.y, building.x, building.y)
                
                if dist < 1.0:  # Robot reached the building
                    if building.on_fire and robot.water_capacity > 0:
                        # Extinguish fire
                        extinguish_amount = min(robot.extinguish_rate * self.dt,
                                              building.fire_intensity,
                                              robot.water_capacity)
                        building.fire_intensity -= extinguish_amount
                        robot.water_capacity -= extinguish_amount
                        
                        if building.fire_intensity <= 0:
                            # Fire extinguished!
                            building.on_fire = False
                            building.fire_intensity = 0
                            robot.fires_extinguished += 1
                            self.total_fires_extinguished += 1
                            
                            # Record response time
                            response_time = self.time - building.fire_start_time
                            self.response_times.append(response_time)
                            
                            # Remove fire from list
                            self.fires = [f for f in self.fires 
                                        if f.building_id != robot.target_building]
                            robot.target_building = None
                    else:
                        robot.target_building = None
                else:
                    # Move towards target
                    dx = building.x - robot.x
                    dy = building.y - robot.y
                    move_dist = min(robot.speed * self.dt, dist)
                    robot.x += (dx / dist) * move_dist
                    robot.y += (dy / dist) * move_dist
            
            # Track distance traveled
            robot.distance_traveled += self.distance(last_x, last_y, robot.x, robot.y)
    
    def update_fires(self):
        """Update fire intensity and handle fire spread"""
        new_fires = []
        
        for fire in self.fires:
            building = self.buildings[fire.building_id]
            
            if building.on_fire and not building.destroyed:
                # Fire grows (but slower now)
                building.fire_intensity += fire.spread_rate * self.dt * 0.7  # 30% slower growth
                building.fire_intensity = min(building.fire_intensity, 200)
                fire.intensity = building.fire_intensity
                
                # Building gets destroyed if fire is too intense for too long
                if building.fire_intensity > 180:  # Increased from 150
                    time_on_fire = self.time - building.fire_start_time
                    if time_on_fire > 45:  # Increased from 30 seconds
                        building.destroyed = True
                        building.on_fire = False
                        self.total_buildings_destroyed += 1
                        # Remove this fire
                        continue
                
                # Fire spread mechanics (very small chance each step)
                # Only spread if fire is very intense and not being fought
                robots_nearby = sum(1 for r in self.robots 
                                  if r.target_building == building.id)
                if robots_nearby == 0 and random.random() < 0.0001 * self.dt * building.fire_intensity:
                    self._try_spread_fire(building, new_fires)
        
        # Add new fires from spreading
        for building_id in new_fires:
            if not self.buildings[building_id].on_fire:
                self._start_fire(building_id)
                self.total_fires_started += 1
    
    def _try_spread_fire(self, source_building: Building, new_fires: List[int]):
        """Attempt to spread fire to nearby buildings"""
        spread_radius = 8.0  # meters (reduced from 10)
        
        # Only spread to max 1 building per fire
        potential_targets = []
        for building in self.buildings:
            if building.id != source_building.id and not building.on_fire and not building.destroyed:
                dist = self.distance(source_building.x, source_building.y,
                                   building.x, building.y)
                
                if dist < spread_radius:
                    potential_targets.append((building, dist))
        
        if potential_targets:
            # Pick closest building with low probability
            building, dist = min(potential_targets, key=lambda x: x[1])
            spread_prob = 0.15 * (1 - dist / spread_radius)  # Reduced from 0.3
            if random.random() < spread_prob:
                new_fires.append(building.id)
    
    def step(self):
        """Run one simulation step"""
        self.assign_targets()
        self.update_robots()
        self.update_fires()
        self.time += self.dt
    
    def get_stats(self):
        """Get current simulation statistics"""
        active_fires = len([f for f in self.fires if f.intensity > 0])
        robots_fighting = len([r for r in self.robots if r.target_building is not None])
        robots_refilling = len([r for r in self.robots if r.target_station is not None])
        robots_idle = len([r for r in self.robots 
                          if r.target_building is None and r.target_station is None])
        
        avg_water = sum(r.water_capacity for r in self.robots) / len(self.robots)
        total_fire_intensity = sum(f.intensity for f in self.fires)
        
        avg_response_time = (sum(self.response_times) / len(self.response_times) 
                           if self.response_times else 0)
        
        return {
            'time': round(self.time, 1),
            'active_fires': active_fires,
            'robots_fighting': robots_fighting,
            'robots_refilling': robots_refilling,
            'robots_idle': robots_idle,
            'total_fires_started': self.total_fires_started,
            'total_fires_extinguished': self.total_fires_extinguished,
            'buildings_destroyed': self.total_buildings_destroyed,
            'avg_water_capacity': round(avg_water, 1),
            'total_fire_intensity': round(total_fire_intensity, 1),
            'avg_response_time': round(avg_response_time, 1)
        }
    
    def export_state(self):
        """Export current state for visualization"""
        return {
            'time': self.time,
            'buildings': [asdict(b) for b in self.buildings],
            'robots': [{**asdict(r), 'robot_type': r.robot_type.value} for r in self.robots],
            'fires': [asdict(f) for f in self.fires],
            'water_stations': [asdict(s) for s in self.water_stations],
            'stats': self.get_stats()
        }
    
    def print_detailed_stats(self):
        """Print detailed statistics"""
        stats = self.get_stats()
        print("\n" + "="*70)
        print(f"{'SIMULATION STATISTICS':^70}")
        print("="*70)
        print(f"Time Elapsed: {stats['time']}s")
        print(f"\nFire Status:")
        print(f"  Active Fires: {stats['active_fires']}")
        print(f"  Total Started: {stats['total_fires_started']}")
        print(f"  Extinguished: {stats['total_fires_extinguished']}")
        print(f"  Buildings Destroyed: {stats['buildings_destroyed']}")
        print(f"  Total Fire Intensity: {stats['total_fire_intensity']}")
        print(f"\nRobot Status:")
        print(f"  Fighting Fires: {stats['robots_fighting']}")
        print(f"  Refilling Water: {stats['robots_refilling']}")
        print(f"  Idle: {stats['robots_idle']}")
        print(f"  Avg Water Capacity: {stats['avg_water_capacity']}%")
        print(f"\nPerformance:")
        print(f"  Avg Response Time: {stats['avg_response_time']}s")
        
        # Robot type breakdown
        scouts = sum(1 for r in self.robots if r.robot_type == RobotType.SCOUT)
        standard = sum(1 for r in self.robots if r.robot_type == RobotType.STANDARD)
        heavy = sum(1 for r in self.robots if r.robot_type == RobotType.HEAVY)
        print(f"\nRobot Fleet Composition:")
        print(f"  Scouts: {scouts} | Standard: {standard} | Heavy: {heavy}")
        print("="*70)

# Example usage
if __name__ == "__main__":
    print("🚨 RESCUE BOTS SIMULATION - ENHANCED VERSION 🚨\n")
    
    sim = RescueBotsSimulation(
        city_size=200,
        num_robots=50,
        num_buildings=1000,
        num_fires=100,
        num_stations=5
    )
    
    print(f"City: {sim.city_size}m × {sim.city_size}m")
    print(f"Robots: {sim.num_robots} | Buildings: {sim.num_buildings}")
    print(f"Initial Fires: {sim.num_fires} | Water Stations: {sim.num_stations}")
    print("-" * 70)
    
    start_time = time.time()
    
    # Run simulation
    max_iterations = 10000
    for i in range(max_iterations):
        sim.step()
        
        # Print stats every 10 seconds of simulation time
        if i % 100 == 0:
            stats = sim.get_stats()
            print(f"[{stats['time']:6.1f}s] Fires: {stats['active_fires']:3d} | "
                  f"Fighting: {stats['robots_fighting']:2d} | "
                  f"Refilling: {stats['robots_refilling']:2d} | "
                  f"Destroyed: {stats['buildings_destroyed']:2d}")
        
        # Stop if all fires are out
        if len(sim.fires) == 0:
            print("\n✅ SUCCESS! All fires extinguished!")
            break
        
        # Warning if too many buildings destroyed
        if sim.total_buildings_destroyed > 100:
            print("\n⚠️  WARNING: Significant building damage!")
            print("   Consider increasing robots or reducing fire spread!")
            break
    else:
        print("\n⏱️  Simulation time limit reached")
    
    # Print final detailed statistics
    sim.print_detailed_stats()
    
    # Calculate real-time performance
    real_time = time.time() - start_time
    print(f"\nSimulation completed in {real_time:.2f} real seconds")
    print(f"Simulation speed: {sim.time/real_time:.1f}x real-time")
    
    # Export final state
    with open('simulation_state.json', 'w') as f:
        json.dump(sim.export_state(), f, indent=2)
    print("\n📁 Simulation state exported to simulation_state.json")