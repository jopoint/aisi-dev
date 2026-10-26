"""Inverse of td_pose, solely for copied masks in a simulation test network."""
import math


def mask_transform(data, row):
    """Read the same float state used by the Motion shader; never use old poses."""
    hidden = (0.0,0.0,0.0,0.0)
    if data is None or data.shape != (6,6,4) or row not in range(5):
        return hidden
    x,y,rotation,valid = (float(v) for v in data[row,0])
    if (not all(math.isfinite(v) for v in (x,y,rotation,valid))
            or valid < .5 or not float(data[5,0,2]) >= .5):
        return hidden
    return ((x-250)*.0052, (250-y)*.0052, -rotation, 1.0)
