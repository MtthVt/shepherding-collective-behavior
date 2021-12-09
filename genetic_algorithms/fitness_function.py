import numpy as np
from genetic_algorithms.shepherd_simulation import ShepherdSimulation

STEP_BETWEEN_SIMULATIONS_FOR_N_AND_n = 16


def simulation_count():
    """Compute number of simulation in fitness function"""
    counter = 0
    for N in range(30, 140, STEP_BETWEEN_SIMULATIONS_FOR_N_AND_n):
        for n in range(int(np.floor(3 * np.log2(N))), int(np.ceil(0.53 * N)), STEP_BETWEEN_SIMULATIONS_FOR_N_AND_n):
            counter += 1
    return counter


def fitness_func_single_sim(solution, num_sheep_total, num_sheep_neighbors, sim_count):
    """Return the score of provided solution for certain total and neighbor numbers of sheep
    Is based on running shepherd simulation
    """
    sim = ShepherdSimulation(
        num_sheep_total=num_sheep_total, num_sheep_neighbors=num_sheep_neighbors)
    sim.set_thresh_field_params(*solution)

    t_steps, sheep_poses = sim.run()

    target = sim.target
    sheep_target_dists = np.linalg.norm(sheep_poses - target, axis=1)

    # score calculation - to be specified
    score = t_steps
    if t_steps >= sim.max_steps:
        score = sim.max_steps * sim_count + np.sum(sheep_target_dists)
    return score


def fitness_func(solution, solution_idx):
    """Returns the score of provided solution
    To be used in PyGAD, needs to be maximization function
    """
    scores = []
    sim_count = simulation_count()
    for N in range(30, 140, STEP_BETWEEN_SIMULATIONS_FOR_N_AND_n):
        for n in range(int(np.floor(3 * np.log2(N))), int(np.ceil(0.53 * N)), STEP_BETWEEN_SIMULATIONS_FOR_N_AND_n):
            sc = fitness_func_single_sim(solution, N, n, sim_count)
            scores.append(sc)

    # score calculation - to be specified
    total_score = np.sum(scores)
    print('Total score', 1 / total_score)
    return 1 / total_score
