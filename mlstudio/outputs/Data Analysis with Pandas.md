# Data Analysis with Pandas

---

**Created:** 2024-01-15 10:36:40

**Last Updated:** 2024-01-15 10:46:40

---


### 👤 User

2024-01-15 10:36:40
How do I read a CSV file and filter rows in Pandas?


### 🤖 Assistant

2024-01-15 10:37:00
Here's how to read a CSV file and filter rows using Pandas:
```python
import pandas as pd

# Read CSV file
df = pd.read_csv('data.csv')

# View first few rows
print(df.head())

# Filter rows where column value meets a condition
filtered_df = df[df['age'] > 25]

# Filter with multiple conditions
filtered_df = df[(df['age'] > 25) & (df['city'] == 'New York')]

# Filter using isin()
cities_of_interest = ['New York', 'Los Angeles', 'Chicago']
filtered_df = df[df['city'].isin(cities_of_interest)]
```
These filtering operations return new DataFrames, leaving the original unchanged.
