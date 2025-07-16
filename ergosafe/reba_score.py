def reba_upper_arm_score(angle, shoulder_raised=False, abducted=False, leaning=False):
    if angle < 20:
        score = 1
    elif angle < 45:
        score = 2
    elif angle < 90:
        score = 3
    else:
        score = 4
    if shoulder_raised:
        score += 1
    if abducted:
        score += 1
    if leaning:
        score -= 1
    return max(1, score)


def reba_lower_arm_score(angle):
    return 1 if 60 <= angle <= 100 else 2


def reba_wrist_score(angle, bent_twisted=False):
    score = 1 if angle <= 15 else 2
    if bent_twisted:
        score += 1
    return score


def reba_neck_score(angle, twisted=False, side_bending=False):
    if angle < 0:
        score = 2
    elif angle <= 20:
        score = 1
    else:
        score = 2
    if twisted:
        score += 1
    if side_bending:
        score += 1
    return score


def reba_trunk_score(angle, twisted=False, side_bending=False):
    if angle <= 0:
        score = 1
    elif angle <= 20:
        score = 2
    elif angle <= 60:
        score = 3
    else:
        score = 4
    if twisted:
        score += 1
    if side_bending:
        score += 1
    return score


def reba_leg_score(knee_bent=False, unstable=False):
    if not knee_bent and not unstable:
        return 1
    elif knee_bent or unstable:
        return 2
    else:
        return 3


def lookup_table_a(trunk_score, leg_score, neck_score):
    # trunk (1-5), leg (1-4)
    table_a = [
        [1, 2, 3, 4],
        [2, 2, 3, 4],
        [3, 3, 4, 5],
        [4, 4, 5, 6],
        [5, 5, 6, 7],
    ]
    trunk_index = min(trunk_score, 5) - 1
    leg_index = min(leg_score, 4) - 1
    inter_score = table_a[trunk_index][leg_index]

    # Neck vai de 1 a 3
    posture_table = [
        [1, 2, 3],
        [2, 3, 4],
        [3, 4, 5],
        [4, 5, 6],
        [5, 6, 7],
        [6, 7, 8],
        [7, 8, 9],
    ]
    neck_index = min(neck_score, 3) - 1
    return posture_table[inter_score - 1][neck_index]


def lookup_table_b(upper_arm, lower_arm, wrist):
    table_b = [
        [1, 2, 2],
        [2, 2, 3],
        [2, 3, 3],
        [3, 3, 4],
        [3, 4, 4],
        [4, 4, 5],
    ]
    row = min(upper_arm, 6) - 1
    col1 = min(lower_arm, 3) - 1
    score1 = table_b[row][col1]

    wrist_index = min(wrist, 3) - 1
    posture_table = [
        [1, 2, 3],
        [2, 3, 4],
        [3, 4, 5],
        [4, 5, 6],
        [5, 6, 7],
        [6, 7, 8],
    ]
    return posture_table[score1 - 1][wrist_index]


def lookup_table_c(score_a, score_b):
    table_c = [
        [1, 2, 3, 3, 4, 4, 5, 5, 6, 6, 7, 7],
        [2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 7, 7],
        [3, 3, 3, 4, 4, 5, 5, 6, 6, 7, 7, 7],
        [3, 3, 4, 4, 5, 5, 6, 6, 7, 7, 7, 8],
        [4, 4, 4, 5, 5, 6, 6, 7, 7, 8, 8, 8],
        [4, 4, 5, 5, 6, 6, 7, 7, 8, 8, 8, 9],
        [5, 5, 5, 6, 6, 7, 7, 8, 8, 9, 9, 9],
        [5, 5, 6, 6, 7, 7, 8, 8, 9, 9, 9, 9],
        [6, 6, 6, 7, 7, 8, 8, 9, 9, 9, 9, 9],
        [6, 6, 7, 7, 8, 8, 9, 9, 9, 9, 9, 9],
        [7, 7, 7, 8, 8, 9, 9, 9, 9, 9, 9, 9],
        [7, 7, 8, 8, 9, 9, 9, 9, 9, 9, 9, 9],
    ]
    row = min(score_a, 12) - 1
    col = min(score_b, 12) - 1
    return table_c[row][col]


def compute_reba_score(input_data):
    """
    input_data: dicionário com campos:
        - upper_arm_angle
        - lower_arm_angle
        - wrist_angle
        - neck_angle
        - trunk_angle
        - carga_peso (kg)
        - ajustes (dicionário com chaves como shoulder_raised, etc)
    """
    ajustes = input_data.get("ajustes", {})
    peso = input_data.get("carga_peso", 0)

    upper = reba_upper_arm_score(input_data["upper_arm_angle"],
                                  shoulder_raised=ajustes.get("shoulder_raised", False),
                                  abducted=ajustes.get("abducted", False),
                                  leaning=ajustes.get("leaning", False))
    lower = reba_lower_arm_score(input_data["lower_arm_angle"])
    wrist = reba_wrist_score(input_data["wrist_angle"], bent_twisted=ajustes.get("wrist_twisted", False))
    neck = reba_neck_score(input_data["neck_angle"],
                           twisted=ajustes.get("neck_twisted", False),
                           side_bending=ajustes.get("neck_side", False))
    trunk = reba_trunk_score(input_data["trunk_angle"],
                             twisted=ajustes.get("trunk_twisted", False),
                             side_bending=ajustes.get("trunk_side", False))
    leg = reba_leg_score(knee_bent=ajustes.get("knee_bent", False), unstable=ajustes.get("unstable", False))

    score_a = lookup_table_a(trunk, leg, neck)
    score_b = lookup_table_b(upper, lower, wrist)

    force_score = 0
    if peso > 0 and peso <= 5:
        force_score = 0
    elif peso <= 10:
        force_score = 1
    elif peso <= 20:
        force_score = 2
    else:
        force_score = 3

    score_a += force_score
    reba_final = lookup_table_c(score_a, score_b)

    table_score = {
        "upper_arm": upper,
        "lower_arm": lower,
        "wrist": wrist,
        "neck": neck,
        "trunk": trunk,
        "leg": leg,
        "score_a": score_a,
        "score_b": score_b,
    }
    
    return reba_final, table_score 
