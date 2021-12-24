#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Main file implementing full simulation of shepherding with environment and its dog and sheep agents
   Based on: https://github.com/buntyke/shepherd_gym
"""

import matplotlib.pyplot as plt
import numpy as np
import warnings
from utils import get_degree_between_3_points

# suppress runtime warnings
warnings.filterwarnings("ignore")


# class implementation of shepherding

class Decision_type:
    SIGMOID = "sigmoid"
    DEFAULT_STROMBOM = "default_strombom"


class ShepherdSimulation:

    def __init__(self, num_sheep_total=30, num_sheep_neighbors=15, decision_type=Decision_type.DEFAULT_STROMBOM):

        #initialize random state
        self.random_state = np.random.RandomState(num_sheep_total*num_sheep_neighbors)

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
        init_sheep_pose = self.random_state.uniform(
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
        self.max_steps = 1000

        self.decision_type = decision_type
        # field threshold params (for driving/collecting decision) for default strombom decision
        self.thresh_alpha = 1
        self.thresh_beta = 2 / 3
        self.thresh_gamma = 0

        # field threshold params (for driving/collecting decision) for sigmoid decision decision
        self.thresh_N = 0
        self.thresh_n = 0
        self.thresh_furthest = 0
        self.thresh_variance = 0
        self.thresh_angle = 0



    # main function to perform simulation
    def run(self, render=False, verbose=False):

        # start the simulation
        if verbose:
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
            # self.dog_heuristic_model()
            self.dog_strombom_model()

            # find new inertia
            self.update_environment()

            # plot every 5th frame
            if counter % 5 == 0 and render:
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

        # complete execution
        if verbose:
            print('Finish simulation')
        return counter, self.sheep_poses

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
        moving_sheep = self.random_state.choice([True, False], num_far_sheep, p=[
            self.grazing_prob, 1 - self.grazing_prob])
        inertia_sheep_far_dog[moving_sheep, :] = self.random_state.randn(
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
                                  + np.sum(self.sheep_poses[indices, :] ** 2, axis=1) + np.sum(
            self.sheep_poses[indices, :] ** 2, axis=1)[:,
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
        noise = self.random_state.randn(num_near_sheep, 2)
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

        # determine the dog position
        if self.__decision_fuction() == 0:
            # perform herding

            int_goal = self.__get_driving_point()

        else:  # decision function return 1
            # perform collecting

            int_goal = self.__get_collecting_point()

        # compute increments in x,y components
        direction = int_goal - self.dog_pose
        direction /= np.linalg.norm(direction)

        # error term
        inds_sheep_near_dog = dist_sheep_dog < self.dog_repulsion_dist
        inertia_sheep_near_dog = self.inertia[inds_sheep_near_dog, :]
        num_near_sheep = len(inertia_sheep_near_dog)
        noise = self.random_state.randn(num_near_sheep, 2)
        noise /= np.linalg.norm(noise, axis=1, keepdims=True)

        # update position
        # ToDo: add noise
        self.dog_pose = self.dog_pose + self.dog_speed * direction

    def __get_collecting_point(self):
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
        return int_goal

    def __get_driving_point(self):
        # perform herding

        # compute driving Point
        direction = self.sheep_com - self.target
        direction /= np.linalg.norm(direction)

        factor = self.sheep_repulsion_dist * \
                 (np.sqrt(self.num_sheep_total))

        # get intermediate collecting goal; P_d
        int_goal = self.sheep_com + (direction * factor)
        return int_goal


    def __decision_func_default_strombom(self):
        # check if sheep are within field
        field = self.thresh_alpha * self.sheep_repulsion_dist * \
                (self.num_sheep_total ** self.thresh_beta) + self.thresh_gamma
        dist_to_com = np.linalg.norm(
            (self.sheep_poses - self.sheep_com[None, :]), axis=1)

        if np.max(dist_to_com) < field:
            return 0
        else:
            return 1

    def __decision_func_sigmoid(self):

        # get position of furthest sheep
        dist_to_com = np.linalg.norm(
            (self.sheep_poses - self.sheep_com[None, :]), axis=1)
        farthest_sheep = self.sheep_poses[np.argmax(dist_to_com), :]

        distance_to_furthest_sheep = np.linalg.norm(farthest_sheep - self.dog_pose)

        driving_point = self.__get_driving_point()

        collecting_point = self.__get_collecting_point()

        # angle between driving point, shepherd, collecting point
        angle = get_degree_between_3_points(driving_point, self.dog_pose, collecting_point)

        variance = np.var(dist_to_com)

        # params must be normalize
        # TODO: better than fixed normalized value
        norm_N = self.num_sheep_total / 140
        norm_n = self.num_sheep_neighbors / self.num_sheep_total
        norm_angle = angle / 180
        norm_dist_to_fur_sheep = distance_to_furthest_sheep / 150 if distance_to_furthest_sheep / 150 < 1 else 1
        norm_variance = variance / 200 if variance / 200 < 1 else 1


        g = self.thresh_N * norm_N + self.thresh_n * norm_n + self.thresh_variance * norm_variance + self.thresh_furthest * norm_dist_to_fur_sheep + self.thresh_angle * norm_angle
        sigmoid = 1 / (1 + np.exp(-g))

        if sigmoid <= 0.5:
            return 0
        else:
            return 1

    def __decision_fuction(self):
        if self.decision_type == Decision_type.DEFAULT_STROMBOM:
            return self.__decision_func_default_strombom()
        elif self.decision_type == Decision_type.SIGMOID:
            return self.__decision_func_sigmoid()
        else:
            raise Exception("invalid decision type")

    # set parameters related to field threshold calculation (used for genetic algorithm)
    def set_thresh_field_params(self, decision_params):
        if self.decision_type == Decision_type.DEFAULT_STROMBOM:
            alpha, beta, gamma = decision_params
            self.thresh_alpha = alpha
            self.thresh_beta = beta
            self.thresh_gamma = gamma

        elif self.decision_type == Decision_type.SIGMOID:
            thresh_N, thresh_n, thresh_furthest, thresh_variance, thresh_angle = decision_params
            self.thresh_N = thresh_N
            self.thresh_n = thresh_n
            self.thresh_furthest = thresh_furthest
            self.thresh_variance = thresh_variance
            self.thresh_angle = thresh_angle
        else:
            raise Exception("decision type is not valid")


def main():
    shepherd_sim = ShepherdSimulation(
        num_sheep_total=50, num_sheep_neighbors=50)
    shepherd_sim.run(render=True, verbose=True)


if __name__ == '__main__':
    main()
