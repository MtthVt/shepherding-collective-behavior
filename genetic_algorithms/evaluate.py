import multiprocessing as mp

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from shepherd_simulation import Decision_type

from shepherd_simulation import ShepherdSimulation
from datetime import datetime

NO_TIMESTEPS = 8000
MAX_NO_NEIGHBOURS = 139
NO_SIMS_PER_COMBINATION = 50
DIFFICULT_RANGE_ONLY = True
VERBOSE = True

RESULTS_INITIAL_FILL_VAL = -1.

evaluated_counter = 0
total_evaluations_num = 0

DECISION_TYPE = Decision_type.SIGMOID
DECISION_PARAMS = None

timestamp = datetime.now().strftime('%Y.%m.%d.%H.%M')
result_file = f"results/evaluation_strombom.{DECISION_TYPE}.{timestamp}.npy"
result_fig_file = f"results/evaluation_strombom.{DECISION_TYPE}.{timestamp}.png"


def _sim_with_agents(N, n, id, total_evaluations_num, start_time):
    """
    Helper function needed for parallelization.
    Computes the simulation result for one specifc N, n.
    """
    if VERBOSE:
        print(f"Evaluating N: {N}\tn: {n}\tprocess_id: {mp.current_process().name[len('ForkPoolWorker-'):]}\telapsed: {str(datetime.now() - start_time).split('.')[0]}\tprogress: {round(100 * id / total_evaluations_num, 2)}")

    result = []
    # Repeat simulation for 50 times, 8000 time steps each (default parameter)
    avg_success = 0
    for _ in range(NO_SIMS_PER_COMBINATION):
        sim = ShepherdSimulation(num_sheep_total=N, num_sheep_neighbors=n, max_steps=NO_TIMESTEPS, decision_type=DECISION_TYPE, random_state=np.random.RandomState())
        sim.set_thresh_field_params(DECISION_PARAMS)
        _, success, _ = sim.run()
        avg_success += success
    avg_success /= NO_SIMS_PER_COMBINATION

    res = None
    with open(RESULT_FILE, 'rb') as f:
        res = np.load(f)
        res[N, n] = avg_success
    if res is not None:
        with open(RESULT_FILE, 'wb') as f:
            np.save(f, res)
    return { (N, n): result }

def generate_N_n_pairs():
    pairs = []
    for N in range(2, MAX_NO_NEIGHBOURS + 1):
        for n in range(1, N):
            pairs.append([N, n])
    return pairs

def generate_N_n_pairs_difficult_range():
    pairs = []
    for N in range(30, MAX_NO_NEIGHBOURS + 1):
        for n in range(int(np.floor(3 * np.log2(N))), int(np.ceil(0.53 * N))):
            pairs.append([N, n])
    return pairs

def generate_simulations_args(difficult_range_only=False):
    pairs_N_n = generate_N_n_pairs_difficult_range() if difficult_range_only else generate_N_n_pairs()
    total_evaluations_num = len(pairs_N_n)
    start_time = datetime.now()
    return [p + [i, total_evaluations_num, start_time] for i, p in enumerate(pairs_N_n)]

def evaluate_paper():
    """
    Run the evaluation algorithm specified
    :return:
    """

    results = np.full((MAX_NO_NEIGHBOURS + 1, MAX_NO_NEIGHBOURS + 1), RESULTS_INITIAL_FILL_VAL)
    results = results.astype('float64')
    with open(RESULT_FILE, 'wb') as f:
        np.save(f, results)

    with mp.Pool(processes=mp.cpu_count()) as pool:
        out = pool.starmap(_sim_with_agents, generate_simulations_args(difficult_range_only=DIFFICULT_RANGE_ONLY), chunksize=1)

    with open(RESULT_FILE, 'rb') as f:
        results = np.load(f)

    return results

def load_best_alpha_beta_gamma(fname):
    df = pd.read_pickle(fname)

    df_sorted = df.sort_values('fitness')
    a = df_sorted.iloc[-1]['alpha']
    b = df_sorted.iloc[-1]['beta']
    y = df_sorted.iloc[-1]['gamma']
    return a,b,y

def load_best_sigmoid_params(fname):
    df = pd.read_pickle(fname)

    df_sorted = df.sort_values('fitness')
    N = df_sorted.iloc[-1]['param_N']
    n = df_sorted.iloc[-1]['param_n']
    fur = df_sorted.iloc[-1]['param_fur']
    var = df_sorted.iloc[-1]['param_var']
    angl = df_sorted.iloc[-1]['param_angle']
    return N, n, fur, var, angl

def load_best_decision_params(fname):
    if DECISION_TYPE == Decision_type.SIGMOID:
        return load_best_sigmoid_params(fname)
    elif DECISION_TYPE == Decision_type.DEFAULT_STROMBOM:
        return load_best_alpha_beta_gamma(fname)

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
    DECISION_PARAMS = load_best_decision_params('results/basic_ga.step_4.sigmoid2021.12.28.10.15.pkl')
    print(f"Loaded decision params: {DECISION_PARAMS}")

    print("Start evaluation")
    results = evaluate_paper()
    print(results)
    plot_results(results[1:, 1:].T, RESULT_FIG_FILE)
