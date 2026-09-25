"""Synthetic Lunar Data Generation Module.
Provides procedural lunar terrain, DEMs, crater populations, and multi-sensor simulators.
All generated data is explicitly tagged as SYNTHETIC / DEMO DATA.
"""
from .terrain_generator import SyntheticTerrainGenerator, SyntheticLunarLandscape
from .sensor_simulator import SensorSimulator, SimulatedObservation

__all__ = [
    "SyntheticTerrainGenerator",
    "SyntheticLunarLandscape",
    "SensorSimulator",
    "SimulatedObservation",
]
