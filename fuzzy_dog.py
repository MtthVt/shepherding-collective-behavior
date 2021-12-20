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

    D_s_1 = FuzzySet(function=Trapezoidal_MF(a=0, b=0, c=d_s, d=1.5 * d_s), term="near")
    D_s_2 = FuzzySet(function=Trapezoidal_MF(a=d_s, b=1.5 * d_s, c=2 * d_s, d=3 * d_s), term="medium")
    D_s_3 = FuzzySet(function=Trapezoidal_MF(a=2.5 * d_s, b=3.5*d_s, c=5 * d_s, d=5 * d_s), term="far")
    FS.add_linguistic_variable("Distance_runaway",
                               LinguisticVariable([D_s_1, D_s_2, D_s_3], concept="Distance of runaway sheep to com",
                                                  universe_of_discourse=[0, 5*d_s]))

    # evtl. density of sheep-herd

    # distance to collecting point is compared to distance to driving point
    D_d_1 = FuzzySet(function=Trapezoidal_MF(a=0, b=0, c=0.37*d_d, d=0.75 * d_d), term="near")
    D_d_2 = FuzzySet(function=Trapezoidal_MF(a=0.5 * d_d, b=0.75 * d_d, c=1.25 * d_d, d=1.5 * d_d), term="medium")
    D_d_3 = FuzzySet(function=Trapezoidal_MF(a=1.25 * d_d, b=1.75 * d_d, c=5 * d_d, d=5 * d_d), term="far")
    FS.add_linguistic_variable("Distance_collecting_point",
                               LinguisticVariable([D_d_1, D_d_2, D_d_3], concept="Distance to next temporary collecting target",
                                                  universe_of_discourse=[0, 5 * d_s]))

    # distance of center of mass to target, if sheep herd is very close to target, it should go into driving mode
    D_t_1 = FuzzySet(function=Trapezoidal_MF(a=0, b=0, c=0.15 * d_t, d=0.3 * d_t), term="near")
    D_t_2 = FuzzySet(function=Trapezoidal_MF(a=0.2 * d_t, b=0.4 * d_t, c=0.6 * d_t, d=0.8*d_t), term="medium")
    D_t_3 = FuzzySet(function=Trapezoidal_MF(a=0.7 * d_t, b=d_t, c=3 * d_t, d=3 * d_t), term="far")
    FS.add_linguistic_variable("Distance_final_target",
                               LinguisticVariable([D_t_1, D_t_2, D_t_3],
                                                  concept="Distance to final target",
                                                  universe_of_discourse=[0, 3 * d_s]))

    """
    # Minimum number of sheep to be collected
    q_min = 0.5*num_sheep_total
    # capacity of the robot (probably not applicable to dog)
    c_n = num_sheep_total
    D_1 = FuzzySet(function=Trapezoidal_MF(a=0, b=0, c=q_min, d=0.5 * c_n), term="small")
    D_2 = FuzzySet(function=Triangular_MF(a=q_min, b=0.5 * c_n, c=c_n), term="medium")
    D_3 = FuzzySet(function=Trapezoidal_MF(a=0.5 * c_n, b=c_n, c=c_n + 5, d=c_n + 5), term="large")
    FS.add_linguistic_variable("Quantity", LinguisticVariable([D_1, D_2, D_3], concept="Number of collected sheep",
                                                              universe_of_discourse=[0, c_n + 5]))
                                                              
                                                              
    # Depending on how much time is left the dog should try to collect more sheep or drive the sheep he collected to the target
    T_1 = FuzzySet(function=Trapezoidal_MF(a=0, b=0, c=t_min, d=0.3 * t_max), term="small")
    T_2 = FuzzySet(function=Triangular_MF(a=t_min, b=0.3 * t_max, c=0.5 * t_max), term="medium")
    T_3 = FuzzySet(function=Triangular_MF(a=0.3 * t_max, b=0.5 * t_max, c=t_max), term="large")
    T_4 = FuzzySet(function=Trapezoidal_MF(a=0.5 * t_max, b=t_max, c=t_max + 5, d=t_max + 5), term="very_large")

    FS.add_linguistic_variable("Time", LinguisticVariable([T_1, T_2, T_3, T_4], concept="Elapsed time",
                                                          universe_of_discourse=[0, t_max + 5]))
    """

    # Define output fuzzy sets and linguistic variable
    O_1 = FuzzySet(function=Trapezoidal_MF(a=0, b=0, c=0.1, d=0.3), term="driving")
    O_2 = FuzzySet(function=Trapezoidal_MF(a=0.1, b=0.3, c=0.8, d=1), term="collecting")

    FS.add_linguistic_variable("Decision", LinguisticVariable([O_1, O_2], universe_of_discourse=[0, 1]))

    # Define Fuzzy Rules
    """
    R1 = "IF (Time IS large) AND (Distance IS far) AND (Quantity IS small) THEN (Decision IS collecting)"
    R2 = "IF (Time IS very_large) AND (Distance IS far) AND (Quantity IS medium) THEN (Decision IS driving)"
    R3 = "IF (Time IS small) AND (Distance IS near) AND (Quantity IS small) THEN (Decision IS collecting)"
    R4 = "IF (Time IS medium) AND (Distance IS far) AND (Quantity IS large) THEN (Decision IS driving)"
    R5 = "IF (Time IS very_large) AND (Distance IS near) AND (Quantity IS small) THEN (Decision IS driving)"            # this rule does not make too much sense in our setting, because the target is not like a bucket that the sheep stay in

    FS.add_rules([R1, R2, R3, R4, R5])
    """

    R1 = "IF (Distance_runaway IS far) AND (Distance_collecting_point IS near) THEN (Decision IS collecting)"
    R2 = "IF (Distance_runaway IS medium) AND (Distance_collecting_point IS near) THEN (Decision IS collecting)"
    R3 = "IF (Distance_runaway IS near) AND (Distance_collecting_point IS far) THEN (Decision IS driving)"
    R4 = "IF (Distance_runaway IS medium) AND (Distance_collecting_point IS far) AND (Distance_final_target IS near) THEN (Decision IS driving)"
    FS.add_rules([R1, R2, R3, R4])

    return FS