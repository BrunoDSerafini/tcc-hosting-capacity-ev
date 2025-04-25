import os
import pandas as pd
import numpy as np
import glob
from pathlib import Path
import math
import traceback

# Define the scenarios from the directory listing
scenarios = [
    'GD0-EV0', 'GD0-EV25', 'GD0-EV50', 'GD0-EV75', 'GD0-EV100',
    'GD25-EV0', 'GD25-EV25', 'GD25-EV50', 'GD25-EV75', 'GD25-EV100',
    'GD50-EV0', 'GD50-EV25', 'GD50-EV50', 'GD50-EV75', 'GD50-EV100',
    'GD75-EV0', 'GD75-EV25', 'GD75-EV50', 'GD75-EV75', 'GD75-EV100',
    'GD100-EV0', 'GD100-EV25', 'GD100-EV50', 'GD100-EV75', 'GD100-EV100'
]

# Define transformers to analyze with their rated power (kVA)
transformers = {
    '90199814': 75,
    '86683110': 112.5,
    '34569437': 112.5,
    '34611212': 112.5,
    '34622044': 75,
    '34623374': 112.5,
    '34629647': 112.5,
    '34631299': 75,
    '34633937': 75,
    '34685435': 75,
    '34693896': 112.5,
    '34705676': 45,
    '34784390': 75,
    '101428666': 75,
    '91402190': 112.5
}

# Create the main output directory
output_dir = r"C:\DSSResumo\RESUMOFINAL"
os.makedirs(output_dir, exist_ok=True)

# Parameters for p.u. calculations
BASE_VOLTAGE = 127.0  # V
TRIFASICO_FATOR = math.sqrt(3)
POWER_FACTOR = 0.92   # Typical power factor

def calculate_nominal_current(power_kva):
    """Calculate nominal current for a transformer with given rated power."""
    # For a three-phase transformer at 220/127V
    # I = S / (√3 × V × PF) where S is in VA and V is in V
    power_va = power_kva * 1000
    current = power_va / (TRIFASICO_FATOR * BASE_VOLTAGE * POWER_FACTOR)
    return current

def get_subfolder_name(scenario, rs):
    """Generate the correct subfolder name with the appropriate number of hyphens."""
    scenario_parts = scenario.split('-')
    if len(scenario_parts) == 2:
        # Format like GD25-EV75
        gd_part, ev_part = scenario_parts
        return f"{gd_part}--{ev_part}--RS{rs}"
    else:
        # Special case or different format
        return f"{scenario}--RS{rs}"

def process_file(voltage_file, transformer_id, data_storage):
    """Process a single transformer voltage file and store the results."""
    if not os.path.exists(voltage_file):
        return False
    
    # Read the file
    try:
        with open(voltage_file, 'r') as f:
            lines = f.readlines()
        
        if len(lines) <= 1:
            return False
        
        # Process each line (skip header - line 1)
        for i, line in enumerate(lines[1:], 0):  # i will go from 0 to 95
            if i >= 96:  # Ensure we don't exceed our array bounds
                break
                
            try:
                # Split the line into columns
                parts = line.strip().split(',')
                if len(parts) < 11:  # Need at least hour, V1, and I1
                    continue
                
                # Always use the line index as the interval (ignoring the 'hour' column value)
                interval = i  # i is already the correct 0-based index for the 96 intervals
                
                # Ensure we have space in our data structure
                while interval >= len(data_storage[transformer_id]['voltage']):
                    data_storage[transformer_id]['voltage'].append([])
                    data_storage[transformer_id]['current'].append([])
                
                # Extract V1 (column 2) and I1 (column 10)
                try:
                    v1 = float(parts[2])
                    data_storage[transformer_id]['voltage'][interval].append(v1)
                except:
                    pass
                
                try:
                    i1 = float(parts[10])
                    data_storage[transformer_id]['current'][interval].append(i1)
                except:
                    pass
                
            except Exception as e:
                print(f"  Error processing line in {voltage_file}: {str(e)}")
        
        # Report successful processing
        valid_v = sum(1 for intervals in data_storage[transformer_id]['voltage'] if intervals)
        valid_i = sum(1 for intervals in data_storage[transformer_id]['current'] if intervals)
        print(f"  Processed {voltage_file}: found {valid_v} voltage intervals and {valid_i} current intervals")
        return True
    
    except Exception as e:
        print(f"  Error reading {voltage_file}: {str(e)}")
        return False

