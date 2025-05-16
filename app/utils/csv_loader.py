import pandas as pd
import os

def load_csv(filepath: str):
    """Load a CSV file into a pandas DataFrame"""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Prospects file not found at: {filepath}")
            
    return pd.read_csv(filepath)