import pandas as pd
import json
import numpy as np

# with open('panels_gh/for_stats/niche_sizes.json', 'r') as out_file:
# data = json.load(out_file)


# data = pd.DataFrame.from_dict(data, orient='index')
# data.to_csv('panels_gh/for_stats/221031_panels_sizes.csv', encoding='utf-8', index=True)

data = pd.read_csv('panels_gh/for_stats/221031_panels_sizes.csv')
new = {'1': [], '2': [], '3': [], '4': [], '5': [], '6': []}

for i,v in enumerate(data['names']):
    n = v[4]
    val = data.iloc[i]
    new[str(n)].append(list(val.values))


d = list(new.values())

iterables = [*[i for i in d], *[np.repeat('1', 122), np.repeat('2', 122), np.repeat('3', 122), np.repeat('4', 122), np.repeat('5', 122), np.repeat('6', 122)]]
#tuples = list(zip(*arrays))
#a = pd.MultiIndex.from_product(iterables, names=["names", "height", 'width'])
