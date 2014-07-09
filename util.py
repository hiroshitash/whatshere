import traceback
import math
import sys


def log_exception_error(logger, msg):
    logger.error("%s" % msg)
    logger.error("%s", sys.exc_info()[0])
    logger.error("%s", traceback.format_exc())


def calc_approximate_distance(loc1, loc2):
    """Calculates approximate distance between two locations. 
    Assume each location to be tuple of (longitude, latitude).
    Approximate distance in miles between 2 points (longitude, latitude):
    sqrt(x * x + y * y)
    where x = 69.1 * (lat2 - lat1) and y = 53.0 * (lon2 - lon1)         
    """
    assert(isinstance(loc1, tuple) and isinstance(loc2, tuple))

    y = 53.0 * (float(loc1[0]) - float(loc2[0]))
    x = 69.1 * (float(loc1[1]) - float(loc2[1]))
    return math.sqrt(x * x + y * y)
