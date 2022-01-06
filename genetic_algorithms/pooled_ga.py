import pygad
import numpy as np


class PooledGA(pygad.GA):
    """Wrapper class for pygad.GA, enabling multiprocessing of fitness function computing
    """

    def __init__(self, pool, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pool = pool

    def fitness_wrapper(self, solution):
        return self.fitness_func(solution, 0)

    def cal_pop_fitness(self):
        pop_fitness = self.pool.map(self.fitness_wrapper, self.population)
        pop_fitness = np.array(pop_fitness)
        return pop_fitness

    # overriden to resolve the error of pickling pool object inside PooledGA instance
    def __getstate__(self):
        self_dict = self.__dict__.copy()
        del self_dict['pool']
        return self_dict

    def __setstate__(self, state):
        self.__dict__.update(state)
