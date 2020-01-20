# By: Cameron Witz
# Savings method for the VRP... adapted for problem instance 1.

# Outline of algorithm...
# I am not given a vehicle cost, so i'm assuming that isn't 

#1. Each node is visited by an individual vehicle.
#2. For each node pair, find the savings possible by joining them.
#3. Find pair (i,j) in the savings matrix with largest savings where:
	#a. i and j on different routes.
	#b. i and j are the first and last nodes visited.
	#c. Time spent on tour plus stoppage time is less than 160 minutes per driver

#4. Add arc (i,j), delete arcs (0,i) and (j,0). 

import pandas as pd
import numpy as np 
import random

# Read in the data
edge_weights = pd.read_excel('NSLS_2_data.xls', skiprows = 3, usecols=(range(2, 53)) ,header = None, sheet_name = 1)
frequency = pd.read_excel('NSLS_2_data.xls', usecols=(range(6,7)), sheet_name = 0)


# Build initial list of subtours for the nodes 
Freq2_only = []
Freq3_only = []
MWF = []
TTH = []
for node in range(1,50):
	subtour = [(0, node), (node, 0)]
	node_freq = frequency.iloc[node]['Frequency']
	if node_freq == 2:
		Freq2_only.append(subtour)
		TTH.append(subtour)
	elif node_freq == 3:
		Freq3_only.append(subtour)
		MWF.append(subtour)
	else:
		MWF.append(subtour)
		TTH.append(subtour)

# This will be useful for redirecting paths so that they have order 
def find_next_edge(edge, path):
	for pt_edge in path:
		if pt_edge != edge:
			if (pt_edge[0] == edge[1]) or (pt_edge[1] == edge[1]):
				return pt_edge
	raise ValueError('Next Edge not Found')

def find_start_or_end(tour, place): 
	if place == 'start':
		for edge in tour:
			if edge[0] == 0:
				return edge
		raise ValueError('No start node found')

	elif place == 'end':
		for edge in tour: 
			if edge[1] == 0:
				return edge
		raise ValueError('No end node found')

def makeDirectedPath(path):
	# This function simply takes the path and puts the nodes in order, so instead of path [(0,1), (3,1), (0,3)]
	# you will see [(0,1), (1,3), (3,0)]
	path2 = path.copy()
	orderedpath = []
	start = find_start_or_end(path2, 'start')
	orderedpath.append(start)
	i = 0
	while(len(orderedpath) != len(path)):
		find_next = find_next_edge(orderedpath[i], path2)
		path2.remove(find_next) # we don't want to add this again
		if orderedpath[i][1] == find_next[0]:
			orderedpath.append(find_next)
		else:
			reoredered_edge = (find_next[1], find_next[0])
			orderedpath.append(reoredered_edge)
		i = i +1
	return orderedpath

# Function reverse a tour
def tour_reverse(tour):
	new_tour = []
	for edge in tour:
		new_edge = (edge[1], edge[0])
		new_tour.append(new_edge)
	new_tour = makeDirectedPath(new_tour) # just in case... this should work fine
	return new_tour

# Function to calculate tour cost and check feasability...
def tourCheck(tour): 
	origCost = 10*len(tour) # initialize the path costs with the stoppage time on the tours

	# check if the tour length is less than 160 minutes total
	for i in range(0, len(tour)):
		origEdge = tour[i]
		origCost += edge_weights.iloc[origEdge[0], origEdge[1]]
	
	if origCost > 160:
		return [], False, np.inf
	else:
		return tour, True, origCost


# Use this to calculate the travel time for the drivers...
def tourCost(tour):
	cost = 10*len(tour)
	for edge in tour:
		cost += edge_weights.iloc[edge[0], edge[1]]
	return cost

