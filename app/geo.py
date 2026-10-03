from math import asin, cos, radians, sin, sqrt


def distance_m(lat1, lon1, lat2, lon2):
    """Odległość w linii prostej (haversine), w metrach."""
    dlat, dlon = radians(lat2 - lat1), radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return 2 * 6_371_000 * asin(sqrt(a))
