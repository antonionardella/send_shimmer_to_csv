import pandas as pd

# Read in the two CSV files
crew3_shimmer_address = pd.read_csv("crew3_shimmer_address.csv")
crew3_airdrop_export = pd.read_csv("crew3_airdrop_export.csv")

# get a list of unique names present in both CSV files
common_names = set(crew3_shimmer_address["Name"]).intersection(
    set(crew3_airdrop_export["Name"])
)

# filter both dataframes to include only rows with common names
df1_filtered = crew3_shimmer_address[crew3_shimmer_address["Name"].isin(common_names)]
df2_filtered = crew3_shimmer_address[crew3_shimmer_address["Name"].isin(common_names)]

# merge the two filtered dataframes on the 'Name' column
merged_df = pd.merge(df1_filtered, df2_filtered, on="Name")

# select only the 'Name' and 'Address' columns from the first CSV file and save to a new CSV file
merged_df[["Name", "answer_x"]].to_csv(
    "recepients_addresses.csv", index=False, header=["Name", "answer"]
)