# Function to calculate possible savings by swapping arcs assuming feasability
def findBestSavings(subtours):

	done = True
	bestSavingsTour = []
	bestSavings = np.inf
	best_i_index = 100
	best_j_index = 100

	for i in range(0, len(subtours)):
		cur_tour = subtours[i]
		for j in range(0, len(subtours)):
			next_tour = subtours[j]
			if i != j:

				# find the start of i and the end of j, and the end of i and start of j
				cur_start = find_start_or_end(cur_tour, 'start')
				cur_end = find_start_or_end(cur_tour, 'end')

				next_start = find_start_or_end(next_tour, 'start')
				next_end = find_start_or_end(next_tour, 'end')

				# create the two new possible tours from these edges.
				newTour1 = [] # combine cur_start and next_end
				newTour2 = [] # combine cur_end and next_start

				for edge in cur_tour:
					if edge != cur_start: 
						newTour1.append(edge)

					if edge != cur_end:
						newTour2.append(edge)
				for edge in next_tour:
					if edge != next_end: 
						newTour1.append(edge)
					if edge != next_start:
						newTour2.append(edge)

				newTour1.append((cur_start[1], next_end[0]))
				newTour1 = makeDirectedPath(newTour1)
				newTour2.append((next_start[1], cur_end[0]))
				newTour2 = makeDirectedPath(newTour2)

				# Check if both new tours are feasible
				ptour1, feas1, cost1 = tourCheck(newTour1)
				ptour2, feas2, cost2 = tourCheck(newTour2)

				# Calculate savings with the two new tours
				old_costs = tourCost(cur_tour) + tourCost(next_tour)
				save1 = cost1 - old_costs # if we are actually improving our solution, this should be negative
				save2 = cost2 - old_costs
				print(feas1, feas2)
				if (feas1 == True) and (feas2 == True): 
					if save1 < save2:
						if save1 < bestSavings:
							bestSavings = save1
							bestSavingsTour = ptour1
							best_i_index = i
							best_j_index = j
					else:
						if save2 < bestSavings:
							bestSavings = save2
							bestSavingsTour = ptour2
							best_i_index = i
							best_j_index = j

	# If we are still making good saving (first condition) or we don't yet have 4 or fewer subtours (second condition)
	# we need to continue running the algorithm. 
	if (bestSavings < 0) or (len(subtours) > 4):
		# Remove the two tours we are joining, and add the joined tour...
		done = False
		try:
			removei = subtours[best_i_index]
		except:
			print(best_i_index)
			print(subtours)
			# return empty list, done, newattempt
			return [], False, True
		removej = subtours[best_j_index]
		subtours.remove(removei)
		subtours.remove(removej)
		subtours.append(bestSavingsTour)
		return subtours, done
	else:
		# We have stopped making beneficial savings on our tours, and we have at most 4 subtours
		done = True
		return subtours, done

