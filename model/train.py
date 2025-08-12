import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error
import numpy as np

df = pd.read_csv('Data/cleaned_data.csv')

# Split the data into features and target variable
X = df.drop(columns = ['id','price'])
print(X.shape)
y = df['price']

# onehot encode categorical variables
X = pd.get_dummies(X, columns=['timing_type', 'time_of_day', 'event_type', 'target_audience', 'event_mood_energy', 'freebies_included', 'is_weekend'], drop_first=True, dtype=int)

print(X.shape)

# split data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

rf = RandomForestRegressor(n_estimators=100, random_state=42)
rf.fit(X_train, y_train)
y_pred = rf.predict(X_test)
print("Mean Squared Error:", mean_squared_error(y_test, y_pred))
