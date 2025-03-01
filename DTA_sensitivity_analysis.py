# ----------------------------------
# Author: Fang (Alicia) Tang
# Date: 2/26/2025
# Email: fangt@asu.edu
# ----------------------------------
#   - run traffic assignment
#   - sort_and_rewrite_GMNS_links(modifications, network_file, modified_folder)
#   - compare_link_performance(baseline_file, modified_file, key_columns=['from_node_id', 'to_node_id'])
#   - detect_affected_OD_pairs(baseline_file, modified_file, threshold)


import os
import pandas as pd
import DTALite as dta

def run_dtalite_simulation(output_folder: str) -> str:
    """
    Runs a DTALite simulation using input files from sim_folder and writes
    all output files back to sim_folder. DTALite reads/writes in the current
    working directory, so we temporarily switch to sim_folder.

    Args:
        sim_folder (str): Folder containing all DTALite input files and
                          where output files will be stored.

    Returns:
        str: The same folder path (for reference).
    """
    # Ensure the folder exists
    os.makedirs(output_folder, exist_ok=True)

    # Save the original working directory
    original_dir = os.getcwd()

    try:
        # Change to the simulation folder so DTALite can find inputs
        os.chdir(output_folder)

        print(f"Running DTALite simulation in: {output_folder}")
        # DTALite will read from node.csv, link.csv, etc. in sim_folder
        # and will write its output files there.
        dta.assignment()

    finally:
        # Change back to the original working directory
        os.chdir(original_dir)

    return output_folder


def sort_and_rewrite_GMNS_links(link_modifications, network_file, modified_folder):
    """
    Reads the link.csv file from the specified folder, updates specified attributes
    (e.g., lanes, free_speed, capacity) for a set of specified links, sorts the links
    sequentially by from_node_id and to_node_id, reassigns link IDs, and rewrites the
    sorted content back to the same file in that folder.

    Args:
        link_modifications (list of dict): A list where each dictionary represents a modification with keys:
            - from_node_id (int): The starting node ID of the link.
            - to_node_id (int): The ending node ID of the link.
            - Any additional key-value pairs (e.g., lanes, free_speed, capacity) to be updated.
        network_file (str): The name of the link file (default 'link.csv').
        folder (str): The folder where the link file is located (default 'After').
    """
    file_path = os.path.join(modified_folder, network_file)

    try:
        # Read the link file
        links_df = pd.read_csv(file_path)

        # Ensure the necessary identification columns exist
        if 'from_node_id' not in links_df.columns or 'to_node_id' not in links_df.columns:
            print("Error: Missing required columns 'from_node_id' and 'to_node_id' in the file.")
            return

        # Loop through each modification and update corresponding attributes
        for mod in link_modifications:
            from_node_id = mod.get('from_node_id')
            to_node_id = mod.get('to_node_id')

            # Validate that the modification has the required identification fields
            if from_node_id is None or to_node_id is None:
                print(f"Skipping modification {mod} because it lacks 'from_node_id' or 'to_node_id'.")
                continue

            # Create a mask to find the link(s) that match the identifiers
            mask = (links_df['from_node_id'] == from_node_id) & (links_df['to_node_id'] == to_node_id)
            if mask.sum() == 0:
                print(
                    f"No link found with from_node_id {from_node_id} and to_node_id {to_node_id}. Skipping modification.")
                continue

            # Update any provided attributes other than the identification fields
            for key, value in mod.items():
                if key in ['from_node_id', 'to_node_id']:
                    continue
                # If the column doesn't exist, add it with a default value of None
                if key not in links_df.columns:
                    links_df[key] = None
                links_df.loc[mask, key] = value

        # Sort the DataFrame by from_node_id and to_node_id
        sorted_links_df = links_df.sort_values(by=['from_node_id', 'to_node_id']).reset_index(drop=True)

        # Generate new link IDs sequentially
        sorted_links_df['link_id'] = range(1, len(sorted_links_df) + 1)

        # Write the updated DataFrame back to the same file in the folder
        sorted_links_df.to_csv(file_path, index=False)
        print(
            f"The file '{file_path}' has been successfully updated with the modifications and sorted with new link IDs.")

    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
    except Exception as e:
        print(f"An error occurred: {e}")