def findBestSavingsRand(subtours, range_):
	all_savings = pd.DataFrame(columns=['i', 'j', 'savings', 'tour'])
	done = True
	bestSavingsTour = []
	bestSavings = np.inf
	best_i_index = 100
	best_j_index = 100
	list_of_all_tours = []
	tlistindex = 0
	for i in range(0, len(subtours)):
		cur_tour = subtours[i]
		for j in range(0, len(subtours)):
			next_tour = subtours[j]
			if i != j:

				# find the start of i and the end of j, and the end of i and start of j
				cur_start = find_start_or_end(cur_tour, 'start')
				cur_end = find_start_or_end(cur_tour, 'end')

				next_start = find_start_or_end(next_tour, 'start')
				next_end = find_start_or_end(next_tour, 'end')

				# create the two new possible tours from these edges.
				newTour1 = [] # combine cur_start and next_end
				newTour2 = [] # combine cur_end and next_start

				for edge in cur_tour:
					if edge != cur_start: 
						newTour1.append(edge)

					if edge != cur_end:
						newTour2.append(edge)
				for edge in next_tour:
					if edge != next_end: 
						newTour1.append(edge)
					if edge != next_start:
						newTour2.append(edge)

				newTour1.append((cur_start[1], next_end[0]))
				newTour1 = makeDirectedPath(newTour1)
				newTour2.append((next_start[1], cur_end[0]))
				newTour2 = makeDirectedPath(newTour2)

				# Check if both new tours are feasible
				ptour1, feas1, cost1 = tourCheck(newTour1)
				ptour2, feas2, cost2 = tourCheck(newTour2)

				# Calculate savings with the two new tours
				old_costs = tourCost(cur_tour) + tourCost(next_tour)
				save1 = cost1 - old_costs # if we are actually improving our solution, this should be negative
				save2 = cost2 - old_costs
				# add data to the dataframe...
				if feas1:
					list_of_all_tours.append(newTour1)
					tdata1 = {'i':i, 'j':j, 'savings':save1, 'tour': tlistindex}
					tlistindex +=1

					tdf1 =  pd.DataFrame(data = tdata1, index=[0])
					all_savings = all_savings.append(tdf1)

				if feas2: 
					list_of_all_tours.append(newTour2)
					tdata2 = {'i':i, 'j':j, 'savings':save2, 'tour':tlistindex}
					tlistindex +=1

					tdf2 =  pd.DataFrame(data = tdata2, index = [0])
					all_savings = all_savings.append(tdf2)
	
	# If the dataframe is empty and we weren't done, then we have to start all over again and hope things work out differently...
	if (all_savings.empty == True) or (all_savings.isnull().values.any()):
		print('___________________________')
		print('Triggered Stopping Criteria')
		if len(subtours) <= 4:
			print('Solution Found')
			return subtours, True, False
		else:
			print('Solution not found, starting sequence again')
			return [], False, True

	# Sort the data frame...
	all_savings.sort_values(by='savings', axis=0, ascending=True, inplace=True)
	all_savings.reset_index().drop(['index'],axis=1)
	randex = min(random.randint(0, range_), all_savings.shape[0]-1)
	
	# If we are still making good saving (first condition) or we don't yet have 4 or fewer subtours (second condition)
	# we need to continue running the algorithm. 
	bestSavings = all_savings.iloc[randex]['savings']
	best_i_index = all_savings.iloc[randex]['i']
	best_j_index = all_savings.iloc[randex]['j']
	bestSavingsTour = list_of_all_tours[all_savings.iloc[randex]['tour']]

	if (bestSavings < 0) or (len(subtours) > 4):
		# Remove the two tours we are joining, and add the joined tour...
		done = False
		removei = subtours[best_i_index]
		removej = subtours[best_j_index]
		subtours.remove(removei)
		subtours.remove(removej)
		subtours.append(bestSavingsTour)
		return subtours, done, False
	else:
		# We have stopped making beneficial savings on our tours, and we have at most 4 subtours
		done = True
		return subtours, done, False

####################

# Calculate solution for nodes requiring 3 visits and 5 visits
print('Beginning sequence for 3 frequency nodes...')
done = False

Freq3 = MWF.copy()

iteration = 0
while(not done):

	print('iteration ', iteration)
	Freq3, done, newAttempt = findBestSavingsRand(Freq3,1)

	if newAttempt == True:
		Freq2 = TTH.copy()
		iteration = 0
	else:
		iteration += 1

print('\nInitial Solution for 3 frequency nodes')
print(Freq3)
print('')
################################
# Calculate solution for nodes requiring 2 and 5 visits...
print('Beginning sequence for 2 frequency nodes...')
done = False

Freq2 = TTH.copy()

iteration = 0
while(not done):

	print('iteration ', iteration)
	Freq2, done, newAttempt = findBestSavingsRand(Freq2,1)

	if newAttempt == True:
		Freq2 = TTH.copy()
		iteration = 0
	else:
		iteration += 1

print('\nInitial Solution for 3 frequency nodes')
print(Freq2)
print('')

# Solutions from the first two runs are:

'''
Each bracketed group [] indicates one route for a given vehicle. 
The arcs inside indicate the direction of the edge, (0, 1) (1, 2) indicates an edge from node 0 to 1, and 1 to 2.
The 0 node is the depot. 

MWF Tours
[(0, 5), (5, 29), (29, 7), (7, 23), (23, 1), (1, 10), (10, 0)]
[(0, 41), (41, 4), (4, 11), (11, 16), (16, 27), (27, 40), (40, 6), (6, 0)]
[(0, 24), (24, 43), (43, 26), (26, 18), (18, 48), (48, 47), (47, 42), (42, 33), (33, 37), (37, 9), (9, 0)]
[(0, 35), (35, 3), (3, 38), (38, 0)]


TTH Tours
[(0, 16), (16, 20), (20, 27), (27, 2), (2, 14), (14, 30), (30, 45), (45, 11), (11, 0)]
[(0, 8), (8, 21), (21, 22), (22, 25), (25, 34), (34, 46), (46, 49), (49, 44), (44, 0)]
[(0, 39), (39, 36), (36, 15), (15, 7), (7, 1), (1, 17), (17, 12), (12, 0)]
[(0, 19), (19, 47), (47, 13), (13, 28), (28, 31), (31, 33), (33, 37), (37, 9), (9, 32), (32, 0)]]
'''


###################################################
# Attempt to add in nodes from MWF into the TTH group if possible.

# Write function to return all of the nodes except for the nodes in the initial MWF or TTH group
def clean_solution(init_group, subtours):
	for i in subtours:
		if i in init_group:
			subtours.remove(i)
	return subtours

# Need to reonstruct findBestSavingsRand function to stop only when it is infeasible. And then to return the solution
# minus all of the nodes that are in MWF group...
# This function is no longer being used.  
def maximize_frequency(subtours, range_, init_group):
	all_savings = pd.DataFrame(columns=['i', 'j', 'savings', 'tour'])
	done = True
	bestSavingsTour = []
	bestSavings = np.inf
	best_i_index = 100
	best_j_index = 100
	list_of_all_tours = []
	tlistindex = 0
	for i in range(0, len(subtours)):
		cur_tour = subtours[i]
		for j in range(0, len(subtours)):
			next_tour = subtours[j]
			if i != j:

				# find the start of i and the end of j, and the end of i and start of j
				cur_start = find_start_or_end(cur_tour, 'start')
				cur_end = find_start_or_end(cur_tour, 'end')

				next_start = find_start_or_end(next_tour, 'start')
				next_end = find_start_or_end(next_tour, 'end')

				# create the two new possible tours from these edges.
				newTour1 = [] # combine cur_start and next_end
				newTour2 = [] # combine cur_end and next_start

				for edge in cur_tour:
					if edge != cur_start: 
						newTour1.append(edge)

					if edge != cur_end:
						newTour2.append(edge)
				for edge in next_tour:
					if edge != next_end: 
						newTour1.append(edge)
					if edge != next_start:
						newTour2.append(edge)

				newTour1.append((cur_start[1], next_end[0]))
				newTour1 = makeDirectedPath(newTour1)
				newTour2.append((next_start[1], cur_end[0]))
				newTour2 = makeDirectedPath(newTour2)

				# Check if both new tours are feasible
				ptour1, feas1, cost1 = tourCheck(newTour1)
				ptour2, feas2, cost2 = tourCheck(newTour2)

				# Calculate savings with the two new tours
				old_costs = tourCost(cur_tour) + tourCost(next_tour)
				save1 = cost1 - old_costs # if we are actually improving our solution, this should be negative
				save2 = cost2 - old_costs
				# add data to the dataframe...
				if feas1:
					list_of_all_tours.append(newTour1)
					tdata1 = {'i':i, 'j':j, 'savings':save1, 'tour': tlistindex}
					tlistindex +=1

					tdf1 =  pd.DataFrame(data = tdata1, index=[0])
					all_savings = all_savings.append(tdf1)

				if feas2: 
					list_of_all_tours.append(newTour2)
					tdata2 = {'i':i, 'j':j, 'savings':save2, 'tour':tlistindex}
					tlistindex +=1

					tdf2 =  pd.DataFrame(data = tdata2, index = [0])
					all_savings = all_savings.append(tdf2)
	
	# If the dataframe is empty and we weren't done, then we have to start all over again and hope things work out differently...
	if (all_savings.empty == True) or (all_savings.isnull().values.any()):
		print('___________________________')
		print('Triggered Stopping Criteria')
		if len(subtours) <= 4:
			print('Solution Found')
			return subtours, True, False
		else:
			print('Cleaning up solution')
			# Use function to remove nodes in the MWF group
			subtours = clean_solution([init_group], subtours)
			if len(subtours) != 4:
				print(init_group)
				print('')
				print(subtours)
				raise ValueError('Something has gone terribly wrong')
			return subtours, True, False

	# Sort the data frame...
	all_savings.sort_values(by='savings', axis=0, ascending=True, inplace=True)
	all_savings.reset_index().drop(['index'],axis=1)
	randex = min(random.randint(0, range_), all_savings.shape[0]-1)
	
	# If we are still making good saving (first condition) or we don't yet have 4 or fewer subtours (second condition)
	# we need to continue running the algorithm. 
	bestSavings = all_savings.iloc[randex]['savings']
	best_i_index = all_savings.iloc[randex]['i']
	best_j_index = all_savings.iloc[randex]['j']
	bestSavingsTour = list_of_all_tours[all_savings.iloc[randex]['tour']]

	if (len(subtours) > 4): # I have removed the check to see if we are making good savings, as we now want to 
	# put as many nodes on the path as feasible in the least cost way. 
		# Remove the two tours we are joining, and add the joined tour...
		done = False
		removei = subtours[best_i_index]
		removej = subtours[best_j_index]
		subtours.remove(removei)
		subtours.remove(removej)
		subtours.append(bestSavingsTour)
		return subtours, done, False
	else:
		# We have stopped making beneficial savings on our tours, and we have at most 4 subtours
		done = True
		return subtours, done, False