def analyze_scenario(scenario):
    """Analyze a specific scenario and create summary files for transformers."""
    print(f"Analyzing transformers for scenario: {scenario}")
    
    # Create output directory for this scenario
    scenario_output_dir = os.path.join(output_dir, scenario)
    os.makedirs(scenario_output_dir, exist_ok=True)
    
    # Initialize data storage
    data_storage = {}
    for transformer_id in transformers:
        data_storage[transformer_id] = {
            'voltage': [[] for _ in range(96)],
            'current': [[] for _ in range(96)]
        }
    
    # Process each random seed (1 to 51)
    processed_files = 0
    for rs in range(1, 52):
        subfolder = get_subfolder_name(scenario, rs)
        input_path = f"C:\\DSSFiles3\\{subfolder}\\DSS"
        
        # Skip if directory doesn't exist
        if not os.path.exists(input_path):
            continue
        
        # Process each transformer
        for transformer_id in transformers:
            voltage_file = os.path.join(input_path, f"MyCircuit_Mon_{transformer_id}_voltage_1.csv")
            if process_file(voltage_file, transformer_id, data_storage):
                processed_files += 1
    
    print(f"  Processed {processed_files} files for scenario {scenario}")
    
    # Create output directory for transformer data
    transformer_dir = os.path.join(scenario_output_dir, "transformers")
    os.makedirs(transformer_dir, exist_ok=True)
    
    # Generate summary files for each transformer
    for transformer_id in transformers:
        # Create data for summary
        summary_data = {
            'Hour': list(range(96)),
            'V1_Min': [],
            'V1_Avg': [],
            'V1_Max': [],
            'I1_Min': [],
            'I1_Avg': [],
            'I1_Max': []
        }
        
        # Calculate statistics for each interval
        for interval in range(96):
            v_values = data_storage[transformer_id]['voltage'][interval] if interval < len(data_storage[transformer_id]['voltage']) else []
            i_values = data_storage[transformer_id]['current'][interval] if interval < len(data_storage[transformer_id]['current']) else []
            
            # Voltage statistics
            if v_values:
                summary_data['V1_Min'].append(min(v_values))
                summary_data['V1_Avg'].append(sum(v_values) / len(v_values))
                summary_data['V1_Max'].append(max(v_values))
            else:
                summary_data['V1_Min'].append(None)
                summary_data['V1_Avg'].append(None)
                summary_data['V1_Max'].append(None)
            
            # Current statistics
            if i_values:
                summary_data['I1_Min'].append(min(i_values))
                summary_data['I1_Avg'].append(sum(i_values) / len(i_values))
                summary_data['I1_Max'].append(max(i_values))
            else:
                summary_data['I1_Min'].append(None)
                summary_data['I1_Avg'].append(None)
                summary_data['I1_Max'].append(None)
        
        # Create DataFrame and save to CSV
        df_summary = pd.DataFrame(summary_data)
        csv_file = os.path.join(transformer_dir, f"{transformer_id}.csv")
        df_summary.to_csv(csv_file, index=False)
        print(f"  Saved summary for transformer {transformer_id}")
    
    # Create a combined hourly summary for all transformers
    create_hourly_summary(scenario, data_storage)
    
    # Create a PU summary
    create_pu_summary(scenario, data_storage)

def create_hourly_summary(scenario, data_storage):
    """Create an hourly summary with all transformers in columns, including min/avg/max values."""
    print(f"  Creating hourly summary for scenario {scenario}")
    
    # Initialize the summary data structure
    hourly_summary = {'Hour': list(range(96))}
    
    # Add columns for each transformer
    for transformer_id in transformers:
        # Voltage columns with min/avg/max
        hourly_summary[f"{transformer_id}_V1_Min"] = []
        hourly_summary[f"{transformer_id}_V1_Avg"] = []
        hourly_summary[f"{transformer_id}_V1_Max"] = []
        
        # Current columns with min/avg/max
        hourly_summary[f"{transformer_id}_I1_Min"] = []
        hourly_summary[f"{transformer_id}_I1_Avg"] = []
        hourly_summary[f"{transformer_id}_I1_Max"] = []
        
        # Calculate statistics for each hour
        for interval in range(96):
            v_values = data_storage[transformer_id]['voltage'][interval] if interval < len(data_storage[transformer_id]['voltage']) else []
            i_values = data_storage[transformer_id]['current'][interval] if interval < len(data_storage[transformer_id]['current']) else []
            
            # Voltage statistics
            if v_values:
                hourly_summary[f"{transformer_id}_V1_Min"].append(min(v_values))
                hourly_summary[f"{transformer_id}_V1_Avg"].append(sum(v_values) / len(v_values))
                hourly_summary[f"{transformer_id}_V1_Max"].append(max(v_values))
            else:
                hourly_summary[f"{transformer_id}_V1_Min"].append(None)
                hourly_summary[f"{transformer_id}_V1_Avg"].append(None)
                hourly_summary[f"{transformer_id}_V1_Max"].append(None)
            
            # Current statistics
            if i_values:
                hourly_summary[f"{transformer_id}_I1_Min"].append(min(i_values))
                hourly_summary[f"{transformer_id}_I1_Avg"].append(sum(i_values) / len(i_values))
                hourly_summary[f"{transformer_id}_I1_Max"].append(max(i_values))
            else:
                hourly_summary[f"{transformer_id}_I1_Min"].append(None)
                hourly_summary[f"{transformer_id}_I1_Avg"].append(None)
                hourly_summary[f"{transformer_id}_I1_Max"].append(None)
    
    # Create and save hourly summary
    hourly_file = os.path.join(output_dir, f"{scenario}_hourly_summary.csv")
    pd.DataFrame(hourly_summary).to_csv(hourly_file, index=False)
    print(f"  Hourly summary saved to: {hourly_file}")