def compare_link_performance(baseline_file, modified_file, key_columns, threshold):
    """
    Compares link performance metrics between a baseline and a modified DTALite run.

    Args:
        baseline_file (str): Path to the baseline link_performance.csv.
        modified_file (str): Path to the modified link_performance.csv.
        key_columns (list): Columns to merge on (default: ['from_node_id', 'to_node_id']).

    Returns:
        pd.DataFrame: Merged DataFrame with computed differences for key metrics.
    """
    # Read the CSV files
    baseline_df = pd.read_csv(baseline_file)
    modified_df = pd.read_csv(modified_file)

    print(
        f"Baseline file '{baseline_file}' has {baseline_df.shape[0]} rows and columns: {baseline_df.columns.tolist()}")
    print(
        f"Modified file '{modified_file}' has {modified_df.shape[0]} rows and columns: {modified_df.columns.tolist()}")

    # Merge on key columns with automatic suffixes
    merged_df = pd.merge(baseline_df, modified_df, on=key_columns, suffixes=('_before', '_after'))

    # Example: Compute differences in travel time if that column exists.
    # Check for the travel_time column and calculate differences
    if 'travel_time_before' in merged_df.columns and 'travel_time_after' in merged_df.columns:
        merged_df['travel_time_diff'] = merged_df['travel_time_after'] - merged_df['travel_time_before']
        print("Calculated travel_time_diff for merged records.")
    else:
        print("Warning: Expected travel_time columns not found after merge.")

    if 'volume_before' in merged_df.columns and 'volume_after' in merged_df.columns:
        merged_df['volume_diff'] = merged_df['volume_after'] - merged_df['volume_before']
        print("Calculated volume_diff for merged records.")

    # Set threshold and filter significant changes
    if 'travel_time_diff' in merged_df.columns:
        significant_changes = merged_df[merged_df['travel_time_diff'].abs() >= threshold]
        print("Links with significant travel time changes:")
        print(significant_changes[key_columns + ['travel_time_before', 'travel_time_after', 'travel_time_diff', 'volume_before', 'volume_after', 'volume_diff']])
    else:
        print("No travel_time_diff computed; cannot filter significant changes.")

    return merged_df


# Example usage:
# merged_link_perf = compare_link_performance('baseline_link_performance.csv', 'modified_link_performance.csv')


def detect_affected_OD_pairs(baseline_file, modified_file, threshold):
    """
    Detects which OD pairs are affected by the network modifications by comparing
    baseline and modified DTALite OD performance files.

    The function merges the two files on the key columns and computes the differences
    in total_free_flow_travel_time and total_congestion_travel_time. OD pairs with
    differences greater than the given threshold are considered affected.

    Args:
        baseline_file (str): Path to the baseline OD_performance.csv.
        modified_file (str): Path to the modified OD_performance.csv.
        threshold (float): The threshold difference to consider an OD pair as affected.
                           Units should match those in the travel time columns.

    Returns:
        pd.DataFrame: DataFrame containing OD pairs with significant differences.
    """
    # Read the baseline and modified OD performance files
    baseline_df = pd.read_csv(baseline_file)
    modified_df = pd.read_csv(modified_file)

    # Merge on key columns: mode, o_zone_id, and d_zone_id
    merged_df = pd.merge(
        baseline_df,
        modified_df,
        on=['mode', 'o_zone_id', 'd_zone_id'],
        suffixes=('_before', '_after')
    )

    # Compute the differences for travel time metrics
    merged_df['free_flow_diff'] = merged_df['total_free_flow_travel_time_after'] - merged_df[
        'total_free_flow_travel_time_before']
    merged_df['congestion_diff'] = merged_df['total_congestion_travel_time_after'] - merged_df[
        'total_congestion_travel_time_before']
    merged_df['volume_diff'] = merged_df['volume_after'] - merged_df[
        'volume_before']

    # Identify OD pairs where either travel time difference exceeds the threshold
    affected_od = merged_df[
        (merged_df['free_flow_diff'].abs() >= threshold) |
        (merged_df['congestion_diff'].abs() >= threshold) |
        (merged_df['volume_diff'].abs() >= threshold)
        ]

    # Report affected OD pairs with relevant details
    print("Affected OD pairs (threshold = {}):".format(threshold))
    print(affected_od[[
        'mode',
        'o_zone_id',
        'd_zone_id',
        'total_free_flow_travel_time_before',
        'total_free_flow_travel_time_after',
        'free_flow_diff',
        'total_congestion_travel_time_before',
        'total_congestion_travel_time_after',
        'congestion_diff',
        'volume_before',
        'volume_after',
        'volume_diff'
    ]])

    return affected_od


