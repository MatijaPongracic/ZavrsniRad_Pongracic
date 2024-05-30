import os
import cv2
import tensorflow as tf
import numpy as np
import scipy.io
from math import sqrt

def distance(x1, y1, x2, y2):
    return sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

interpreter = tf.lite.Interpreter(model_path = "3.tflite")
interpreter.allocate_tensors()

tolerance = 0.1
threshold = 0.3
videos = {"videos\\baseball":"matdata\\0005.mat",
          "videos\\jumpingJacks":"matdata\\1083.mat",
          "videos\\guitar":"matdata\\1951.mat",
          "videos\\bowling":"matdata\\0532.mat",
          "videos\\jumpingRope":"matdata\\0989.mat"}

for key, value in videos.items():
    mat_file_path = value
    mat_data = scipy.io.loadmat(mat_file_path)

    action = mat_data["action"]
    x = mat_data["x"]
    y = mat_data["y"]
    visibility = mat_data["visibility"]
    train = mat_data["train"]
    bbox = mat_data["bbox"]
    dimensions = mat_data["dimensions"]
    nframes = mat_data["nframes"]

    joint_match = {1:6, #desno rame
                   2:5, #lijevo rame
                   3:8, #desni lakat
                   4:7, #lijevi lakat
                   5:10, #desni zglob
                   6:9, #lijevi zglob
                   7:12, #desni kuk
                   8:11, #lijevi kuk
                   9:14, #desno koljeno
                   10:13, #lijevo koljeno
                   11:16, #desni glezanj
                   12:15} #lijevi glezanj

    frame_files = [f for f in os.listdir(key)]
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()

    low = 0
    mid_low = 0
    mid_high = 0
    high = 0
    for i in range(len(frame_files)):
        image = cv2.imread(os.path.join(key, frame_files[i]))
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        img = tf.image.resize_with_pad(np.expand_dims(image_rgb, axis=0), 192, 192)
        input_image = tf.cast(img, dtype=tf.float32)

        interpreter.set_tensor(input_details[0]["index"], np.array(input_image))
        interpreter.invoke()
        keypoints_with_scores = interpreter.get_tensor(output_details[0]["index"])
        joints = keypoints_with_scores.reshape(17,3)
        for j in range(joints.shape[0]):
            if joints[j,2] < threshold:
                joints[j,0] = 0
                joints[j,1] = 0
        height, width, _ = image_rgb.shape
        for j in range(joints.shape[0]):
            joints[j,0] = joints[j,0] * height
            joints[j,1] = joints[j,1] * width

        tocno = 0
        visible_keypoints = 0
        if visibility[i, 8] == 0:
            dt = distance(x[i, 1], y[i, 1], x[i, 2], y[i, 2])  # udaljenost lijevog i desnog ramena
        else:
            dt = distance(x[i, 1], y[i, 1], x[i, 8], y[i, 8])  # udaljenost desnog ramena i lijevog kuka

        for key1, value1 in joint_match.items():
            if visibility[i, key1] == 0:
                continue  #Ako je tocka nevidljiva, ne racuna se
            else:
                visible_keypoints += 1
                d = distance(x[i, key1], y[i, key1], joints[value1, 1], joints[value1, 0])
                if d < tolerance * dt:
                    tocno += 1
        PDJ = float(tocno / visible_keypoints)

        if PDJ < 0.25:
            low += 1
        elif PDJ < 0.5:
            mid_low += 1
        elif PDJ < 0.75:
            mid_high += 1
        else:
            high += 1

        #for key2, value2 in joint_match.items():
        #    cv2.circle(image, (int(joints[value2,1]),int(joints[value2,0])), 5, (0, 0, 255), -1)
        #    cv2.circle(image, (int(x[i, key2]), int(y[i, key2])), 5, (0, 255, 0), -1)
        #cv2.imshow("Image", image)
        #cv2.waitKey(0)
        #cv2.destroyAllWindows()

    print(key + ":")
    print(f"0%-25%: {low}")
    print(f"25%-50%: {mid_low}")
    print(f"50%-75%: {mid_high}")
    print(f"75%-100%: {high}\n")