def create_pu_summary(scenario, data_storage):
    """Create a summary with transformer data in PU values for each hour, including min/avg/max values."""
    print(f"  Creating PU summary for scenario {scenario}")
    
    # Initialize the summary data
    pu_summary = {'Hour': list(range(96))}
    
    # Add columns for each transformer in PU
    for transformer_id, power_kva in transformers.items():
        # Calculate nominal current
        nominal_current = calculate_nominal_current(power_kva)
        
        # Add columns for voltage PU with min/avg/max
        pu_summary[f"{transformer_id}_V_PU_Min"] = []
        pu_summary[f"{transformer_id}_V_PU_Avg"] = []
        pu_summary[f"{transformer_id}_V_PU_Max"] = []
        
        # Add columns for current PU with min/avg/max
        pu_summary[f"{transformer_id}_I_PU_Min"] = []
        pu_summary[f"{transformer_id}_I_PU_Avg"] = []
        pu_summary[f"{transformer_id}_I_PU_Max"] = []
        
        # Calculate PU values for each hour
        for interval in range(96):
            v_values = data_storage[transformer_id]['voltage'][interval] if interval < len(data_storage[transformer_id]['voltage']) else []
            i_values = data_storage[transformer_id]['current'][interval] if interval < len(data_storage[transformer_id]['current']) else []
            
            # Voltage PU statistics
            if v_values:
                v_min = min(v_values) / BASE_VOLTAGE
                v_avg = (sum(v_values) / len(v_values)) / BASE_VOLTAGE
                v_max = max(v_values) / BASE_VOLTAGE
                
                pu_summary[f"{transformer_id}_V_PU_Min"].append(v_min)
                pu_summary[f"{transformer_id}_V_PU_Avg"].append(v_avg)
                pu_summary[f"{transformer_id}_V_PU_Max"].append(v_max)
            else:
                pu_summary[f"{transformer_id}_V_PU_Min"].append(None)
                pu_summary[f"{transformer_id}_V_PU_Avg"].append(None)
                pu_summary[f"{transformer_id}_V_PU_Max"].append(None)
            
            # Current PU statistics
            if i_values:
                i_min = min(i_values) / nominal_current
                i_avg = (sum(i_values) / len(i_values)) / nominal_current
                i_max = max(i_values) / nominal_current
                
                pu_summary[f"{transformer_id}_I_PU_Min"].append(i_min)
                pu_summary[f"{transformer_id}_I_PU_Avg"].append(i_avg)
                pu_summary[f"{transformer_id}_I_PU_Max"].append(i_max)
            else:
                pu_summary[f"{transformer_id}_I_PU_Min"].append(None)
                pu_summary[f"{transformer_id}_I_PU_Avg"].append(None)
                pu_summary[f"{transformer_id}_I_PU_Max"].append(None)
    
    # Create and save PU summary
    pu_file = os.path.join(output_dir, f"{scenario}_pu_summary.csv")
    pd.DataFrame(pu_summary).to_csv(pu_file, index=False)
    print(f"  PU summary saved to: {pu_file}")

def main():
    # Create main output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Process each scenario
    for scenario in scenarios:
        try:
            # Create scenario directory
            scenario_dir = os.path.join(output_dir, scenario)
            os.makedirs(scenario_dir, exist_ok=True)
            
            # Analyze transformer data
            analyze_scenario(scenario)
            
        except Exception as e:
            print(f"Error processing scenario {scenario}: {str(e)}")
            traceback.print_exc()
    
    print("Analysis complete. Results saved to:", output_dir)

if __name__ == "__main__":
    main()