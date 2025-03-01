# DTA Sensitivity Analysis for Specific Links Change

This repository demonstrates how to perform a **Dynamic Traffic Assignment (DTA)** sensitivity analysis using **DTALite**. The primary goal is to see how changes to certain link attributes (e.g., lanes, free speed, capacity) affect network-wide performance metrics such as link travel times, OD travel times, and volumes.

---

## Overview

In a **Dynamic Traffic Assignment** model, traffic demand is assigned to paths in a time-dependent manner based on congestion and other network conditions. By modifying certain link attributes (like number of lanes or free speed) in one scenario and comparing it to a baseline, you can evaluate how these changes affect:

- **Link-level** metrics (travel times, volumes, etc.)
- **Origin-Destination (OD) level** metrics (travel times, volumes, congestion)

This codebase automates:

1. Running a **baseline** simulation (original link attributes).
2. **Modifying** link attributes in a copy of the network.
3. Running a **modified** simulation.
4. **Comparing** link and OD performance between baseline and modified scenarios.

---

## Dependencies

- **Python 3.7+**
- **pandas** for reading and writing CSV files
- **DTALite** for performing the traffic assignment

Install these via pip install pandas and ensure DTALite is correctly installed.

## Data Inputs

You will need the following input files for DTALite to run properly. Place them in each simulation folder (e.g., `Before/` and `After/`):

- **node.csv**
- **link.csv**
- **settings.csv**
- **demand.csv**
- **mode_type.csv** (only needed if you have multiple OD demand files)

These files must be present in the folder where the simulation is run.

## Data Outputs

When DTALite completes a simulation, it typically generates:

- **link_performance.csv** 
- **route_assignment.csv**
- **od_performance.csv**

This code focuses on comparing `link_performance.csv` and `od_performance.csv` in the `Before/` (baseline) and `After/` (modified) folders. Finally, it outputs a `link_performance_comparison.csv` and `od_performance_comparison.csv` in the current folder.

## Example Usage

1. **Prepare Baseline Folder (`Before/`):**
    - Ensure it contains `node.csv`, `link.csv`, `settings.csv`, `demand.csv`, and optionally `mode_type.csv`.

2. **Prepare Modified Folder (`After/`):**
    - Initially, it should have the same set of input files as the baseline folder so that DTALite can run.

3. **Define Modifications in Python:**

    ```python
    modifications = [
        {'from_node_id': 1, 'to_node_id': 4, 'lanes': 3, 'free_speed': 70},
        {'from_node_id': 3, 'to_node_id': 2, 'free_speed': 50, 'capacity': 1500}
    ]
    ```

4. **Run the Pipeline:**

    ```python
    # Path to your network file (e.g., 'link.csv')
    network_file = 'link.csv'
    # Define output folders for baseline and modified simulation results.
    baseline_folder = "Before"
    modified_folder = "After"
    
    # Run the sensitivity pipeline.
    link_diff, od_diff = sensitivity_pipeline(
        network_file, modifications, baseline_folder, modified_folder, key_columns=['from_node_id', 'to_node_id'], threshold=0
    )
    ```