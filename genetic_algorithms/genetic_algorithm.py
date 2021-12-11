"""Main file with functions required for performing genetic algorithm parameters exploration
"""
import pygad
from os.path import isfile
import pandas as pd
import time
from genetic_algorithms.fitness_function import fitness_func

def create_log(alphas=(), betas=(), gamas=(), fitnesses=(), indices=(), generation=0, timestamp=time.time()):
    df = pd.DataFrame({'alpha': alphas,
                      'beta': betas,
                      'gama': gamas,
                      'fitness': fitnesses,
                      'index': indices,
                      })
    df['generation'] = generation
    df['timestamp'] = timestamp
    return df


def on_generation(ga):
    global filepath
    global last_fitness

    alphas, betas, gamas = ga.population.T
    fitness = ga.last_generation_fitness
    indices = list(range(len(fitness)))
    generation = ga.generations_completed
    timestamp = time.time()

    if isfile(filepath):
        old_logs = pd.read_pickle(filepath)
    else:
        old_logs = create_log()
    new_logs = pd.concat([old_logs, create_log(alphas,betas,gamas, fitness,indices,generation,timestamp)])
    pd.to_pickle(new_logs,filepath)

    print(f'Generation {ga.generations_completed} was completed')
    actual_fitness = max(fitness)
    print(f'Best solution was {actual_fitness}')
    print(f'The change was {actual_fitness - last_fitness}')
    last_fitness = actual_fitness


if __name__ == '__main__':

    last_fitness = 0
    filename = 'basic_ga ' + str(time.time()) + '.pkl'
    filepath = f'results/{filename}'

    num_generations = 100
    sol_per_pop = 25
    num_parents_mating = int(sol_per_pop * 0.5)
    num_genes = 3
    parent_selection_type = "rws"
    crossover_type = "uniform"
    mutation_by_replacement = False
    gen_space = [{"low": 0, 'high': 10}, {"low": 0, "high":4}, {"low": -100, "high": 100}]

    ga_instance = pygad.GA(num_generations=num_generations,
                           num_parents_mating=num_parents_mating,
                           fitness_func=fitness_func,
                           sol_per_pop=sol_per_pop,
                           num_genes=num_genes,
                           parent_selection_type=parent_selection_type,
                           crossover_type=crossover_type,
                           mutation_by_replacement=mutation_by_replacement,
                           gene_space=gen_space,
                           on_generation=on_generation)

    ga_instance.run()
    solution, solution_fitness, solution_idx = ga_instance.best_solution()
    print("Parameters of the best solution : {solution}".format(
        solution=solution))
    print("Fitness value of the best solution = {solution_fitness}".format(
        solution_fitness=solution_fitness))
