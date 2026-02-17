import json
import matplotlib.pyplot as plt
import os
from collections import defaultdict
from datetime import datetime

def parse_input_data(data):
    parsed_data = defaultdict(list)
    
    for key, values in data.items():
        for entry in values:
            entry_dict = json.loads(entry)
            for date, value in entry_dict.items():
                parsed_data[key].append((datetime.strptime(date, "%Y-%m-%d"), float(value)))
    
    return parsed_data

def plot_and_save_graphs(data):
    output_dir = "graphs"
    os.makedirs(output_dir, exist_ok=True)
    
    for key, values in data.items():
        values.sort()  # Sorting by date
        dates, readings = zip(*values)
        
        plt.figure(figsize=(8, 6))
        plt.scatter(readings, dates, color='blue', label=key)
        plt.plot(readings, dates, linestyle='--', color='red', alpha=0.6)
        
        plt.xlabel("Values", fontsize=12)
        plt.ylabel("Date", fontsize=12)
        plt.title(key, fontsize=14, fontweight='bold')
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.legend()
        
        output_path = os.path.join(output_dir, f"{key}.png")
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
    
    print(f"Graphs saved in {output_dir} folder.")

# Sample Input
data = {
    "Haemoglobin": ["{\"2024-08-29\": 12.6}", "{\"2024-04-15\": 14.6}", "{\"2023-11-10\": 12.5}", "{\"2024-05-18\": 10.8}"]
}

# parsed_data = parse_input_data(data)
# plot_and_save_graphs(parsed_data)