'''

This file implements a neighborgrid data structure, which allows for more efficient
sorting of particles by their positions. By only searching nearby grid cells, the 
number of pairwise distance computations to determine bonds can be drastically reduced. 

Code modified from a 2D version created by Daniel Goldstein. 

'''


import numpy as np
from itertools import product
import sys


class Neighborgrid:
    '''This class implements a neighborlist to faciliate the fast
    finding of nearby particles. '''

    def __init__(self, lim, R, periodic):
        
        #set the bounding box for the simulation
        self.lim = np.array(lim)
        self.domain_size = self.lim[:,1] - self.lim[:,0]

        #set which dimensions are periodic
        self.periodic = periodic

        #set the interaction range
        self.R = R

        #get the number of dimensions for the requested system
        self.dim = len(self.lim)
        
        #break up the space of the simulation into a grid were the size
        #of each box is at least R then we will only need to check the
        #8 boxes around each particle

        self.numD    = np.zeros(self.dim, dtype=int)
        self.boxSize = np.zeros(self.dim, dtype=float)

        for i in range(self.dim):
            self.numD[i]    = np.floor(self.domain_size[i] / (self.R/2))
            self.boxSize[i] = self.domain_size[i] / self.numD[i]
        
        #init a dict to store grid cell to particle mapping
        self.map = {}

        #if the domain boundaries aren't of the form [0,L], define a shift to make it so
        self.shift = []
        for i in range(self.dim):
            self.shift.append(-lim[i][0])
        self.shift = np.array(self.shift)

        #list of all grid cell moves to check for neighbors
        self.indexAdjustment = list(product([-2,-1,0,1,2], repeat=self.dim))


    def update(self, bodies):
        '''The update function takes in a list of bodies (objects with a position) and will
        create a map from box number and from particle'''

        #empty out the dictionary from previous step
        self.map.clear()

        #add in new particle positions
        for body in bodies:
            self.addItemToMap(self.convertPosToIndex(body), body)
            

    def convertPosToIndex(self, body):

        #grab the position of the body (2 or 3 dim)
        position = body.get_position()[0:self.dim]

        #check if all coordinates are within the known box size

        #for loop version
        # for i in range(self.dim):
        #     if position[i] < self.lim[i][0] or position[i] > self.lim[i][1]:
        #         raise ValueError("Particle is outside the set bounds")

        #vectorized version - reduces total runtime by about 10%
        if ( (position < self.lim[:,0]).any() or (position > self.lim[:,1]).any() ):
            print(self.lim)
            print(position)
            raise ValueError("Particle is outside the set bounds")

        #convert to an index - tuple for use as key in map
        # index = []
        # for i in range(self.dim):
        #     box_num = np.floor((position[i]+self.shift[i]) / self.boxSize[i])
        #     index.append(int(box_num))

        #vectorized version - reduces function time by factor of 2
        index = ((position + self.shift) / self.boxSize).astype(int)

        return tuple(index)



    def addItemToMap(self, key, value):

        if key in self.map:
            self.map[key].append(value)

        else:
            self.map[key] = [value]


    def getNeighborhood(self, body):
        '''find the box that the atom is in, look in the 5x5(x5) area around
        it and return all that are within the interaction radius'''

        centerBox = self.convertPosToIndex(body)  
        body_list = []

        for box in self.AdjacentBoxes(centerBox):
            if box in self.map:
                if isinstance(self.map[box], list):
                   for body_j in self.map[box]:

                        #check that body_j is not the original body and within cutoff
                        if body != body_j:
                            if body_j.distance_to_body(body, self.domain_size) < self.R:
                                body_list.append(body_j)

        return body_list
               
       
    def AdjacentBoxes(self, centerBox):
        ''' determine all adjacent boxes to the center'''

        #init list of all neighbor indices
        neighbor_list = []

        #get all possible grid shifts within range
        indexAdjustment = self.indexAdjustment

        # add the adjustment to the center box and then wrap boundaries  
        for boxAdjustment in indexAdjustment:

            #for loop version - note: vectorizing this led to slowdown
            neighborBox = [0]*self.dim
            for i in range(self.dim):
                neighborBox[i] = (centerBox[i]+boxAdjustment[i]) % self.numD[i]

            neighbor_list.append(tuple(neighborBox))

        return neighbor_list