def makeDirectedPath2(path):
	# This is an updated version which was necessary for 2 edge optimization.
	# This function simply takes the path and puts the nodes in order, so instead of path [(0,1), (3,1), (0,3)]
	# you will see [(0,1), (1,3), (3,0)] which makes things more readable and is essential for my edge swapping logic
	path2 = path.copy()
	orderedpath = []
	try: 
		start = find_start_or_end(path2,'start')
	except:
		start = find_start_or_end(path2,'end')
		start = (start[1], start[0])

	orderedpath.append(start)
	i = 0
	while(len(orderedpath) != len(path)):
		find_next = find_next_edge(orderedpath[i], path2)
		path2.remove(find_next) # we don't want to add this again
		if orderedpath[i][1] == find_next[0]:
			orderedpath.append(find_next)
		else:
			reoredered_edge = (find_next[1], find_next[0])
			orderedpath.append(reoredered_edge)
		i = i +1
	return orderedpath


# Run two Edge optimization on the path...
def swap_edges(old_edges, new_edges, path):
	# old edges and new edges should be ordered, the first element of old edges should swap with the first element of new edges etc.
	npath = path.copy()
	for i in range(0, len(path)):
		for j in range(0, len(old_edges)):
			if npath[i] == old_edges[j]:
				npath[i] = new_edges[j]

	return npath

