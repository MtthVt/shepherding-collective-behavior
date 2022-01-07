from matplotlib import pyplot as plt
import numpy as np
import os


def plot_driving_collecting_progress(driving_counter):
    fig = plt.figure()
    plt.plot(driving_counter)
    plt.xlabel("Steps")
    plt.ylabel("Driving")
    os.makedirs('log', exist_ok=True)
    fig.savefig('log/driving_progress.png')


def plot_driving_collecting_bar(driving_counter):
    fig = plt.figure()
    bars = ('Driving', 'Collecting')
    num_driving = driving_counter[-1]
    num_collecting = len(driving_counter) - num_driving
    x_pos = np.arange(len(bars))
    plt.bar(x_pos, [num_driving, num_collecting])
    plt.xticks(x_pos, bars)
    fig.savefig('log/driving_bar.png')
