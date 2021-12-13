#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Main file implementing full simulation of shepherding with environment and its dog and sheep agents
   Based on: https://github.com/buntyke/shepherd_gym
"""

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import warnings
from simpful import *
from fuzzy_dog import get_fuzzy_system

# Following line is needed to get an updated graphic plot of the env.
matplotlib.use("TkAgg")

# suppress runtime warnings
warnings.filterwarnings("ignore")

# class implementation of shepherding


class ShepherdSimulation:

    def __init__(self, num_sheep_total=30, num_sheep_neighbors=15, max_steps=1500):

        # radius for sheep to be considered as collected by dog
        self.dog_collect_radius = 2.0

        # weight multipliers for sheep forces
        self.lcm_term = 1.05  # relative strength of attraction to the n nearest neighbors, c
        self.noise_term = 0.3  # relative strength of angular noise, e
        self.inertia_term = 0.5  # relative strength of proceeding in the previous direction, h
        self.repulsion_dog_term = 1.0  # relative strength of repulsion from the shepherd
        self.repulsion_sheep_term = 2.0  # relative strength of repulsion from other agents
        self.grazing_prob = 0.05  # probability of moving per time step while grazing

        # constants used to update environment
        # delta [m ts^(-1) ???] agent displacement per time step
        self.delta_sheep_pose = 1.0
        # r_s [m] shepherd detection distance
        self.dog_repulsion_dist = 65.0
        # r_a [m] agent to agent interaction distance
        self.sheep_repulsion_dist = 2.0

        # total number of sheep, N
        self.num_sheep_total = num_sheep_total

        # length of field size, L
        self.field_length = 150

        # number of nearest neighbors (for LCM), n
        self.num_sheep_neighbors = num_sheep_neighbors

        # initialize target position
        self.target = np.array([3, 3])

        # initialize sheep positions
        field_center = np.array(
            [self.field_length // 2, self.field_length // 2])
        init_sheep_pose = np.random.uniform(
            0, self.field_length // 2, size=(self.num_sheep_total, 2)) + field_center
        self.sheep_poses = init_sheep_pose
        self.sheep_com = self.sheep_poses.mean(axis=0)

        # initialize dog position
        init_dog_pose = np.array([0, 0])
        self.dog_pose = init_dog_pose

        # initialize dog displacement per time step (speed, delta_s)
        self.dog_speed = 1.5

        # initialize inertia
        self.inertia = np.ones((self.num_sheep_total, 2))

        # initialize maximum number of steps
        self.max_steps = max_steps

        # number of executed steps
        self.counter = 0


    def success_criteria(self):
        """
        Function to determine the success of the simulation (to be modified)
        :return: Success or not
        """
        return np.linalg.norm(self.target - self.sheep_com) < 1.0

    # main function to perform simulation
    def run(self, render=False, verbose=False):

        # start the simulation
        if verbose:
            print('Start simulation')

        # initialize matplotlib figure
        if render:
            plt.figure()
            plt.ion()
            plt.show()

        # main loop for simulation
        while not self.success_criteria() and self.counter < self.max_steps:
            # update counter variable
            self.counter += 1

            # get the new dog position
            # self.dog_heuristic_model()
            # self.dog_strombom_model()
            self.dog_fuzzy_model(verbose=verbose)

            # find new inertia
            self.update_environment()

            # plot every 5th frame
            if self.counter % 5 == 0 and render:
                plt.clf()

                plt.scatter(self.target[0], self.target[1],
                            c='g', s=40, label='Goal')
                plt.scatter(
                    self.dog_pose[0], self.dog_pose[1], c='r', s=50, label='Dog')
                plt.scatter(
                    self.sheep_poses[:, 0], self.sheep_poses[:, 1], c='b', s=50, label='Sheep')

                plt.title('Shepherding')
                border = 20
                plt.xlim([0 - border, self.field_length + border])
                plt.ylim([0 - border, self.field_length + border])
                plt.legend()
                plt.draw()
                plt.pause(0.01)

        success = False
        if self.success_criteria():
            success = True
        # complete execution
        if verbose:
            print('Finish simulation')
        return self.counter, success

    # function to find new inertia for sheep
    def update_environment(self):
        # find sheep near and far dog
        dist_to_dog = np.linalg.norm(
            (self.sheep_poses - self.dog_pose[None, :]), axis=1)

        inds_sheep_near_dog = dist_to_dog < self.dog_repulsion_dist
        self.__compute_inertia_for_sheep_near_from_dog(inds_sheep_near_dog)

        inds_sheep_far_dog = np.logical_not(inds_sheep_near_dog)
        self.__compute_inertia_for_sheep_far_from_dog(inds_sheep_far_dog)

        # find new sheep position
        self.sheep_poses += self.delta_sheep_pose * self.inertia
        self.sheep_com = np.mean(self.sheep_poses, axis=0)

    def __compute_inertia_for_sheep_far_from_dog(self, indices):
        inertia_sheep_far_dog = self.inertia[indices, :]
        num_far_sheep = len(inertia_sheep_far_dog)

        # compute random movements while grazing (with prob self.grazing_prob)
        inertia_sheep_far_dog = np.zeros(inertia_sheep_far_dog.shape)
        moving_sheep = np.random.choice([True, False], num_far_sheep, p=[
                                        self.grazing_prob, 1 - self.grazing_prob])
        inertia_sheep_far_dog[moving_sheep, :] = np.random.randn(
            inertia_sheep_far_dog[moving_sheep, :].shape[0], 2)
        inertia_sheep_far_dog[moving_sheep, :] = np.linalg.norm(inertia_sheep_far_dog[moving_sheep, :], axis=1,
                                                                keepdims=True)
        # update general inertia
        self.inertia[indices, :] = inertia_sheep_far_dog

    def __compute_inertia_for_sheep_near_from_dog(self, indices):
        inertia_sheep_near_dog = self.inertia[indices, :]
        num_near_sheep = len(inertia_sheep_near_dog)

        # compute a distance matrix
        distance_matrix = np.sqrt(-2 * np.dot(self.sheep_poses[indices, :], self.sheep_poses[indices, :].T)
                                  + np.sum(self.sheep_poses[indices, :] ** 2, axis=1) + np.sum(self.sheep_poses[indices, :] ** 2, axis=1)[:,
                                                                                                                                          np.newaxis])

        # find the sheep which are within sheep repulsion distance between each other
        xvals, yvals = np.where(
            (distance_matrix < self.sheep_repulsion_dist) & (distance_matrix != 0))
        # list of interacting sheep id pairs (both ways included - i.e. [1,2] & [2,1])
        interact = np.hstack((xvals[:, None], yvals[:, None]))

        # compute the repulsion forces within sheep
        repulsion_sheep = np.zeros((num_near_sheep, 2))

        for val in range(num_near_sheep):
            iv = interact[interact[:, 0] == val, 1]
            transit = self.sheep_poses[val, :][None,
                                               :] - self.sheep_poses[iv, :]
            transit /= np.linalg.norm(transit, axis=1, keepdims=True)
            repulsion_sheep[val, :] = np.sum(transit, axis=0)

        repulsion_sheep /= np.linalg.norm(repulsion_sheep,
                                          axis=1, keepdims=True)
        repulsion_sheep[np.isnan(repulsion_sheep)] = 0

        # repulsion from dog
        repulsion_dog = self.sheep_poses[indices, :] - self.dog_pose[None, :]
        repulsion_dog /= np.linalg.norm(repulsion_dog, axis=1, keepdims=True)
        repulsion_dog[np.isnan(repulsion_dog)] = 0

        # attraction to LCMs
        sheep_neighbors = np.argsort(distance_matrix, axis=1)[
            :, 0:self.num_sheep_neighbors + 1]
        sheep_lcms = np.zeros((num_near_sheep, 2))

        for i in range(num_near_sheep):
            sheep_lcms[i, :] = self.sheep_poses[sheep_neighbors[i]].mean(
                axis=0)

        attraction_lcm = sheep_lcms - self.sheep_poses[indices, :]
        attraction_lcm /= np.linalg.norm(attraction_lcm, axis=1, keepdims=True)
        attraction_lcm[np.isnan(attraction_lcm)] = 0

        # error term
        noise = np.random.randn(num_near_sheep, 2)
        noise /= np.linalg.norm(noise, axis=1, keepdims=True)

        # compute sheep motion direction
        inertia_sheep_near_dog = self.inertia_term * inertia_sheep_near_dog + self.lcm_term * attraction_lcm + \
            self.repulsion_sheep_term * repulsion_sheep + self.repulsion_dog_term * repulsion_dog + \
            self.noise_term * noise

        # normalize the inertia terms
        inertia_sheep_near_dog /= np.linalg.norm(
            inertia_sheep_near_dog, axis=1, keepdims=True)
        inertia_sheep_near_dog[np.isnan(inertia_sheep_near_dog)] = 0

        # update general inertia
        self.inertia[indices, :] = inertia_sheep_near_dog

    # function to get new position of dog according to model presented in paper by Strombom et al.
    def dog_strombom_model(self):

        # check if a sheep is closer than r_a to dog, if yes stop walking
        dist_sheep_dog = np.linalg.norm(
            self.sheep_poses - self.dog_pose, axis=1)
        if np.min(dist_sheep_dog) < 3 * self.sheep_repulsion_dist:
            self.dog_pose = self.dog_pose
            return

        # check if sheep are within field
        field = self.sheep_repulsion_dist * (self.num_sheep_total ** (2 / 3))
        dist_to_com = np.linalg.norm(
            (self.sheep_poses - self.sheep_com[None, :]), axis=1)

        is_within_field = False
        if np.max(dist_to_com) < field:
            is_within_field = True

        # determine the dog position
        if is_within_field:
            # perform herding

            # compute driving Point
            direction = self.sheep_com - self.target
            direction /= np.linalg.norm(direction)

            factor = self.sheep_repulsion_dist * \
                (np.sqrt(self.num_sheep_total))

            # get intermediate collecting goal; P_d
            int_goal = self.sheep_com + (direction * factor)

        else:
            # perform collecting

            # get the farthest sheep
            dist_to_com = np.linalg.norm(
                (self.sheep_poses - self.sheep_com[None, :]), axis=1)
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

        # error term
        noise = np.random.randn(2)
        noise /= np.linalg.norm(noise, keepdims=True)

        # update position
        self.dog_pose = self.dog_pose + self.dog_speed * direction + self.noise_term*noise

    def dog_fuzzy_model(self, verbose= False):
        """
        Dog decides between driving and collecting using Fuzzy Logic
        :return:
        """
        # check if a sheep is closer than r_a to dog, if yes stop walking
        dist_sheep_dog = np.linalg.norm(
            self.sheep_poses - self.dog_pose, axis=1)
        if np.min(dist_sheep_dog) < 3 * self.sheep_repulsion_dist:
            self.dog_pose = self.dog_pose
            return

        # decision parameter
        alpha = 0.3
        t_min = np.linalg.norm(self.target - self.dog_pose)
        FS = get_fuzzy_system(self.counter, t_min=t_min, num_sheep_total=self.num_sheep_total)
        FS.set_variable("Time", self.counter)

        # number of sheep in field
        field = self.sheep_repulsion_dist * (self.num_sheep_total ** (2 / 3))
        dist_to_com = np.linalg.norm(
            (self.sheep_poses - self.sheep_com[None, :]), axis=1)

        field_size = (dist_to_com < field).sum()
        FS.set_variable("Quantity", field_size)

        # distance to the target
        dist = np.linalg.norm(self.target - self.sheep_com)
        FS.set_variable("Distance", dist)

        driving = False
        crisp_decision_value = FS.Mamdani_inference(['Decision'])['Decision']
        if crisp_decision_value < alpha:
            driving = True

        if verbose:
            # plot membership functions
            FS.plot_variable("Time")
            FS.plot_variable("Quantity")
            FS.plot_variable("Distance")
            FS.plot_variable("Decision")
            print(f"Decision: {crisp_decision_value}, {driving}")

        # determine the dog position
        if driving:
            # perform driving

            # compute driving Point
            direction = self.sheep_com - self.target
            direction /= np.linalg.norm(direction)

            factor = self.sheep_repulsion_dist * \
                     (np.sqrt(self.num_sheep_total))

            # get intermediate collecting goal; P_d
            int_goal = self.sheep_com + (direction * factor)

        else:
            # perform collecting

            # get the farthest sheep
            dist_to_com = np.linalg.norm(
                (self.sheep_poses - self.sheep_com[None, :]), axis=1)
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

        # error term
        noise = np.random.randn(2)
        noise /= np.linalg.norm(noise, keepdims=True)

        # update position
        self.dog_pose = self.dog_pose + self.dog_speed * direction + self.noise_term * noise





def main():
    shepherd_sim = ShepherdSimulation(
        num_sheep_total=30, num_sheep_neighbors=15)
    shepherd_sim.run(render=True)


if __name__ == '__main__':
    main()
