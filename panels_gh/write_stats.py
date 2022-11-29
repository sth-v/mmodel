#import pandas as pd
import json


class Stats:

    def __init__(self, unrolls):

        self.unrolls = unrolls

        self.sizes = {"name":[], "width":[], "height":[]}

    def bound_frame(self):
        for i in self.unrolls:

            try:
                frame = i.N_1

            except AttributeError:
                frame = i.N_3

            self.sizes["name"].append(frame.panel.tag)
            self.sizes["width"].append(round(frame.bound_stats.Width))
            self.sizes["height"].append(round(frame.bound_stats.Height))

        return self.sizes



s = Stats(x)

a = s.bound_frame()
with open('/Users/sofyadobycina/Documents/GitHub/mmodel/panels_gh/for_stats/nicheside_sizes.json', 'w') as out_file:
    json.dump(a, out_file)


#data = pd.DataFrame(a)
#data.to_csv('panels_gh/for_stats/221125_nicheside_sizes.csv', encoding='utf-8', index=True)
