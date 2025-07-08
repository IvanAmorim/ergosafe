def reba_upper_arm_score(angle):
    if angle < 20:
        return 1
    elif angle < 45 or angle < -20:
        return 2
    elif angle < 90:
        return 3
    else:
        return 4

def reba_lower_arm_score(angle):
    if 60 <= angle <= 100:
        return 1
    else:
        return 2

def reba_wrist_score(angle):
    if angle < 15:
        return 1
    else:
        return 2

def reba_trunk_score(angle):
    if angle == 0:
        return 0
    elif angle < 20:
        return 2
    elif angle < 0 and angle > -20:
        return 2
    elif angle > 20 and angle < 60:
        return 3
    elif angle < -20:
        return 3
    else:
        return 4

def reba_neck_score(angle):
    if angle < 0:
        return 2
    elif angle < 20:
        return 1
    else:
        return 2

def reba_leg_score():
    return 1  # Assumimos ambas as pernas em suporte estável

def reba_table_a_upper_arm(ua, la, wrist):
    score = ua + la + wrist
    return min(score, 8)

def reba_table_b_neck_trunk_leg(neck, trunk, leg):
    return min(neck + trunk + leg, 9)

def reba_table_c(table_a, table_b):
    raw = table_a + table_b
    if raw <= 4:
        return 1
    elif raw <= 7:
        return 2
    elif raw <= 10:
        return 3
    elif raw <= 13:
        return 4
    elif raw <= 15:
        return 5
    elif raw <= 17:
        return 6
    elif raw <= 19:
        return 7
    else:
        return 8

def compute_reba_score(angles):
    """
    Calcula o score REBA a partir dos ângulos normalizados (15x1).
    Retorna o score final e os componentes das tabelas A, B, C.
    """

    upper_arm_angle = max(angles[0][0], angles[1][0])
    lower_arm_angle = max(angles[0][0], angles[1][0])
    wrist_angle = max(angles[2][0], angles[3][0])
    neck_angle = angles[11][0]
    trunk_angle = angles[10][0]
    leg_score = reba_leg_score()

    upper_arm_score = reba_upper_arm_score(upper_arm_angle)
    lower_arm_score = reba_lower_arm_score(lower_arm_angle)
    wrist_score = reba_wrist_score(wrist_angle)
    neck_score_val = reba_neck_score(neck_angle)
    trunk_score_val = reba_trunk_score(trunk_angle)

    table_a = reba_table_a_upper_arm(upper_arm_score, lower_arm_score, wrist_score)
    table_b = reba_table_b_neck_trunk_leg(neck_score_val, trunk_score_val, leg_score)
    final_score = reba_table_c(table_a, table_b)

    tabela = {
        "upper_arm_score": upper_arm_score,
        "lower_arm_score": lower_arm_score,
        "wrist_score": wrist_score,
        "neck_score": neck_score_val,
        "trunk_score": trunk_score_val,
        "leg_score": leg_score,
        "table_a": table_a,
        "table_b": table_b,
        "final_reba_score": final_score,
    }

    return final_score, tabela
