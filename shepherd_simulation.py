#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Main file implementing full simulation of shepherding with environment and its dog and sheep agents
   Based on: https://github.com/buntyke/shepherd_gym
"""
import argparse
import warnings

import matplotlib
import matplotlib.pyplot as plt
import numpy as np

from fuzzy_dog import get_fuzzy_system
from helper import plot_driving_collecting_progress, plot_driving_collecting_bar

# Following line is needed to get an updated graphic plot of the env.
# Important: Comment this line out if run on server without frontend!
matplotlib.use("TkAgg")

# suppress runtime warnings
warnings.filterwarnings("ignore")


class ShepherdSimulation:
    genVideo = False

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
        self.init_sheep_pose = np.random.uniform(
            0, self.field_length // 2, size=(self.num_sheep_total, 2)) + field_center
        self.sheep_poses = self.init_sheep_pose
        self.vis_sheep_poses = self.sheep_poses
        self.sheep_com = self.sheep_poses.mean(axis=0)

        self.sheep_radius = 2

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
        self.driving_counter = [0]
        self.video_counter = 0

    def success_criteria(self):
        """
        Function to determine the success of the simulation (to be modified)
        :return: Success or not
        """
        return np.linalg.norm(self.target - self.sheep_com) < 5.0

    def run(self, render=False, verbose=False):
        """
        main function to perform the simulation loop
        :param render: argument specifying if the environment shall be plotted
        :param verbose: Output verbose information during the run
        :return: counter, success: specifying if simulation successful and how long it took.
        """
        # start the simulation
        if verbose:
            print('Start simulation')

        # initialize matplotlib figure
        if render:
            # Init plot - 1 figure for the gamefield and 3 for the fuzzy memberships.
            fuzzy_rows = 1
            fuzzy_cols = 4
            plt.subplots(fuzzy_rows, fuzzy_cols, figsize=(fuzzy_cols * 5, fuzzy_rows * 5),
                         gridspec_kw={'width_ratios': [2, 1, 1, 1], 'wspace': 0.5})
            plt.ion()
            if not ShepherdSimulation.genVideo:
                plt.show()

        # main loop for simulation
        while not self.success_criteria() and self.counter < self.max_steps:
            # update counter variable
            self.counter += 1

            # get the new dog position
            # self.dog_heuristic_model()
            # self.dog_strombom_model(self.vis_sheep_poses)
            self.dog_fuzzy_model(self.vis_sheep_poses, verbose=verbose, render=render)

            # find new inertia
            self.update_environment()
            # Update the list of visible sheep
            self.vis_sheep_poses = self.get_visible_sheep(self.sheep_poses, self.dog_pose, self.sheep_radius)

            # plot every 5th frame, export every frame if making a video
            if (render and self.counter % 5 == 0) or ShepherdSimulation.genVideo:
                self.plot_env()

        success = False
        if self.success_criteria():
            success = True
        # complete execution
        if verbose:
            print('Finish simulation')

        if render:
            plot_driving_collecting_bar(self.driving_counter)
            plot_driving_collecting_progress(self.driving_counter)

        return self.counter, success

    def plot_env(self):
        # The first subplot is the plot for our simulation.
        ax = plt.subplot(141)  # 1 row, 4 cols and we select the 1. subplot (most left)
        ax.clear()
        plt.scatter(self.target[0], self.target[1],
                    c='orange', s=40, label='Goal')
        plt.scatter(
            self.dog_pose[0], self.dog_pose[1], c='r', s=50, label='Dog')
        vis_sheep = self.vis_sheep_poses
        other_sheep = np.asarray([i for i in self.sheep_poses if i not in vis_sheep])
        if len(other_sheep) > 0:
            plt.scatter(
                other_sheep[:, 0], other_sheep[:, 1], c='b', s=50, label='Not visible Sheep')
        plt.scatter(
            vis_sheep[:, 0], vis_sheep[:, 1], c='g', s=50, label='Visible Sheep')
        plt.title('Shepherding (N=' + str(self.num_sheep_total) + ', n=' + str(self.num_sheep_neighbors) + ')')
        border = 20
        plt.xlim([0 - border, self.field_length + border])
        plt.ylim([0 - border, self.field_length + border])
        plt.legend()
        if not ShepherdSimulation.genVideo:
            plt.pause(0.01)

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
                                  + np.sum(self.sheep_poses[indices, :] ** 2, axis=1)
                                  + np.sum(self.sheep_poses[indices, :] ** 2, axis=1)[:, np.newaxis])

        # find the sheep which are within sheep repulsion distance between each other
        xvals, yvals = np.where(
            (distance_matrix < self.sheep_repulsion_dist) & (distance_matrix != 0))
        # list of interacting sheep id pairs (both ways included - i.e. [1,2] & [2,1])
        interact = np.hstack((xvals[:, None], yvals[:, None]))

        # compute the repulsion forces within sheep
        repulsion_sheep = np.zeros((num_near_sheep, 2))

        for val in range(num_near_sheep):
            iv = interact[interact[:, 0] == val, 1]
            transit = self.sheep_poses[val, :][None, :] - self.sheep_poses[iv, :]
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
        sheep_neighbors = np.argsort(distance_matrix, axis=1)[:, 0:self.num_sheep_neighbors + 1]
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
    def dog_strombom_model(self, sheep_poses):

        # check if a sheep is closer than r_a to dog, if yes stop walking
        dist_sheep_dog = np.linalg.norm(
            sheep_poses - self.dog_pose, axis=1)
        if np.min(dist_sheep_dog) < 3 * self.sheep_repulsion_dist:
            self.dog_pose = self.dog_pose
            return

        # check if sheep are within field
        field = self.sheep_repulsion_dist * (self.num_sheep_total ** (2 / 3))
        dist_to_com = np.linalg.norm(
            (sheep_poses - self.sheep_com[None, :]), axis=1)

        is_within_field = False
        if np.max(dist_to_com) < field:
            is_within_field = True

        # determine the dog position
        if is_within_field:
            # perform herding

            # compute driving Point
            direction = self.sheep_com - self.target
            direction /= np.linalg.norm(direction)

            factor = self.sheep_repulsion_dist * (np.sqrt(self.num_sheep_total))

            # get intermediate collecting goal; P_d
            int_goal = self.sheep_com + (direction * factor)

            self.driving_counter.append(self.driving_counter[-1] + 1)

        else:
            # perform collecting

            # get the farthest sheep
            dist_to_com = np.linalg.norm(
                (sheep_poses - self.sheep_com[None, :]), axis=1)
            farthest_sheep = sheep_poses[np.argmax(dist_to_com), :]

            # compute the direction
            direction = (farthest_sheep - self.sheep_com)
            direction /= np.linalg.norm(direction)

            # compute the distance factor
            factor = self.sheep_repulsion_dist

            # get intermediate collecting goal; P_c
            int_goal = farthest_sheep + (direction * factor)

            self.driving_counter.append(self.driving_counter[-1])

        # compute increments in x,y components
        direction = int_goal - self.dog_pose
        direction /= np.linalg.norm(direction)

        # error term
        noise = np.random.randn(2)
        noise /= np.linalg.norm(noise, keepdims=True)

        # update position
        self.dog_pose = self.dog_pose + self.dog_speed * direction + self.noise_term * noise

    def dog_fuzzy_model(self, sheep_poses, render=False, verbose=False):
        """
        Dog decides between driving and collecting using Fuzzy Logic
        :return:
        """
        # Calculate sheep_com of visible sheeps
        sheep_com = np.mean(sheep_poses, axis=0)
        # check if a sheep is closer than r_a to dog, if yes stop walking
        dist_sheep_dog = np.linalg.norm(
            sheep_poses - self.dog_pose, axis=1)
        if np.min(dist_sheep_dog) < 3 * self.sheep_repulsion_dist:
            self.dog_pose = self.dog_pose
            return

        # decision parameter
        # calculate distance to driving point
        direction = sheep_com - self.target
        direction /= np.linalg.norm(direction)

        factor = self.sheep_repulsion_dist * (np.sqrt(self.num_sheep_total))

        P_d = sheep_com + (direction * factor)
        distance_P_d = np.linalg.norm(P_d - self.dog_pose)

        # calculate distance of initial sheep position to target
        initial_distance_target = np.linalg.norm(self.target - self.init_sheep_pose)

        t_min = np.linalg.norm(self.target - self.dog_pose) / self.dog_speed

        # average distance of sheep to com
        dist_to_com = np.linalg.norm(
            (sheep_poses - sheep_com[None, :]), axis=1)
        avg_dist_to_com = np.mean(dist_to_com)

        FS = get_fuzzy_system(self.counter, t_min, self.max_steps, avg_dist_to_com, distance_P_d,
                              initial_distance_target)

        # Distance of farthest sheep to center of mass
        farthest_sheep = sheep_poses[np.argmax(dist_to_com), :]
        dist_farthest_sheep_com = np.linalg.norm(farthest_sheep - sheep_com)
        FS.set_variable("Distance_runaway", dist_farthest_sheep_com)

        # Distance of dog to potential collecting point
        # compute the direction
        direction = (farthest_sheep - sheep_com)
        direction /= np.linalg.norm(direction)
        # compute the distance factor
        factor = self.sheep_repulsion_dist
        # P_c: temporary collecting target
        P_c = farthest_sheep + (direction * factor)
        distance_dog_P_c = np.linalg.norm(P_c - self.dog_pose)
        FS.set_variable("Distance_collecting_point", distance_dog_P_c)

        # distance to the final target
        dist_final_target = np.linalg.norm(self.target - sheep_com)
        FS.set_variable("Distance_final_target", dist_final_target)

        driving = False
        alpha = 0.3
        crisp_decision_value = FS.Mamdani_inference(['Decision'], ignore_warnings=True)['Decision']
        if crisp_decision_value < alpha:
            driving = True

        if verbose:
            # print decision
            print(f"Firing strengths: {FS.get_firing_strengths()}")
            print(f"Decision: {crisp_decision_value}, {driving}")
        if (render and self.counter % 10 == 0) or ShepherdSimulation.genVideo:
            self.plot_fuzzy_variables(FS, crisp_decision_value, dist_farthest_sheep_com, distance_dog_P_c)

        # quick fix for the special case when only one sheep is visible
        if len(sheep_poses) == 1:
            driving = True
        # determine the dog position
        if driving:
            # perform driving
            # get intermediate collecting goal; P_d
            int_goal = P_d
            self.driving_counter.append(self.driving_counter[-1] + 1)

        else:
            # perform collecting
            # get intermediate collecting goal; P_c
            int_goal = P_c
            self.driving_counter.append(self.driving_counter[-1])

        # compute increments in x,y components
        direction = int_goal - self.dog_pose
        direction /= np.linalg.norm(direction)

        # error term
        noise = np.random.randn(2)
        noise /= np.linalg.norm(noise, keepdims=True)

        # update position
        self.dog_pose = self.dog_pose + self.dog_speed * direction + self.noise_term * noise

    def plot_fuzzy_variables(self, FS, crisp_decision_value, dist_farthest_sheep_com, distance_dog_P_c):
        """
        Print the different linguistic variables, including the final decision
        :param FS: Fuzzy system used for inference
        :param crisp_decision_value: Crisp decision value (range[0,1]) resulting from inference
        :param dist_farthest_sheep_com: distance between farthest sheep and the sheep com
        :param distance_dog_P_c: distance between the shepherd and the collecting point
        :return:
        """
        # Plot Distance_runaway
        ax = plt.subplot(142)
        ax.clear()
        FS._lvs["Distance_runaway"].draw(ax, TGT=dist_farthest_sheep_com)

        # Plot Distance collecting point
        ax = plt.subplot(143)
        ax.clear()
        FS._lvs["Distance_collecting_point"].draw(ax, TGT=distance_dog_P_c)

        # Plot Distance collecting point
        ax = plt.subplot(144)
        ax.clear()
        FS._lvs["Decision"].draw(ax, TGT=crisp_decision_value)

        # Draw the resulting plot
        if not ShepherdSimulation.genVideo:
            plt.pause(0.01)
        else:
            # Save every plot as a figure.
            plt.savefig("video/file%04d.png" % self.video_counter)
            self.video_counter += 1
            # For video creation: Execute this command in linux:
            # ffmpeg -framerate 5 -i file%03d.png -pattern_type sequence video.mp4
            # This will generate a video of all the figures/images. Attention: The ids have to be subsequent!
            # Check if any subsequent id is missing.

    @staticmethod
    def get_visible_sheep(sheep_poses, dog_pose, sheep_radius):
        """
        Calculates the sheeps the dog can actually see
        :return:
        """
        # 1. Remove sheeps which are not in the field of view of the dog
        # sheep poses: self.sheep_poses
        # dog pose: self.dog_pose [= np.array([0, 0])]
        # TBD: need vector in a specific direction to compute it
        # Vector3 toSc = sc.transform.position - dc.transform.position;
        # float cos = Vector3.Dot(dc.transform.forward, toSc.normalized);
        # return cos > Mathf.Cos((180f - blindAngle / 2f) * Mathf.Deg2Rad);

        # 2. Remove sheep which are occluded by other sheep
        # Calculate distance of sheep to dog
        dist_sheep_dog = np.linalg.norm(
            sheep_poses - dog_pose, axis=1)
        # Sort sheep by their distances
        sheep_pos_sorted = [x for _, x in sorted(zip(dist_sheep_dog, sheep_poses))]

        # Iterate over every sheep, calculate the line between the sheep and the dog & save the line.
        # In the next step, check if a sheep collides with the line
        visible_sheep_positions = list()
        for i in range(len(sheep_pos_sorted)):
            sheep_pos = sheep_pos_sorted[i]
            # Check if sheep collides with previous sheep
            occluded = False
            for vis_sheep_pos in visible_sheep_positions:
                # distance between sheep and the line formed by the visible sheep and the dog
                p1 = dog_pose
                p2 = vis_sheep_pos
                p3 = sheep_pos
                distance = np.linalg.norm(np.cross(p2 - p1, p1 - p3)) / np.linalg.norm(p2 - p1)
                # Check if the distance is smaller than the radius of one sheep
                if distance < sheep_radius:
                    occluded = True
                    break
            if occluded:
                continue
            # sheep is not occluded by other sheep, add to visible sheep list
            visible_sheep_positions.append(sheep_pos)
        return np.asarray(visible_sheep_positions)


def get_args():
    parser = argparse.ArgumentParser(description='Run the Strömbom simulation with fuzzy logic')
    parser.add_argument('num_sheep', metavar='N', nargs='?', type=int, default=30, help='Total number of sheep')
    parser.add_argument('num_neighbors', metavar='n', nargs='?', type=int, default=20,
                        help='Number of neighbors sheep take into account')
    parser.add_argument('max_steps', type=int, nargs='?', default=8000,
                        help='Max number of steps to run the simulation')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Print verbose informations')
    parser.add_argument('-nr', '--no-render', action='store_true',
                        help='Toggle if the simulation shall be run with visualization')
    parser.add_argument('-vi', '--video', action='store_true',
                        help='Toggle to enable exporting of every frame into a folder "/video",'
                             ' to create a video with ffmpeg afterwards.')

    return parser.parse_args()


def main():
    args = get_args()
    ShepherdSimulation.genVideo = args.video
    shepherd_sim = ShepherdSimulation(
        num_sheep_total=args.num_sheep, num_sheep_neighbors=args.num_neighbors, max_steps=args.max_steps)
    shepherd_sim.run(render=not args.no_render, verbose=args.verbose)


if __name__ == '__main__':
    main()
