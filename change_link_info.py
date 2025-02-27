import pandas as pd


def sort_and_rewrite_GMNS_links(link_modifications, file_path='link.csv'):
    """
    Reads the link.csv file, updates specified attributes (e.g., lanes, free_speed, capacity)
    for a set of specified links, sorts the links sequentially by from_node_id and to_node_id,
    reassigns link IDs, and rewrites the sorted content back to the file.

    Args:
        link_modifications (list of dict): A list where each dictionary represents a modification with keys:
            - from_node_id (int): The starting node ID of the link.
            - to_node_id (int): The ending node ID of the link.
            - Any additional key-value pairs (e.g., lanes, free_speed, capacity) that need to be updated.
        file_path (str): Path to the link.csv file.
    """
    try:
        # Read the link.csv file
        links_df = pd.read_csv(file_path)

        # Ensure the necessary identification columns exist
        if 'from_node_id' not in links_df.columns or 'to_node_id' not in links_df.columns:
            print("Error: Missing required columns 'from_node_id' and 'to_node_id' in the file.")
            return

        # Loop through each modification and update corresponding attributes for each specified link
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
        sorted_links_df = links_df.sort_values(by=['from_node_id', 'to_node_id'])

        # Generate new link IDs sequentially
        sorted_links_df = sorted_links_df.reset_index(drop=True)
        sorted_links_df['link_id'] = range(1, len(sorted_links_df) + 1)

        # Write the updated DataFrame back to the file
        sorted_links_df.to_csv(file_path, index=False)
        print(
            f"The file '{file_path}' has been successfully updated with the modifications and sorted with new link IDs.")

    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
    except Exception as e:
        print(f"An error occurred: {e}")


# Define a list of link modifications. Each dictionary specifies the from_node_id, to_node_id,
# and any additional attributes to be updated.
modifications = [
    {'from_node_id': 1, 'to_node_id': 4, 'lanes': 3, 'free_speed': 70},
    {'from_node_id': 3, 'to_node_id': 2, 'free_speed': 50, 'capacity': 1500}
]

# Update the links and rewrite the file.
sort_and_rewrite_GMNS_links(modifications)
