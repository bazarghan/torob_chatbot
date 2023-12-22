import numpy as np

def calc_cosine_similarity(vector1, vector2):

    # Calculate dot product
    dot_product = np.dot(vector1, vector2)

    # Calculate magnitudes
    magnitude1 = np.linalg.norm(vector1)
    magnitude2 = np.linalg.norm(vector2)

    # Calculate cosine similarity
    similarity = dot_product / (magnitude1 * magnitude2)

    return similarity

