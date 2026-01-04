def get_roi(frame):
    """
    Extract Region Of Interest from frame.
    We assume animals appear mostly in the lower half.
    """

    height, width, _ = frame.shape

    # Bottom 50% of the frame
    roi = frame[int(height * 0.5):, :]

    return roi
