#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Main file implementing full simulation of shepherding with environment and its dog and sheep agents
   Based on: https://github.com/buntyke/shepherd_gym
"""

# suppress runtime warnings
import warnings

warnings.filterwarnings("ignore")

# import libraries
import numpy as np
import matplotlib.pyplot as plt


# class implementation of shepherding
class ShepherdSimulation:

    def __init__(self, num_sheep=25, init_radius=100):

        # radius for sheep to be considered as collected by dog
        self.dog_collect_radius = 2.0

        # weight multipliers for sheep forces
        self.lcm_term = 1.05  # relative strength of attraction to the n nearest neighbors
        self.noise_term = 0.3
        self.inertia_term = 0.5
        self.repulsion_dog_term = 1.0
        self.repulsion_sheep_term = 2.0

        ## constants used to update environment
        # delta [m ts^(-1) ???] agent displacement per time step
        self.delta_sheep_pose = 1.0
        # r_s [m] shepherd detection distance
        self.dog_repulsion_dist = 70.0
        # r_a [m] agent to agent interaction distance
        self.sheep_repulsion_dist = 2.0

        # total number of sheep, N
        self.num_sheep = num_sheep

        # number of nearest neighbors (for LCM), n
        self.num_sheep_neighbors = int(self.num_sheep / 2)

        # initialize target position
        self.target = np.array([0, 0])

        # initialize sheep positions
        init_sheep_pose = np.random.uniform(-200.0, 200.0, size=(2))
        self.sheep_poses = (np.random.uniform(-50.0, 50.0, size=(self.num_sheep, 2))) \
                           + init_sheep_pose[None, :]
        self.sheep_com = self.sheep_poses.mean(axis=0)

        # initialize dog position
        init_dog_pose = init_sheep_pose + 75.0 * (2 * np.random.randint(2, size=(2)) - 1)
        self.dog_pose = init_dog_pose

        # initialize dog displacement per time step (speed, delta_s)
        self.dog_speed = 1.5

        # initialize inertia
        self.inertia = np.ones((self.num_sheep, 2))

        # initialize maximum number of steps
        self.max_steps = 1500

    # main function to perform simulation
    def run(self, render=False):

        # start the simulation
        print('Start simulation')

        # initialize counter for plotting
        counter = 0

        # initialize matplotlib figure
        if render:
            plt.figure()
            plt.ion()
            plt.show()

        # main loop for simulation
        while np.linalg.norm(self.target - self.sheep_com) > 1.0 and counter < self.max_steps:
            # update counter variable
            counter += 1

            # get the new dog position
            #self.dog_heuristic_model()
            self.dog_strombom_model()

            # find new inertia
            self.update_environment()

            # plot every 5th frame
            if counter % 5 == 0 and render:
                plt.clf()

                plt.scatter(self.target[0], self.target[1], c='g', s=40, label='Goal')
                plt.scatter(self.dog_pose[0], self.dog_pose[1], c='r', s=50, label='Dog')
                plt.scatter(self.sheep_poses[:, 0], self.sheep_poses[:, 1], c='b', s=50, label='Sheep')

                plt.title('Shepherding')
                plt.xlim([-300, 300])
                plt.ylim([-300, 300])
                plt.legend()
                plt.draw()
                plt.pause(0.01)

        # complete execution
        print('Finish simulation')

    # function to find new inertia for sheep
    def update_environment(self):
        # compute a distance matrix
        distance_matrix = np.zeros((self.num_sheep, self.num_sheep))
        for i in range(self.num_sheep):
            for j in range(i):
                dist = np.linalg.norm(self.sheep_poses[i, :] - self.sheep_poses[j, :])
                distance_matrix[i, j] = dist
                distance_matrix[j, i] = dist

        # find the sheep which are within sheep repulsion distance between each other
        xvals, yvals = np.where((distance_matrix < self.sheep_repulsion_dist) & (distance_matrix != 0))
        # list of interacting sheep id pairs (both ways included - i.e. [1,2] & [2,1])
        interact = np.hstack((xvals[:, None], yvals[:, None]))

        # compute the repulsion forces within sheep
        repulsion_sheep = np.zeros((self.num_sheep, 2))

        for val in range(self.num_sheep):
            iv = interact[interact[:, 0] == val, 1]
            transit = self.sheep_poses[val, :][None, :] - self.sheep_poses[iv, :]
            transit /= np.linalg.norm(transit, axis=1, keepdims=True)
            repulsion_sheep[val, :] = np.sum(transit, axis=0)

        repulsion_sheep /= np.linalg.norm(repulsion_sheep, axis=1, keepdims=True)
        repulsion_sheep[np.isnan(repulsion_sheep)] = 0

        # find sheep near dog
        dist_to_dog = np.linalg.norm((self.sheep_poses - self.dog_pose[None, :]), axis=1)
        sheep_inds = np.where(dist_to_dog < self.dog_repulsion_dist)
        sheep_near_dog = sheep_inds[0]

        # repulsion from dog
        repulsion_dog = np.zeros((self.num_sheep, 2))
        repulsion_dog[sheep_near_dog, :] = self.sheep_poses[sheep_near_dog, :] - self.dog_pose[None, :]
        repulsion_dog /= np.linalg.norm(repulsion_dog, axis=1, keepdims=True)
        repulsion_dog[np.isnan(repulsion_dog)] = 0

        # attraction to LCMs
        sheep_neighbors = np.argsort(distance_matrix, axis=1)[:, 0:self.num_sheep_neighbors + 1]
        sheep_lcms = np.zeros((self.num_sheep, 2))

        for i in range(self.num_sheep):
            sheep_lcms[i, :] = self.sheep_poses[sheep_neighbors[i]].mean(axis=0)

        attraction_lcm = np.zeros((self.num_sheep, 2))
        attraction_lcm[sheep_near_dog, :] = sheep_lcms[sheep_near_dog, :] - self.sheep_poses[sheep_near_dog, :]
        attraction_lcm /= np.linalg.norm(attraction_lcm, axis=1, keepdims=True)
        attraction_lcm[np.isnan(attraction_lcm)] = 0

        # error term
        noise = np.random.randn(self.num_sheep, 2)
        noise /= np.linalg.norm(noise, axis=1, keepdims=True)

        # compute sheep motion direction
        self.inertia = self.inertia_term * self.inertia + self.lcm_term * attraction_lcm + \
                       self.repulsion_sheep_term * repulsion_sheep + self.repulsion_dog_term * repulsion_dog + \
                       self.noise_term * noise

        # normalize the inertia terms
        self.inertia /= np.linalg.norm(self.inertia, axis=1, keepdims=True)
        self.inertia[np.isnan(self.inertia)] = 0

        # find new sheep position
        self.sheep_poses += self.delta_sheep_pose * self.inertia
        self.sheep_com = np.mean(self.sheep_poses, axis=0)

    # function to get new position of dog
    def dog_heuristic_model(self):

        # check if sheep are within field
        field = self.dog_collect_radius * (self.num_sheep ** (2 / 3))
        dist_to_com = np.linalg.norm((self.sheep_poses - self.sheep_com[None, :]), axis=1)

        is_within_field = False
        if np.max(dist_to_com) < field:
            is_within_field = True

        # determine the dog position
        if is_within_field:
            # perform herding

            # compute the direction
            direction = (self.sheep_com - self.target)
            direction /= np.linalg.norm(direction)

            # compute the factor
            factor = self.dog_collect_radius * (np.sqrt(self.num_sheep))

            # get intermediate herding goal
            int_goal = self.sheep_com + (direction * factor)
        else:
            # perform collecting

            # get the farthest sheep
            dist_to_com = np.linalg.norm((self.sheep_poses - self.sheep_com[None, :]), axis=1)
            farthest_sheep = self.sheep_poses[np.argmax(dist_to_com), :]

            # compute the direction
            direction = (farthest_sheep - self.sheep_com)
            direction /= np.linalg.norm(direction)

            # compute the distance factor
            factor = self.dog_collect_radius

            # get intermediate collecting goal
            int_goal = farthest_sheep + (direction * factor)

        # find distances of dog to sheep
        dist_to_dog = np.linalg.norm((self.sheep_poses - self.dog_pose[None, :]), axis=1)

        # compute increments in x,y components
        direction = int_goal - self.dog_pose
        direction /= np.linalg.norm(direction)

        # discretize actions
        theta = np.arctan2(direction[1], direction[0]) * 180 / np.pi

        increment = np.array([0.0, 0.0])

        if theta <= 22.5 and theta >= -22.5:
            increment = np.array([1.5, 0.0])
        elif theta <= 67.5 and theta > 22.5:
            increment = np.array([1.225, 1.225])
        elif theta <= 112.5 and theta > 67.5:
            increment = np.array([0.0, 1.5])
        elif theta <= 157.5 and theta > 112.5:
            increment = np.array([-1.225, 1.225])
        elif theta < -157.5 or theta > 157.5:
            increment = np.array([-1.5, 0.0])
        elif theta >= -157.5 and theta < -112.5:
            increment = np.array([-1.225, -1.225])
        elif theta >= -112.5 and theta < -67.5:
            increment = np.array([0.0, -1.5])
        elif theta >= -67.5 and theta < -22.5:
            increment = np.array([1.225, -1.225])
        else:
            print('Error!')
        print(increment)

        # update position
        self.dog_pose = self.dog_pose + increment

    # function to get new position of dog according to model presented in paper by Strombom et al.
    def dog_strombom_model(self):

        # check if a sheep is closer than r_a to dog, if yes stop walking
        dist_sheep_dog = np.linalg.norm(self.sheep_poses - self.dog_pose, axis=1)
        if np.max(dist_sheep_dog) < 3 * self.sheep_repulsion_dist:
            self.dog_pose = self.dog_pose
            return

        # check if sheep are within field
        field = self.sheep_repulsion_dist * (self.num_sheep ** (2 / 3))
        dist_to_com = np.linalg.norm((self.sheep_poses - self.sheep_com[None, :]), axis=1)

        is_within_field = False
        if np.max(dist_to_com) < field:
            is_within_field = True

        # determine the dog position
        if is_within_field:
            # perform herding

            # compute driving Point
            P_d = self.sheep_com + np.linalg.norm(self.sheep_com - self.target)*self.sheep_repulsion_dist*(np.sqrt(self.num_sheep))
            dog_driving_direction = P_d - self.dog_pose

            int_goal = P_d

        else:
            # perform collecting

            # get the farthest sheep
            dist_to_com = np.linalg.norm((self.sheep_poses - self.sheep_com[None, :]), axis=1)
            farthest_sheep = self.sheep_poses[np.argmax(dist_to_com), :]

            # compute the direction
            direction = (farthest_sheep - self.sheep_com)
            direction /= np.linalg.norm(direction)

            # compute the distance factor
            factor = self.sheep_repulsion_dist

            # get intermediate collecting goal; P_c
            int_goal = farthest_sheep + (direction * factor)

        # compute increments in x,y components
        direction = int_goal - self.dog_pose
        direction /= np.linalg.norm(direction)

        # update position
        # ToDo: add noise
        self.dog_pose = self.dog_pose + self.dog_speed*direction


def main():
    shepherd_sim = ShepherdSimulation()
    shepherd_sim.run(render=True)


if __name__ == '__main__':
    main()
