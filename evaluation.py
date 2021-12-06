import multiprocessing as mp

import matplotlib.pyplot as plt
import numpy as np

from shepherd_simulation import ShepherdSimulation

no_timesteps = 8000
max_no_neighbours = 6
no_sims_per_combination = 50
verbose = True


def _sim_with_neighbours(N):
    """
    Helper function needed for parallelization.
    Computes the simulation result for one specifc N, iterates over every possible n
    :param N:
    :return:
    """
    if verbose:
        print("Evaluating " + str(N) + " neighbours")
    result = np.zeros(max_no_neighbours - 1)
    for n in range(1, N):
        # Repeat simulation for 50 times, 8000 time steps each (default parameter)
        avg_success = 0
        for i in range(1, no_sims_per_combination + 1):
            sim = ShepherdSimulation(N, n, no_timesteps)
            counter, success = sim.run()
            avg_success += success
        avg_success /= no_sims_per_combination
        # Save result in matrix
        result[n - 1] = avg_success
    if verbose:
        print("Finished evaluation for " + str(N) + " neighbours")
    return {N: result}


def evaluate_paper():
    """
    Run the evaluation algorithm specified
    :return:
    """

    # Step 1: Init multiprocessing.Pool()
    pool = mp.Pool(mp.cpu_count() - 1)

    compute_results = pool.map(_sim_with_neighbours, [N for N in range(2, max_no_neighbours + 1)])

    # Step 3: Don't forget to close
    pool.close()

    # Modify the results into a numpy array
    results = np.zeros([max_no_neighbours - 1, max_no_neighbours - 1])
    for result_dict in compute_results:
        key = list(result_dict.keys())[0]
        item = result_dict[key]
        results[key - 2] = item

    # Transpose the results to match the row/column annotation of the paper
    return results.T


def plot_results(results):
    """
    Function to generate an annotatet heatmap using the results array
    :param results:
    :return:
    """
    # Plot the results
    fig, ax = plt.subplots()

    # Plot the heatmap itself
    im = ax.imshow(results, cmap='hot', interpolation='nearest', origin='lower')

    # Create colorbar
    cbar = ax.figure.colorbar(im, ax=ax)
    cbar.ax.set_ylabel("Proportion of successful shepherding events", rotation=-90, va="bottom")

    # Modify the x and y axis to represent the correct amount of neighbors
    ind = np.arange(max_no_neighbours - 2 + 1)
    x_labels = [str(N) for N in range(2, max_no_neighbours + 1)]
    y_labels = [str(n) for n in range(1, max_no_neighbours)]
    plt.xticks(ind, labels=x_labels)
    plt.yticks(ind, labels=y_labels)

    # Annotate the axes
    # ax.set_title("My title")
    plt.xlabel("no. agents (N)")
    plt.ylabel("no. neighbors (n)")

    # Show the plot
    plt.show()


if __name__ == '__main__':
    print("Start evaluation")
    results = evaluate_paper()
    print(results)
    plot_results(results)
