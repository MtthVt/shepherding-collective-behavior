from simpful import *
import numpy as np


def get_fuzzy_system(t, t_min, t_max, d_s, d_d, d_t):
    """

    :param t: current state of time
    :param t_min: minimum time to get to target
    :param t_max: maximal available time
    :param d_s: average distance of sheep to center of mass
    :param d_d: distance to temporary target for driving
    :param d_t: initial distance of sheep-herd to target
    :return: Fuzzy System
    """

    # Idea from professor: # Scientific approach: say what we found weired in Stromböm ( CoM) as target acquired,
    # compare algorithm to Stromböm how it is, # and then step away from it and say what we did "better"

    FS = FuzzySystem(verbose=False, show_banner=False)

    # distance from the farthest sheep to the com (if dog perceives sheep as near/far from herd depends on average
    # distance to com)

    D_s_1 = FuzzySet(function=Trapezoidal_MF(a=0, b=0, c=1.5*d_s, d=3 * d_s), term="near")
    D_s_2 = FuzzySet(function=Trapezoidal_MF(a=2 * d_s, b=3.5*d_s, c=5 * d_s, d=5 * d_s), term="far")
    FS.add_linguistic_variable("Distance_runaway",
                               LinguisticVariable([D_s_1, D_s_2], concept="Distance of runaway sheep to com",
                                                  universe_of_discourse=[0, 5*d_s]))

    # distance to collecting point is compared to distance to driving point
    D_d_1 = FuzzySet(function=Trapezoidal_MF(a=0, b=0, c=0.6*d_d, d=1.25 * d_d), term="near")
    D_d_2 = FuzzySet(function=Trapezoidal_MF(a=1 * d_d, b=1.75 * d_d, c=5 * d_d, d=5 * d_d), term="far")
    FS.add_linguistic_variable("Distance_collecting_point",
                               LinguisticVariable([D_d_1, D_d_2], concept="Distance to next temporary collecting target",
                                                  universe_of_discourse=[0, 5 * d_s]))

    # distance of center of mass to target, if sheep herd is very close to target, it should go into driving mode
    # D_t_1 = FuzzySet(function=Trapezoidal_MF(a=0, b=0, c=0.4 * d_t, d=0.8 * d_t), term="near")
    # D_t_2 = FuzzySet(function=Trapezoidal_MF(a=0.6 * d_t, b=d_t, c=3 * d_t, d=3 * d_t), term="far")
    # FS.add_linguistic_variable("Distance_final_target", LinguisticVariable([D_t_1, D_t_2], concept="Distance to final target", universe_of_discourse=[0, 3 * d_s]))

    # Define output fuzzy sets and linguistic variable
    O_1 = FuzzySet(function=Trapezoidal_MF(a=0, b=0, c=0.1, d=0.3), term="driving")
    O_2 = FuzzySet(function=Trapezoidal_MF(a=0.1, b=0.3, c=0.8, d=1), term="collecting")

    FS.add_linguistic_variable("Decision", LinguisticVariable([O_1, O_2], universe_of_discourse=[0, 1]))

    R1 = "IF (Distance_runaway IS far) AND (Distance_collecting_point IS near) THEN (Decision IS collecting)"
    R2 = "IF (Distance_runaway IS near) AND (Distance_collecting_point IS far) THEN (Decision IS driving)"
    #R3 = "IF (Distance_runaway IS ) AND (Distance_collecting_point IS far) AND (Distance_final_target IS near) THEN (Decision IS driving)"
    FS.add_rules([R1, R2])

    return FS