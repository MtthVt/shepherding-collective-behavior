import multiprocessing as mp

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from shepherd_simulation import ShepherdSimulation
from datetime import datetime

no_timesteps = 8000
max_no_neighbours = 139
no_sims_per_combination = 50
verbose = True

evaluated_counter = 0
total_evaluations_num = 0

timestamp = datetime.now().strftime('%Y.%m.%d.%H.%M')
result_file = f"results/evaluation_strombom.{timestamp}.npy"
result_fig_file = f"results/evaluation_strombom.{timestamp}.png"

ALPHA, BETA, GAMMA = 0,0,0


def _sim_with_agents(N, n, id, total_evaluations_num, start_time):
    """
    Helper function needed for parallelization.
    Computes the simulation result for one specifc N, n.
    """
    if verbose:
        print(f"Evaluating N: {N}\tn: {n}\tprocess_id: {mp.current_process().name[len('ForkPoolWorker-'):]}\telapsed: {str(datetime.now() - start_time).split('.')[0]}\tprogress: {round(100 * id / total_evaluations_num, 2)}")

    result = []
    # Repeat simulation for 50 times, 8000 time steps each (default parameter)
    avg_success = 0
    for _ in range(no_sims_per_combination):
        sim = ShepherdSimulation(N, n, no_timesteps)
        sim.set_thresh_field_params(ALPHA, BETA, GAMMA)
        _, success, _ = sim.run()
        avg_success += success
    avg_success /= no_sims_per_combination

    res = None
    with open(result_file, 'rb') as f:
        res = np.load(f)
        res[N, n] = avg_success
    if res is not None:
        with open(result_file, 'wb') as f:
            np.save(f, res)
    return { (N, n): result }

def generate_N_n_pairs():
    pairs = []
    for N in range(2, max_no_neighbours + 1):
        for n in range(1, N):
            pairs.append([N, n])
    return pairs

def generate_simulations_args():
    pairs_N_n = generate_N_n_pairs()
    total_evaluations_num = len(pairs_N_n)
    start_time = datetime.now()
    return [p + [i, total_evaluations_num, start_time] for i, p in enumerate(pairs_N_n)]

def evaluate_paper():
    """
    Run the evaluation algorithm specified
    :return:
    """

    results = np.full((max_no_neighbours + 1, max_no_neighbours + 1), -1.)

    with open(result_file, 'wb') as f:
        np.save(f, results)

    with mp.Pool(processes=mp.cpu_count()) as pool:
        out = pool.starmap(_sim_with_agents, generate_simulations_args(), chunksize=1)

    with open(result_file, 'rb') as f:
        results = np.load(f)

    return results

def load_best_alpha_beta_gamma(fname):
    df = pd.read_pickle(fname)

    df_sorted = df.sort_values('fitness')
    a = df_sorted.iloc[-1]['alpha']
    b = df_sorted.iloc[-1]['beta']
    y = df_sorted.iloc[-1]['gamma']
    return a,b,y


def plot_results(results, out_fig_fname=None):
    """
    Function to generate an annotated heatmap using the results array
    :param results:
    :param out_fig_fname:
    :return:
    """
    # Plot the results
    fig, ax = plt.subplots()

    # Plot the heatmap itself
    im = ax.imshow(results, cmap='Blues_r', interpolation='nearest', origin='lower')

    # Create colorbar
    cbar = ax.figure.colorbar(im, ax=ax)
    cbar.ax.set_ylabel("Proportion of successful shepherding events", rotation=-90, va="bottom")

    # Modify the x and y axis to represent the correct amount of neighbors
    res_max_no_neighbours = results.shape[0]
    ind = np.arange(res_max_no_neighbours)
    x_labels = [str(N) for N in range(1, res_max_no_neighbours + 1)]
    y_labels = [str(n) for n in range(1, res_max_no_neighbours + 1)]
    plt.xticks(ind[9::10], labels=x_labels[9::10])
    plt.yticks(ind[9::10], labels=y_labels[9::10])

    # Annotate the axes
    # ax.set_title("My title")
    plt.xlabel("no. agents (N)")
    plt.ylabel("no. neighbors (n)")

    # Show the plot
    if out_fig_fname is None:
        plt.show()
    else:
        plt.savefig(out_fig_fname)

if __name__ == '__main__':
    ALPHA, BETA, GAMMA = load_best_alpha_beta_gamma('results/basic_ga.step_4.2021.12.12.19.40.pkl')
    print(f"Loaded threshold params: {ALPHA}, {BETA}, {GAMMA}")

    print("Start evaluation")
    results = evaluate_paper()
    print(results)
    plot_results(results[1:, 1:].T, result_fig_file)
