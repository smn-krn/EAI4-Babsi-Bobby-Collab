"""
This file processes the raw CSV recordings from the "recordings" folder, 
removes the "label" column, and saves the cleaned data in a new "recordings_clean" folder. 
It also creates a "labels.csv" file that maps each cleaned file ID 
to its corresponding label and original filename.
"""

import os
import pandas as pd

input_folder = "recordings"
output_folder = "recordings_clean"
labels_file = "labels.csv"

os.makedirs(output_folder, exist_ok=True)

label_rows = []
file_id = 0

# Process each CSV file in the input folder
for filename in os.listdir(input_folder):
    if not filename.endswith(".csv"):
        continue

    print("Processing:", filename)

    filepath = os.path.join(input_folder, filename)
    df = pd.read_csv(filepath)

    # Extract label
    if "label" not in df.columns:
        continue

    label = df["label"].iloc[0]

    # Drop label column
    df_clean = df.drop(columns=["label"])

    # Assign ID
    file_id += 1
    new_name = f"{file_id:04d}.csv"
    new_path = os.path.join(output_folder, new_name)

    df_clean.to_csv(new_path, index=False)

    # Save mapping
    label_rows.append({
        "id": f"{file_id:04d}",
        "label": label
    })

# Save labels file
labels_df = pd.DataFrame(label_rows)
labels_df.to_csv(labels_file, index=False)

print("Done. Cleaned data + labels mapping created.")