def BestEdgeSwap(path):
	improvement = False
	minCostOriginal = None
	minCostSwap = None
	cost = tourCost(path.copy())
	# loop through all the possible edge swaps we can make, and save the one that decreases our cost the most
	for cur_edge in path:
		for look_edge in path:
			if (cur_edge != look_edge) and (cur_edge[0] != look_edge[1]) and (cur_edge[1] != look_edge[0]) and (cur_edge[0] != look_edge[0]) and (cur_edge[1] != look_edge[1]):
				old_edges = [cur_edge, look_edge]
				new_edges = [(cur_edge[0],look_edge[0]), (cur_edge[1],look_edge[1])]
				tpath = swap_edges(old_edges, new_edges, path.copy())
				tpath, feas, tcost = tourCheck(tpath)
				if feas == False:
					continue
				else:
					if tcost < cost:
						cost = tcost
						minCostOriginal = cur_edge
						minCostSwap = look_edge
	if minCostSwap != None:
		improvement = True
		BestOldEdges = [minCostOriginal, minCostSwap]
		BestNewEdges = [(minCostOriginal[0], minCostSwap[0]), (minCostOriginal[1], minCostSwap[1])]
		path = swap_edges(BestOldEdges, BestNewEdges, path.copy())
	
	path, feas, cost = tourCheck(path)
	if feas == False:
		return [], improvement, feas

	return path, improvement, feas

def TwoEdgeOpt(path):
	improvement = True
	while(improvement):
		path, improvement, feas = BestEdgeSwap(path.copy())
		if path != []:
			print(path)
			path = makeDirectedPath2(path)
	return path, feas

def addNode(node, tour):
	beginning = find_start_or_end(tour, 'start')
	tour.remove(beginning)
	nstart = (0, node)
	nnext = (node, beginning[1])
	tour.append(nstart)
	tour.append(nnext)
	return tour

######################################################
'''
Two edge optimization for this heuristic. 
0. Save the values of the existing tours which are feasible, before adding the node.
1. Take a node, and add it into the all of the existing tours.
2. Run two edge optimization on all of the tours with the injected node.
3. Find all of the tours that are still feasible with this injection. 
4. Find which tour has the least impacted travel time with the injection, and keep that tour. 
5. Reset the subtours to have all of the originals except for the tour found in step 4.
6. Repeat step 1 until we have gone through all of the nodes. 

'''
'''
print('Save this output')
print('Freq2')
print(Freq2)
print('\nFreq3')
print(Freq3)
print('\nFreq2_only')
print(Freq2_only)
print('\nFreq3_only')
print(Freq3_only)
'''
'''
Freq2=[[(0, 16), (16, 20), (20, 27), (27, 2), (2, 14), (14, 30), (30, 45), (45, 11), (11, 0)], [(0, 8), (8, 21), (21, 22), (22, 25), (25, 34), (34, 46), (46, 49), (49, 44), (44, 0)], [(0, 39), (39, 36), (36, 15), (15, 7), (7, 1), (1, 17), (17, 12), (12, 0)], [(0, 19), (19, 47), (47, 13), (13, 28), (28, 31), (31, 33), (33, 37), (37, 9), (9, 32), (32, 0)]]

Freq3=[[(0, 5), (5, 29), (29, 7), (7, 23), (23, 1), (1, 10), (10, 0)], [(0, 41), (41, 4), (4, 11), (11, 16), (16, 27), (27, 40), (40, 6), (6, 0)], [(0, 9), (9, 37), (37, 33), (33, 42), (42, 47), (47, 48), (48, 18), (18, 26), (26, 43), (43, 24), (24, 0)], [(0, 38), (38, 3), (3, 35), (35, 0)]]

Freq2_only=[[(0, 2), (2, 0)], [(0, 8), (8, 0)], [(0, 12), (12, 0)], [(0, 13), (13, 0)], [(0, 14), (14, 0)], [(0, 15), (15, 0)], [(0, 17), (17, 0)], [(0, 19), (19, 0)], [(0, 20), (20, 0)], [(0, 21), (21, 0)], [(0, 22), (22, 0)], [(0, 25), (25, 0)], [(0, 28), (28, 0)], [(0, 30), (30, 0)], [(0, 31), (31, 0)], [(0, 32), (32, 0)], [(0, 34), (34, 0)], [(0, 36), (36, 0)], [(0, 39), (39, 0)], [(0, 44), (44, 0)], [(0, 45), (45, 0)], [(0, 46), (46, 0)], [(0, 49), (49, 0)]]

Freq3_only=[[(0, 3), (3, 0)], [(0, 4), (4, 0)], [(0, 5), (5, 0)], [(0, 6), (6, 0)], [(0, 10), (10, 0)], [(0, 18), (18, 0)], [(0, 23), (23, 0)], [(0, 24), (24, 0)], [(0, 26), (26, 0)], [(0, 29), (29, 0)], [(0, 35), (35, 0)], [(0, 38), (38, 0)], [(0, 40), (40, 0)], [(0, 41), (41, 0)], [(0, 42), (42, 0)], [(0, 43), (43, 0)], [(0, 48), (48, 0)]]
'''

