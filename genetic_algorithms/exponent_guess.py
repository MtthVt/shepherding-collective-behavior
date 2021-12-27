import numpy as np
from fitness_function import fitness_func
import matplotlib.pyplot as plt
import pickle


# THIS SCRIPT COMPUTE THE BEST EXPONENT FOR NUMBER OF SHEEP IN DECISION FUNCTION,
# ALPHA AND GAMMA ARE SAME AS IN STROMBOM MODEL

def get_fitness(beta):
    score = fitness_func([1, beta, 0], 0)
    score = 1 / score
    print(score)
    return score


betas = np.linspace(0, 4, 41)

scores = list(map(get_fitness, betas))
# with open("betas_scores.pkl", "wr") as fb:
#    pickle.dump(scores,fb)
#scores = [
    # 427655.5728045554,
    # 417172.3518815973,
    # 467633.22193663137,
    # 415139.18645559164,
    # 442230.45202836284,
    # 276283.3273224374,
    # 304737.0873321866,
    # 175970.49621785906,
    # 274876.9932362772,
    # 211767.91619375107,
    # 162219.64884185634,
    # 133115.66044006683,
    # 163670.47923140138,
    # 101272.12521814943,
    # 146852.44723003195,
    # 180225.53847183072,
    # 163731.88042086494,
    # 134980.83381891772,
    # 103920.5451062532,
    # 165368.81642590847,
    # 164708.84478877578,
# ]

plt.plot(betas, scores)
plt.show()