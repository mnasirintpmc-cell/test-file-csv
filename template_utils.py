import pandas as pd
import numpy as np

def create_smart_template():
    """Create Excel-friendly template"""
    smart_template = {
        'TST_SpeedDem': ['SET_SPEED'],
        'TST_CellPresDemand': ['SET_PRESSURE'],
        'TST_InterPresDemand': ['SET_PRESSURE'],
        'TST_InterBPDemand_DE': ['SET_PRESSURE'],
        'TST_InterBPDemand_NDE': ['SET_PRESSURE'],
        'TST_GasInjectionDemand': ['SET_PRESSURE'],
        'TST_StepDuration': ['SET_DURATION'],
        'TST_APFlag': ['SET_FLAG'],
        'TST_TempDemand': ['SET_TEMPERATURE'],
        'TST_GasType': ['Air'],
        'TST_TestMode': ['SET_MODE'],
        'TST_MeasurementReq': ['SET_MEASURE'],
        'TST_TorqueCheck': [0]
    }
    return pd.DataFrame(smart_template)

def create_example_sequence():
    """Create example based on real test patterns"""
    example_sequence = {
        'TST_SpeedDem': [0, 0, 0, 3600, 3600, 0],
        'TST_CellPresDemand': [0.21, 1.0, 10.0, 5.0, 20.0, 0.5],
        'TST_InterPresDemand': [0, 0, 0, 0, 0, 0],
        'TST_InterBPDemand_DE': [0, 0, 0, 1.0, 0.4, 0],
        'TST_InterBPDemand_NDE': [0, 0, 0, 1.0, 0.4, 0],
        'TST_GasInjectionDemand': [0, 0, 0, 0, 0, 0],
        'TST_StepDuration': [2, 2, 2, 2, 10, 2],
        'TST_APFlag': [0, 0, 0, 0, 1, 0],
        'TST_TempDemand': [30, 30, 30, 155, 155, 155],
        'TST_GasType': ['Air', 'Air', 'Air', 'Air', 'Air', 'Air'],
        'TST_TestMode': [1, 1, 1, 1, 1, 1],
        'TST_MeasurementReq': [1, 1, 1, 1, 1, 1],
        'TST_TorqueCheck': [0, 0, 0, 0, 0, 0]
    }
    return pd.DataFrame(example_sequence)

def safe_read_csv(csv_file):
    """Safely read CSV files handling NaN/INF values"""
    # Handle both file paths and uploaded files
    if hasattr(csv_file, 'read'):
        # It's an uploaded file
        df = pd.read_csv(csv_file, delimiter=';')
    else:
        # It's a file path
        df = pd.read_csv(csv_file, delimiter=';')
    
    # FIX FOR NAN/INF ERROR
    df = df.fillna(0)  # Replace NaN with 0
    df = df.replace([np.inf, -np.inf], 0)  # Replace INF with 0
    
    return df
