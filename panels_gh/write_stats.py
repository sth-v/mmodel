import pandas as pd
import json


with open('panels_gh/for_stats/niche_sizes.json', 'r') as out_file:
    data = json.load(out_file)


data = pd.DataFrame(data)
data.to_csv('panels_gh/for_stats/221116_niche_sizes.csv', encoding='utf-8', index=True)

'''data = pd.read_csv('panels_gh/for_stats/221031_niche_sizes.csv')
new = {'1': [], '2': [], '3': [], '4': [], '5': [], '6': []}

for i, v in enumerate(data['names']):
    n = v[4]
    val = data.iloc[i]
    new[str(n)].append(list(val.values))

right = pd.DataFrame.from_dict(right)
left = pd.DataFrame.from_dict(left)
data = pd.concat([right, left], ignore_index=True)
data.to_csv('panels_gh/221012_panels_sizes.csv', encoding='utf-8', index=True)'''
