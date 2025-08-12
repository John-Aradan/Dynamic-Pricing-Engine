import pandas as pd
# Step 1: Load the CSV file
df = pd.read_csv(r"Data/events_data.csv")

# Step 2: Display the columns as a list
cols = ['id',
        'timing_type', 'time_of_day', 
        'food_bev_density', 'food_bev_pop_score', 'access_density', 'access_pop_score', 'lodging_density', 'lodging_pop_score',
        'average_income_zip', 'population_zip', 'median_age_zip', 
        'event_type', 'target_audience', 'event_mood_energy', 'freebies_included',
        'price']
filtered_df = df[cols]

filtered_df.loc[filtered_df['timing_type'].isin(['Single-Day-Ranged', 'Single-Day-Instant']), 'timing_type'] = 'Single-Day'

filtered_df.loc[:, 'is_weekend'] = (df['day_of_week'] > 4).astype(int)

value_counts_aud = filtered_df['target_audience'].value_counts()
to_remove = value_counts_aud[value_counts_aud <= 2].index
filtered_df = filtered_df[~filtered_df['target_audience'].isin(to_remove)]

value_counts_enr = filtered_df['event_mood_energy'].value_counts()
to_remove = value_counts_enr[value_counts_enr <= 4].index
filtered_df = filtered_df[~filtered_df['event_mood_energy'].isin(to_remove)]

value_counts_typ = filtered_df['event_type'].value_counts()
to_remove = value_counts_typ[value_counts_typ <= 3].index
filtered_df = filtered_df[~filtered_df['event_type'].isin(to_remove)]

value_counts_td = filtered_df['time_of_day'].value_counts()
to_remove = value_counts_td[value_counts_td <= 5].index
filtered_df = filtered_df[~filtered_df['time_of_day'].isin(to_remove)]

for col in ['event_type', 'event_mood_energy', 'freebies_included', 'target_audience']:
    filtered_df[col] = filtered_df[col].fillna('unknown')

filtered_df['price'] = filtered_df.pop('price')

filtered_df.to_csv("Data/cleaned_data.csv", index=False)