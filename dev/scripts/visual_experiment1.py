import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

df = pd.read_excel('experiment1.xlsx', index_col=0)

print(df.head())

s = sns.heatmap(df, cmap='coolwarm', linewidths=0.5, annot=True)
s.set(xlabel='Hidden state size', ylabel='Filtermap size')
plt.show()