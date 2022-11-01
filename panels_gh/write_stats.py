import pandas as pd
import json
import numpy as np

with open('panels_gh/for_stats/niche_sizes.json', 'r') as out_file:
    data = json.load(out_file)


data = pd.DataFrame.from_dict(data, orient='index')
data.to_csv('panels_gh/for_stats/221031_niche_sizes.csv', encoding='utf-8', index=True)