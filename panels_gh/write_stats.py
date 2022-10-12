import pandas as pd
import json
import numpy as np

with open('panels_gh/right.json', 'r') as out_file:
    right = json.load(out_file)

with open('panels_gh/left.json', 'r') as out_file:
    left = json.load(out_file)

right = pd.DataFrame.from_dict(right)
left = pd.DataFrame.from_dict(left)
data = pd.concat([right, left], ignore_index=True)
data.to_csv('panels_gh/221012_panels_sizes.csv', encoding='utf-8', index=True)