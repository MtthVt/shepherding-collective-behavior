"""Main file with functions required for performing genetic algorithm parameters exploration
"""
from multiprocessing import Pool, cpu_count
from fitness_function import fitness_func
from pooled_ga import PooledGA


def on_generation(ga):
    print("Generation", ga.generations_completed)
    print(ga.population)


if __name__ == '__main__':
    cpu_num = cpu_count()
    print('{} CPUs available - creating {} pool processes'.format(cpu_num, cpu_num))

    with Pool(processes=cpu_num) as pool:
        ga_instance = PooledGA(pool, num_generations=10, num_parents_mating=2, fitness_func=fitness_func, sol_per_pop=3, num_genes=3,
                               gene_type=float, init_range_low=-1, init_range_high=2, parent_selection_type='sss', keep_parents=-1, on_generation=on_generation)

        ga_instance.run()
        solution, solution_fitness, solution_idx = ga_instance.best_solution()
        print("Parameters of the best solution : {solution}".format(
            solution=solution))
        print("Fitness value of the best solution = {solution_fitness}".format(
            solution_fitness=solution_fitness))
