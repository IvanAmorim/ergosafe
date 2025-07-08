def rula_upper_arm_score(angle, shoulder_raised=False, abducted=False, supported=False):
    if angle > 120:
        score = 6
    elif angle > 100:
        score = 5
    elif angle > 90:
        score = 4
    elif angle > 60:
        score = 3
    elif angle > 20:
        score = 2
    else:
        score = 1

    if shoulder_raised:
        score += 1
    if abducted:
        score += 1
    if supported:
        score -= 1
    return max(1, score)


def rula_forearm_score(angle, working_across_midline=False):
    score = 1 if 60 <= angle <= 100 else 2
    if working_across_midline:
        score += 1
    return score


def rula_wrist_score(angle, bent=False, twist=0):
    score = 1 if angle <= 15 else 2
    if bent:
        score += 1
    if twist == 1:
        score += 1
    elif twist == 2:
        score += 2
    return min(score, 4)


def rula_neck_score(angle, twisted=False, side_bending=False):
    if angle > 20:
        score = 3
    elif angle > 10:
        score = 2
    else:
        score = 1
    if twisted:
        score += 1
    if side_bending:
        score += 1
    return score


def rula_trunk_score(angle, twisted=False, side_bending=False):
    if angle > 60:
        score = 4
    elif angle > 20:
        score = 3
    elif angle > 10:
        score = 2
    else:
        score = 1
    if twisted:
        score += 1
    if side_bending:
        score += 1
    return score


def rula_leg_score(feet_supported=True):
    return 1 if feet_supported else 2


def lookup_table_a(upper, lower, wrist):
    # Matriz da Tabela A do formulário
    table = [
        [1, 2, 2, 3],
        [2, 2, 3, 3],
        [2, 3, 3, 4],
        [3, 3, 4, 4],
        [3, 4, 4, 5],
        [4, 4, 5, 5],
    ]
    row = min(upper, 6) - 1
    col = min(lower, 3) - 1
    wrist_index = min(wrist, 4) - 1
    return table[row][col] + wrist_index


def lookup_table_b(neck, trunk, leg):
    table = [
        [1, 2, 3],
        [2, 3, 3],
        [3, 3, 4],
        [3, 4, 4],
        [4, 4, 5],
        [5, 5, 6],
    ]
    row = min(neck, 6) - 1
    col = min(trunk, 6) - 1
    leg_index = min(leg, 3) - 1
    return table[row][leg_index]


def lookup_table_c(score_a, score_b):
    table_c = [
        [1, 2, 3, 3, 4, 4, 5],
        [2, 3, 3, 4, 4, 5, 5],
        [3, 3, 4, 4, 5, 5, 6],
        [3, 4, 4, 5, 5, 6, 6],
        [4, 4, 5, 5, 6, 6, 7],
        [4, 5, 5, 6, 6, 7, 7],
        [5, 5, 6, 6, 7, 7, 7],
    ]
    row = min(score_a, 7) - 1
    col = min(score_b, 7) - 1
    return table_c[row][col]


def compute_rula_score(data):
    """
    data: dicionário com ângulos e ajustes
    """
    required_keys = ["upper_arm_angle", "forearm_angle", "wrist_angle", "neck_angle", "trunk_angle"]
    missing_keys = [k for k in required_keys if k not in data]

    # if missing_keys:
    #     raise ValueError(f"Faltam os seguintes campos para cálculo RULA: {missing_keys}")

    ajustes = data.get("ajustes", {})

    upper = rula_upper_arm_score(data.get("upper_arm_angle",0),
                                  shoulder_raised=ajustes.get("shoulder_raised", False),
                                  abducted=ajustes.get("abducted", False),
                                  supported=ajustes.get("arm_supported", False))

    lower = rula_forearm_score(data.get("forearm_angle",0), working_across_midline=ajustes.get("midline", False))

    wrist = rula_wrist_score(data.get("wrist_angle",0),
                             bent=ajustes.get("wrist_bent", False),
                             twist=ajustes.get("wrist_twist", 0))

    neck = rula_neck_score(data.get("neck_angle",0),
                           twisted=ajustes.get("neck_twisted", False),
                           side_bending=ajustes.get("neck_side", False))

    trunk = rula_trunk_score(data.get("trunk_angle",0),
                             twisted=ajustes.get("trunk_twisted", False),
                             side_bending=ajustes.get("trunk_side", False))

    leg = rula_leg_score(feet_supported=ajustes.get("feet_supported", True))

    score_a = lookup_table_a(upper, lower, wrist)
    score_b = lookup_table_b(neck, trunk, leg)

    muscle_score = 1 if ajustes.get("static_posture", False) or ajustes.get("repetitive", False) else 0
    load_score = 0
    carga = data.get("carga_peso", 0)
    if 4 < carga <= 10:
        load_score = 1
    elif 10 < carga <= 22:
        load_score = 2
    elif carga > 22:
        load_score = 3

    final_score = lookup_table_c(score_a + muscle_score + load_score, score_b)
    table_score = {
        "upper_arm": upper,
        "forearm": lower,
        "wrist": wrist,
        "neck": neck,
        "trunk": trunk,
        "leg": leg,
        "score_a": score_a,
        "score_b": score_b,
        "muscle_score": muscle_score,
        "load_score": load_score
    }   

    return final_score, table_score 