# Example usage:
# affected_od = detect_affected_OD_pairs('baseline_OD_performance.csv', 'modified_OD_performance.csv', threshold=0.1)


def sensitivity_pipeline(network_file, modifications, baseline_folder, modified_folder, key_columns, threshold):
    """
     Runs a sensitivity analysis pipeline:
       1. Runs a baseline DTALite simulation.
       2. Updates the network file with modifications.
       3. Runs a modified simulation.
       4. Compares both runs to detect affected links and OD pairs.
       5. Outputs the comparison results to CSV files with selected columns.

     Args:
         network_file (str): Name of the network file (e.g., 'link.csv').
         modifications (list of dict): List of network modifications.
         baseline_folder (str): Folder for baseline simulation outputs.
         modified_folder (str): Folder for modified simulation outputs.
         key_columns (list): Columns to merge on for link performance.
         threshold (float): Threshold for flagging significant differences.

     Returns:
         tuple: (link_diff, od_diff) DataFrames.
     """
    # Step 1: Run the baseline simulation.
    print("Running baseline simulation...")
    baseline_output = run_dtalite_simulation(baseline_folder)

    # Step 2: Apply network modifications.
    print("Applying network modifications...")
    sort_and_rewrite_GMNS_links(modifications, network_file, modified_folder)

    # Step 3: Run the modified simulation.
    print("Running modified simulation...")
    modified_output = run_dtalite_simulation(modified_folder)

    # Step 4: Compare link performance.
    print("Comparing link performance...")
    link_diff = compare_link_performance(
        baseline_file=f"{baseline_folder}/link_performance.csv",
        modified_file=f"{modified_folder}/link_performance.csv", key_columns=key_columns, threshold=threshold
    )

    # Step 5: Compare OD performance to detect affected OD pairs.
    print("Comparing OD performance...")
    od_diff = detect_affected_OD_pairs(
        baseline_file=f"{baseline_folder}/od_performance.csv",
        modified_file=f"{modified_folder}/od_performance.csv",
        threshold=threshold
    )

    # Filter desired columns for CSV output
    link_output_cols = key_columns + ['travel_time_before', 'travel_time_after', 'travel_time_diff', 'volume_before', 'volume_after', 'volume_diff']
    link_diff_filtered = link_diff[link_output_cols]

    od_output_cols = [
        'mode', 'o_zone_id', 'd_zone_id',
        'total_free_flow_travel_time_before',
        'total_free_flow_travel_time_after',
        'free_flow_diff',
        'total_congestion_travel_time_before',
        'total_congestion_travel_time_after',
        'congestion_diff',
        'volume_before', 'volume_after', 'volume_diff'
    ]
    od_diff_filtered = od_diff[od_output_cols]

    # Write the filtered DataFrames to CSV files
    link_diff_filtered.to_csv('link_performance_comparison.csv', index=False)
    od_diff_filtered.to_csv('od_performance_comparison.csv', index=False)
    print("CSV files 'link_performance_comparison.csv' and 'od_performance_comparison.csv' have been saved.")

    return link_diff, od_diff


# -------------------------

# Path to your network file (e.g., 'link.csv')
network_file = 'link.csv'

# Define network modifications.
# Each dict must include 'from_node_id' and 'to_node_id' and any attribute to update.
modifications = [
    {'from_node_id': 1, 'to_node_id': 4, 'lanes': 3, 'free_speed': 70},
    {'from_node_id': 3, 'to_node_id': 2, 'free_speed': 50, 'capacity': 1500}
]

# Define output folders for baseline and modified simulation results.
baseline_folder = "Before"
modified_folder = "After"

# Run the sensitivity pipeline.
link_diff, od_diff = sensitivity_pipeline(
    network_file, modifications, baseline_folder, modified_folder, key_columns=['from_node_id', 'to_node_id'], threshold=0
)

