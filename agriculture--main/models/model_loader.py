import cv2

def load_model():
    """
    Loads YOLO model and returns:
    - net: neural network
    - classes: list of class names
    - output_layers: YOLO output layers
    """

    weights_path = "models/yolov3.weights"
    config_path = "models/yolov3.cfg"
    names_path = "models/coco.names"

    # Load YOLO network
    net = cv2.dnn.readNet(weights_path, config_path)

    # Try to use GPU, fallback to CPU
    try:
        net.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)
        net.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA)
    except:
        net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
        net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)

    # Load class names
    with open(names_path, "r") as f:
        classes = [line.strip() for line in f.readlines()]

    # Get output layer names
    layer_names = net.getLayerNames()
    output_layers = [layer_names[i - 1] for i in net.getUnconnectedOutLayers()]

    return net, classes, output_layers
