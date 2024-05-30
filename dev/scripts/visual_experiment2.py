import pandas as pd
import plotly.express as px

df = pd.read_csv('experiment2.csv', index_col=0)

print(df.head())

fig = px.parallel_coordinates(df, color="metric/Accuracy",
    dimensions=['metric/Accuracy', 'Lstm layers', 'Dropout'],
    color_continuous_scale=px.colors.sequential.thermal,
    color_continuous_midpoint=0.5)

fig.show()