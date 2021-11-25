"""Main file with functions required for performing genetic algorithm parameters exploration
"""
import numpy as np
import pygad
from shepherd_simulation import ShepherdSimulation


def fitness_func_single_sim(solution, num_sheep_total, num_sheep_neighbors):
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
        score += sim.max_steps * np.mean(sheep_target_dists)
    return score


def fitness_func(solution, solution_idx):
    """Returns the score of provided solution
    To be used in PyGAD, needs to be maximization function
    """
    scores = []
    for N in range(43, 45, 2):
        for n in range(int(np.floor(3*np.log2(N))), int(np.ceil(0.53*N))):
            print(N, n)
            sc = fitness_func_single_sim(solution, N, n)
            print(sc)
            scores.append(sc)

    # score calculation - to be specified
    total_score = np.sum(scores)
    print('Total score', 1 / total_score)
    return 1 / total_score


def on_generation(ga):
    print("Generation", ga.generations_completed)
    print(ga.population)


if __name__ == '__main__':
    # just an initial sketch, to verify & improve
    ga_instance = pygad.GA(num_generations=10, num_parents_mating=2, fitness_func=fitness_func, sol_per_pop=3, num_genes=3,
                           gene_type=float, init_range_low=-1, init_range_high=2, parent_selection_type='sss', keep_parents=-1, on_generation=on_generation)

    ga_instance.run()
    solution, solution_fitness, solution_idx = ga_instance.best_solution()
    print("Parameters of the best solution : {solution}".format(
        solution=solution))
    print("Fitness value of the best solution = {solution_fitness}".format(
        solution_fitness=solution_fitness))
