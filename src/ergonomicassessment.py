import numpy as np

class ErgonomicAssessment:
    def __init__(self):
        pass

    def compute_angles_from_yolo(self, keypoints):
        # Definir pares de pontos: [(ombro, cotovelo), (cotovelo, pulso), etc.]
        # Assumimos que keypoints tem (17, 2): COCO
        def angle_between(p1, p2, p3):
            v1 = p1 - p2
            v2 = p3 - p2
            unit_v1 = v1 / np.linalg.norm(v1)
            unit_v2 = v2 / np.linalg.norm(v2)
            dot_product = np.dot(unit_v1, unit_v2)
            angle = np.arccos(np.clip(dot_product, -1.0, 1.0))
            return np.degrees(angle)

        # Lista de ângulos de interesse (exemplo simplificado)
        angles = []
        angles.append(angle_between(keypoints[5], keypoints[7], keypoints[9]))   # Braço esquerdo
        angles.append(angle_between(keypoints[6], keypoints[8], keypoints[10]))  # Braço direito
        angles.append(angle_between(keypoints[9], keypoints[10], keypoints[11])) # Mãos
        angles.append(angle_between(keypoints[5], keypoints[6], keypoints[11])) # Ombros
        angles.append(angle_between(keypoints[11], keypoints[5], keypoints[7])) # Tronco esquerdo
        angles.append(angle_between(keypoints[12], keypoints[6], keypoints[8])) # Tronco direito
        angles.append(angle_between(keypoints[11], keypoints[13], keypoints[15])) # Perna esquerda
        angles.append(angle_between(keypoints[12], keypoints[14], keypoints[16])) # Perna direita
        angles.append(angle_between(keypoints[13], keypoints[15], keypoints[15])) # Joelho esquerdo
        angles.append(angle_between(keypoints[14], keypoints[16], keypoints[16])) # Joelho direito
        angles.append(angle_between(keypoints[0], keypoints[1], keypoints[2])) # Pescoço
        angles.append(angle_between(keypoints[0], keypoints[11], keypoints[12])) # Inclinação
        angles.append(angle_between(keypoints[5], keypoints[11], keypoints[13])) # Inclinação tronco
        angles.append(angle_between(keypoints[9], keypoints[7], keypoints[5]))   # Rotação punho

        return np.array(angles)

    def Reba(self, angles, weight, coupling):
        # Placeholder com retorno fixo
        return [2, 3, 5, 2, 2, 2, 3, 2, 1, 0]

    def Rula(self, angles, weight, activity):
        # Placeholder com retorno fixo
        return [1, 2, 3, 1, 2, 2, 2, 2, 1, 0]
