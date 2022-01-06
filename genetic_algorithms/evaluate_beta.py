import multiprocessing as mp

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from shepherd_simulation import Decision_type

from fitness_function import fitness_func
from datetime import datetime

no_timesteps = 1000
no_sims_per_beta = 15
verbose = True

no_beta = 31
max_beta = 3
min_beta = 0

evaluated_counter = 0
total_evaluations_num = 0

DECISION_TYPE = Decision_type.DEFAULT_STROMBOM
DECISION_PARAMS = None

timestamp = datetime.now().strftime('%Y.%m.%d.%H.%M')
result_file = f"results/evaluation_beta.{timestamp}.npy"
result_fig_file = f"results/evaluation_beta.{timestamp}.png"


def _fitness_per_beta(beta, random_seed, beta_idx, id, total_evaluations_num, start_time):
    """
    Helper function needed for parallelization.
    Computes the simulation result for one specific beta.
    """
    if verbose:
        print(f"Evaluating beta: {beta}\tprocess_id: {mp.current_process().name[len('ForkPoolWorker-'):]}\telapsed: {str(datetime.now() - start_time).split('.')[0]}\tprogress: {round(100 * id / total_evaluations_num, 2)}")

    result = []
    # Repeat fitness for 20 times (default parameter)
    avg_score = 0
    score = fitness_func([1,beta,0],decision_type=DECISION_TYPE, random_seed=random_seed, max_steps_in_sim=no_timesteps)

    res = None
    with open(result_file, 'rb') as f:
        res = np.load(f)
        res[random_seed, beta_idx] = score
    if res is not None:
        with open(result_file, 'wb') as f:
            np.save(f, res)
    return { (random_seed, beta): result }

def generate_randomS_beta_pairs():
    pairs = []
    for random_seed in range(no_sims_per_beta):
        for beta_idx in range(no_beta):
            pairs.append([random_seed,beta_idx])
    return pairs

def generate_fitness_args():
    pairs_randomS_beta = generate_randomS_beta_pairs()
    total_evaluations_num = len(pairs_randomS_beta)
    betas = np.linspace(min_beta,max_beta,no_beta)
    start_time = datetime.now()
    return [[betas[p[1]]] + p + [i, total_evaluations_num, start_time] for i, p in enumerate(pairs_randomS_beta)]

def evaluate_paper():
    """
    Run the evaluation algorithm specified
    :return:
    """

    results = np.full((no_sims_per_beta, no_beta), 0)
    results = results.astype('float64')
    with open(result_file, 'wb') as f:
        np.save(f, results)

    with mp.Pool(processes=mp.cpu_count()) as pool:
        out = pool.starmap(_fitness_per_beta, generate_fitness_args(), chunksize=1)

    with open(result_file, 'rb') as f:
        results = np.load(f)

    return results

def plot_results(results, out_fig_fname=None):
    """
    Function to generate an annotated heatmap using the results array
    :param results:
    :param out_fig_fname:
    :return:
    """

    betas = np.linspace(min_beta, max_beta, no_beta)
    plt.plot(betas, np.sum(results, axis=0)/no_sims_per_beta)


    # Annotate the axes
    # ax.set_title("My title")
    plt.xlabel("beta")
    plt.ylabel("fitness score")
    plt.title("score for different betas")

    # Show the plot
    if out_fig_fname is None:
        plt.show()
    else:
        plt.savefig(out_fig_fname)

if __name__ == '__main__':

    print("Start evaluation")
    results = evaluate_paper()
    print(results)
    plot_results(results, result_fig_file)
