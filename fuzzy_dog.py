from simpful import *
import numpy as np


def get_fuzzy_system(t, t_min, t_max, num_sheep_total, d_c):
    """

    :param t: current state of time
    :param t_min: minimum time to get to target
    :param t_max: maximal available time
    :param num_sheep_total: total number of sheep
    :param d_c: critical distance dog can still traverse in the remaining time
    :return: Fuzzy System
    """
    FS = FuzzySystem(verbose=False, show_banner=False)
    # Define fuzzy sets and linguistic variables
    T_1 = FuzzySet(function=Trapezoidal_MF(a=0, b=0, c=t_min, d=0.3 * t_max), term="small")
    T_2 = FuzzySet(function=Triangular_MF(a=t_min, b=0.3 * t_max, c=0.5 * t_max), term="medium")
    T_3 = FuzzySet(function=Triangular_MF(a=0.3 * t_max, b=0.5 * t_max, c=t_max), term="large")
    T_4 = FuzzySet(function=Trapezoidal_MF(a=0.5 * t_max, b=t_max, c=t_max + 5, d=t_max + 5), term="very_large")

    FS.add_linguistic_variable("Time", LinguisticVariable([T_1, T_2, T_3, T_4], concept="Elapsed time",
                                                          universe_of_discourse=[0, t_max + 5]))


    # new rule: distance of the farthest sheep to the herd or density of the herd
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
    """

    # d_c: critical distance, distance dog can still traverse in the remaining time
    D_1 = FuzzySet(function=Trapezoidal_MF(a=0, b=0, c=0.1 * d_c, d=0.4 * d_c), term="near")
    D_2 = FuzzySet(function=Trapezoidal_MF(a=0.2 * d_c, b=0.5 * d_c, c=0.7 * d_c, d=0.95 * d_c), term="medium")
    D_3 = FuzzySet(function=Trapezoidal_MF(a=0.7 * d_c, b=d_c, c=d_c + 5, d=d_c + 5), term="far")
    FS.add_linguistic_variable("Distance",
                               LinguisticVariable([D_1, D_2, D_3], concept="Distance to target",
                                                  universe_of_discourse=[0, d_c + 5]))

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

    R1 = "IF (Time IS large) AND (Distance IS far) THEN (Decision IS collecting)"
    R2 = "IF (Time IS very_large) AND (Distance IS far) THEN (Decision IS driving)"
    R3 = "IF (Time IS small) AND (Distance IS near) THEN (Decision IS collecting)"
    R4 = "IF (Time IS medium) AND (Distance IS far) THEN (Decision IS driving)"
    R5 = "IF (Time IS very_large) AND (Distance IS near) THEN (Decision IS driving)"  # this rule does not make too much sense in our setting, because the target is not like a bucket that the sheep stay in

    FS.add_rules([R1, R2, R3, R4, R5])

    return FS