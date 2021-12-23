"""Main file with functions required for performing genetic algorithm parameters exploration
"""
import time
from os.path import isfile
from datetime import datetime
from multiprocessing import Pool, cpu_count
from timeit import default_timer as timer
from fitness_function import fitness_func_sigmoid, STEP_BETWEEN_SIMULATIONS_FOR_N_AND_n
from pooled_ga import PooledGA
import numpy as np
import pandas as pd


def create_log(Ns=(), ns=(), distances_fur=(),variances=(),angles=(), fitnesses=(), indices=(), generation=0, timestamp=time.time()):
    df = pd.DataFrame({'param_N': Ns,
                       'param_n': ns,
                       'param_fur': distances_fur,
                       'param_var': variances,
                       "param_angle": angles,
                       'fitness': fitnesses,
                       'index': indices,
                       })
    df['generation'] = generation
    df['timestamp'] = timestamp
    return df


def on_generation(ga):
    global last_timer
    global filepath
    global last_fitness

    Ns, ns, distances_fur, variances, angles = ga.population.T
    fitness = ga.last_generation_fitness
    indices = list(range(len(fitness)))
    generation = ga.generations_completed
    timestamp = time.time()

    if isfile(filepath):
        old_logs = pd.read_pickle(filepath)
    else:
        old_logs = create_log()
    new_logs = pd.concat([old_logs, create_log(
        Ns, ns, distances_fur, variances, angles, fitness, indices, generation, timestamp)])
    pd.to_pickle(new_logs, filepath)

    elapsed = round(timer() - last_timer, 2)
    last_timer = timer()
    print(f'Generation {ga.generations_completed} was completed in {elapsed}s')
    idx_best = np.argmax(fitness, axis=0)
    print(
        f'Best solution was {fitness[idx_best]} with parameters {ga.population[idx_best]}')
    print(f'The change was {fitness[idx_best] - last_fitness}')
    last_fitness = fitness[idx_best]


if __name__ == '__main__':
    cpu_num = cpu_count()
    print('{} CPUs available - creating {} pool processes'.format(cpu_num, cpu_num))

    last_fitness = 0
    last_timer = timer()
    filename = f'basic_ga.step_{STEP_BETWEEN_SIMULATIONS_FOR_N_AND_n}.sigmoid' + \
               datetime.now().strftime('%Y.%m.%d.%H.%M') + '.pkl'
    filepath = f'results/{filename}'

    num_generations = 100
    sol_per_pop = 25
    num_parents_mating = int(sol_per_pop * 0.5)
    num_genes = 5
    parent_selection_type = "rws"
    crossover_type = "uniform"
    mutation_by_replacement = False

    with Pool(processes=cpu_num) as pool:
        ga_instance = PooledGA(pool,
                               num_generations=num_generations,
                               num_parents_mating=num_parents_mating,
                               fitness_func=fitness_func_sigmoid,
                               sol_per_pop=sol_per_pop,
                               num_genes=num_genes,
                               parent_selection_type=parent_selection_type,
                               crossover_type=crossover_type,
                               mutation_by_replacement=mutation_by_replacement,
                               on_generation=on_generation)

        ga_instance.run()
        solution, solution_fitness, solution_idx = ga_instance.best_solution()
        print("Parameters of the best solution : {solution}".format(
            solution=solution))
        print("Fitness value of the best solution = {solution_fitness}".format(
            solution_fitness=solution_fitness))