print('_________________________________')
print('Adding nodes to Freq2')
iteration = 0
newFreq2 = Freq2.copy()

for new_edge in Freq3_only:
	print('Iteration ', iteration)
	iteration += 1
	node = new_edge[0][1] #access first element of list, and second element of that is the node
	bestImprovement = np.inf

	atleast1Feas = False
	besttour = []
	bestindex = 1000

	for i in range(0, len(newFreq2)):
		orig_cost = tourCost(newFreq2[i].copy())
		testTour = addNode(node, newFreq2[i].copy())
		testTour = makeDirectedPath(testTour.copy())
		ntour, feas = TwoEdgeOpt(testTour.copy())
		if feas == True:
			atleast1Feas = True
			ntour = makeDirectedPath2(ntour.copy())
			tcost = tourCost(ntour.copy())
			improvement = tcost - orig_cost
			if improvement < bestImprovement:
				bestImprovement = improvement
				bestindex = i
				besttour = ntour

	# After this loop we should know if it was feasible to add the node somewhere
	if atleast1Feas == True:
		print('Improvement made, adding new path')
		print(besttour)
		newFreq2.remove(newFreq2[bestindex])
		newFreq2.append(besttour)


print('Original Tour set')
print(Freq2)
print('\nNew Tour set')
print(newFreq2)
#######################################

print('_________________________________')
print('Adding nodes to Freq3')
iteration = 0
newFreq3 = Freq3.copy()

for new_edge in Freq2_only:
	print('Iteration ', iteration)
	iteration += 1
	node = new_edge[0][1] #access first element of list, and second element of that is the node
	bestImprovement = np.inf

	atleast1Feas = False
	besttour = []
	bestindex = 1000

	for i in range(0, len(newFreq3)):
		orig_cost = tourCost(newFreq3[i].copy())
		testTour = addNode(node, newFreq3[i].copy())
		testTour = makeDirectedPath2(testTour.copy())
		ntour, feas = TwoEdgeOpt(testTour.copy())
		if feas == True:
			atleast1Feas = True
			ntour = makeDirectedPath(ntour.copy())
			tcost = tourCost(ntour.copy())
			improvement = tcost - orig_cost
			if improvement < bestImprovement:
				bestImprovement = improvement
				bestindex = i
				besttour = ntour

	# After this loop we should know if it was feasible to add the node somewhere
	if atleast1Feas == True:
		print('Improvement made, adding new path')
		print(besttour)
		newFreq3.remove(newFreq3[bestindex])
		newFreq3.append(besttour)



print('Original Tour set')
print(Freq3)
print('\nNew Tour set')
print(newFreq3)
print('')

print('_________________________________')
print('Final Solution\n')
print('MWF tours:')
for i in newFreq3:
	cost = tourCost(i)
	print('Driver Time = ', cost)
	print(i)
print('')

print('TTH tours:')
for i in newFreq2:
	cost = tourCost(i)
	print('Driver Time = ' ,cost)
	print(i)
print('')

