import networkx as nx  
import pandas as pd
import numpy as np 
import matplotlib.pyplot as plt 


TTH = [[(0, 16), (16, 20), (20, 27), (27, 2), (2, 14), (14, 30), (30, 45), (45, 11), (11, 0)], [(0, 39), (39, 36), (36, 15), (15, 7), (7, 1), (1, 17), (17, 12), (12, 0)], [(0, 3), (3, 32), (32, 9), (9, 37), (37, 33), (33, 31), (31, 28), (28, 13), (13, 47), (47, 19), (19, 0)], [(0, 6), (6, 44), (44, 49), (49, 46), (46, 34), (34, 25), (25, 22), (22, 21), (21, 8), (8, 0)]]
MWF = [[(0, 5), (5, 29), (29, 7), (7, 23), (23, 1), (1, 10), (10, 0)], [(0, 9), (9, 37), (37, 33), (33, 42), (42, 47), (47, 48), (48, 18), (18, 26), (26, 43), (43, 24), (24, 0)], [(0, 35), (35, 8), (8, 2), (2, 3), (3, 12), (12, 38), (38, 0)], [(0, 39), (39, 41), (41, 4), (4, 11), (11, 40), (40, 27), (27, 16), (16, 6), (6, 0)]]


coordinates = pd.read_excel('NSLS_2_data.xls', usecols=(range(2,5)), sheet_name = 0)
edge_weights = pd.read_excel('NSLS_2_data.xls', skiprows = 3, usecols=(range(2, 53)) ,header = None, sheet_name = 1)

MWFGraph = nx.Graph()
TTHGraph = nx.Graph()

for subtour in MWF:
	for edge in subtour:
		nodeNum = edge[1]
		library = coordinates.iloc[nodeNum]['Library']
		pos = [coordinates.iloc[nodeNum]['Longitude'], coordinates.iloc[nodeNum]['Latitude']]
		MWFGraph.add_node(library, pos = pos)

for subtour in TTH:
	for edge in subtour:
		nodeNum = edge[1]
		library = coordinates.iloc[nodeNum]['Library']
		pos = [coordinates.iloc[nodeNum]['Longitude'], coordinates.iloc[nodeNum]['Latitude']]
		TTHGraph.add_node(library, pos = pos)

#g.add_weighted_edges_from([(nodes.iloc[i]['Node'], nodes.iloc[j]['Node'], edge_weights.iloc[i][j])])

# Change this the below code from TTH to MWF depending on what you wish to visualize

for subtour in TTH:
	for edge in subtour:
		print(len(subtour))
		lib1 = coordinates.iloc[edge[0]]['Library']
		lib2 = coordinates.iloc[edge[1]]['Library']
		TTHGraph.add_weighted_edges_from([(lib1, lib2, edge_weights.iloc[edge[0], edge[1]])])
'''
for subtour in TTH:
	for edge in subtour:
		lib1 = coordinates.iloc[edge[0]]['Library']
		lib2 = coordinates.iloc[edge[1]]['Library']
		TTHGraph.add_weighted_edges_from([lib1, lib2, edge_weights.iloc[edge[0], edge[1]]])
'''
# attempt to draw MWF graph...
pos=nx.get_node_attributes(TTHGraph, 'pos')
nx.draw(TTHGraph, pos=pos, with_labels=True, font_size=4, node_size=5)
plt.show()