nodeCount2 = 0
nodeCount3 = 0
num_nodes = 49 # This is not including the depot
for i in range(0, 4):
	nodeCount2 += len(newFreq2[i]) -1
	nodeCount3 += len(newFreq3[i]) -1

print(nodeCount2)
print(nodeCount3)

total_freq = nodeCount3*3 +nodeCount2*2

avg_freq = total_freq/num_nodes
print(total_freq)
print('Average node Frequency = %.3f' %(avg_freq))





# This section was an old and less effective way that I was adding nodes to the tours. 

'''
# Previous attempt at adding nodes to subtours
print('Adding frequency 3 nodes to TTH tours...')
done = False

iteration = 0
for i in Freq3_only:
	init_group = i
	Freq2.append(init_group)

	print('iteration ', iteration)
	Freq2, done, newAttempt = maximize_frequency(Freq2,1, init_group)
	iteration += 1


print('\nFinal Solution for adding nodes to subtours on TTH')
print(Freq2)
print('')
'''
'''
TTH
Before 
[(0, 16), (16, 20), (20, 27), (27, 2), (2, 14), (14, 30), (30, 45), (45, 11), (11, 0)]
[(0, 8), (8, 22), (22, 21), (21, 25), (25, 34), (34, 46), (46, 49), (49, 44), (44, 0)]
[(0, 39), (39, 36), (36, 15), (15, 7), (7, 1), (1, 17), (17, 12), (12, 0)]
[(0, 19), (19, 47), (47, 13), (13, 28), (28, 31), (31, 33), (33, 37), (37, 9), (9, 32), (32, 0)]]

After 
[[(0, 16), (16, 20), (20, 27), (27, 2), (2, 14), (14, 30), (30, 45), (45, 11), (11, 0)]
[(0, 39), (39, 36), (36, 15), (15, 7), (7, 1), (1, 17), (17, 12), (12, 0)]
[(0, 19), (19, 47), (47, 13), (13, 28), (28, 31), (31, 33), (33, 37), (37, 9), (9, 32), (32, 3), (3, 0)]
[(0, 8), (8, 22), (22, 21), (21, 25), (25, 34), (34, 46), (46, 49), (49, 44), (44, 6), (6, 0)]]
'''
'''
print('Adding frequency 2 nodes to MWF tours...')
done = False

iteration = 0
for i in Freq2_only:
	init_group = i
	Freq3.append(init_group)

	print('iteration ', iteration)
	Freq3, done, newAttempt = maximize_frequency(Freq3,1, init_group)
	iteration += 1


print('\nFinal Solution for adding nodes to subtours on MWF')
print(Freq3)
print('')
'''

'''
MWF 
[[(0, 5), (5, 29), (29, 7), (7, 23), (23, 1), (1, 10), (10, 0)]
[(0, 41), (41, 4), (4, 11), (11, 16), (16, 27), (27, 40), (40, 6), (6, 0)]
[(0, 24), (24, 43), (43, 26), (26, 18), (18, 48), (48, 47), (47, 42), (42, 33), (33, 37), (37, 9), (9, 0)]
[(0, 38), (38, 3), (3, 35), (35, 2), (2, 8), (8, 19), (19, 0)]]

TTH
[[(0, 16), (16, 20), (20, 27), (27, 2), (2, 14), (14, 30), (30, 45), (45, 11), (11, 0)]
[(0, 39), (39, 36), (36, 15), (15, 7), (7, 1), (1, 17), (17, 12), (12, 0)]
[(0, 19), (19, 47), (47, 13), (13, 28), (28, 31), (31, 33), (33, 37), (37, 9), (9, 32), (32, 3), (3, 0)]
[(0, 8), (8, 22), (22, 21), (21, 25), (25, 34), (34, 46), (46, 49), (49, 44), (44, 6), (6, 0)]]
'''
print('For visualization')
print('Freq2')
print(newFreq2)
print('Freq3')
print(newFreq3)














