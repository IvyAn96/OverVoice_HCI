import dlib
import cv2

import sys
import numpy as np

import time
from datetime import datetime

def initialize():
    """
    Initializing the dlib functions used throughtout the program
    These detect the face, and predict the location of the facial landmarks

    Parameters
    ----------

    Returns
    ----------
    detector : detector object (dlib)
        A frontal face detector object produced by the dlib
    predictor: predictor object (dlib)
        An object to predict facial landmark points using dlib

    """
    detector = dlib.get_frontal_face_detector()
    # download the predictor file at: http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2
    predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")

    return detector, predictor


def rect_to_bb(rect):
    """
    Take a rect object predicted by dlib and return the x,y corner coordinates
    and the width and height of the rectangle in (x, y, w, h) tuple format.

    Parameters
    ----------
    rect : rect object (dlib)
        rect object generated by dlib frontal face detector

    Returns
    ----------
    (x,y,w,h) : tuple
        tuple with corner, height and wight of bounding box

    """
    x = rect.left()
    y = rect.top()
    w = rect.right() - x
    h = rect.bottom() - y

    return (x, y, w, h)


def shape_to_np(shape, dtype="int"):
    """
    Take a shape object (that is generated by dlib predictor) and convert that
    into an array containing (x,y) tuples for the coordinates of the facial
    landmark points

    Parameters
    ----------
    shape : shape object (dlib)
        shape object generated by dlib predictor

    Returns
    ----------
    coords : array
        array containing (x,y) tuples for the coordinates of the facial landmark
        points
    """
    coords = np.zeros((68, 2), dtype=dtype)
    # [(0,0),(0,0),(0,0)....68 times]
    # Shape object has 68 landmark points. We extract a landmark point by calculating
    # shape.part(<landmark_number>)
    for i in range(0, 68):
        coords[i] = (shape.part(i).x, shape.part(i).y)
    # coords now looks something like [(12,15),(24,78)....68 times]
    return coords


def detect_action_units(shape_coords, rect):
    """
    Detects the presence of action units

    Parameters
    ----------
    shape : array[array]
        contains (x,y) coordinates of 68 facial landmark points
    rect : rect object (dlib)
        rect object generated by dlib frontal face detector

    Returns
    ----------
    au_array : array
        Array identifying action units, 1 indicating presence, 0 otherwise
        Refer array position under Main codes at:
        https://en.wikipedia.org/wiki/Facial_Action_Coding_System
    """

    # Potential idea can be to normalize the landmark points wrt a particular
    # landmark point (for eg. point 27, located between te eyes that has a
    # relatively fixed position)
    au_array = [0]*29
    (x, y, w, h) = rect_to_bb(rect)

    # Indentifying Action Unit 12: Lip Corner Puller
    left_lip_corner_x, left_lip_corner_y = shape_coords[48]
    right_lip_corner_x, right_lip_corner_y = shape_coords[54]

    # distance between the corners = right_lip_corner_x - left_lip_corner_x

    # print((right_lip_corner_x - left_lip_corner_x)/w)

    # 0.32 comes from calculating the neutral difference between the lip corners
    # which can be calculated using: (right_lip_corner_x - left_lip_corner_x)/w
    smile_param = 0.09 # can be adjusted for different faces
    if (((right_lip_corner_x - left_lip_corner_x)/w)>0.32+smile_param):
        au_array[12] = 1



    # Identifying Action Unit 5(Upper Lid Raiser)

    eyelid_upper_x, eyelid_upper_y = shape_coords[37]
    eyelid_lower_x, eyelid_lower_y = shape_coords[41]

    eyes_wide_param = 0.05

    if((eyelid_lower_y - eyelid_upper_y)/h > eyes_wide_param):
        au_array[5] = 1


    # Identifying Action Unit 26(Jaw Drop)

    mouth_upper_x, mouth_upper_y = shape_coords[62]
    mouth_lower_x, mouth_lower_y = shape_coords[66]

    # The neutral difference between the lips was ~0.03
    jaw_drop_param = 0.055
    if((mouth_lower_y - mouth_upper_y)/h > jaw_drop_param):
        au_array[26] = 1


    # Identifying Action Unit 4(Brow Lowerer) approximated to eye brows moving closer

    left_brow_corner_x, left_brow_corner_y = shape_coords[21]
    right_brow_corner_x, right_brow_corner_y = shape_coords[22]

    # The Neurtal difference between the inner brow corners was ~0.17
    brow_lowerer_param = 0.14
    if((right_brow_corner_x - left_brow_corner_x)/w < 0.14):
        au_array[4] = 1



    # Fill in code to identify Different Action Units

    return au_array


def identify_expression(au_array, frame, rect):
    """
    Identifies facial expression based on action unit array values

    Parameters
    ----------
    au_array : array
        Action Unit array generated by the detect_action_units function
    frame : frame object (OpenCV)
        OpenCV frame produced using the VideoCapture Function
    rect : rect object (dlib)
        rect object generated by dlib frontal face detector

    Returns
    ----------
    updated_frame : frame object (OpenCV)
        Image frame with an identifier for facial expressions
    """

    # Happines, Surprise, Angry

    (x, y, w, h) = rect_to_bb(rect)
    # Expression for Happiness is AU 6 + AU 12
    # Currently only using AU 12
    if au_array[12]==1:
        cv2.putText(frame, "Happiness", (x-10, y-10),
        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 2)
        return frame

    # Expression for Surprise is AU 5 + AU 26
    elif au_array[5]==1 and au_array[26]==1:
        cv2.putText(frame, "Surprise", (x-10, y-10),
        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 2)
        return frame

    # Expression for Anger is AU 4(Brow Lowerer),5(Upper Lid Raiser), and optionally 23
    elif au_array[4]==1 and au_array[5]==1:
        cv2.putText(frame, "Anger", (x-10, y-10),
        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 2)
        return frame

    else:
        cv2.putText(frame, "Neutral", (x-10, y-10),
        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 2)
        return frame
    # elif au_array[4]==1 and au_array[5]==1 and au_array[23]==1:


    return frame


def stream_start():
    """
    Starts the video stream to process facial expressions and opens up a Video
    window when a face is detected

    Parameters
    ----------

    Returns
    ----------
    Press the Esc key to exit the program
    """

    print("Preparing the Program (3sec)")
    detector, predictor = initialize()
    time.sleep(3.0)


    print("[INFO] Starting Camera...")
    cap = cv2.VideoCapture(0)

    while True:

        ret, frame = cap.read()
        keyPress = 0
        if cap.isOpened():
            # Convert image to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            rects = detector(gray, 0)

            for rect in rects:
                # determine the facial landmarks for the face region, then
                # convert the facial landmark (x, y)-coordinates to a NumPy
                # array
                shape = predictor(gray, rect)
                shape_coords = shape_to_np(shape)

                # We create the red dots here
                for (x, y) in shape_coords:
                    cv2.circle(frame, (x, y), 1, (0, 0, 255), -1)

                (x, y, w, h) = rect_to_bb(rect)
                cv2.rectangle(frame, (x, y), (x+h, y+h), (0, 255, 0), 2)

                au_array = detect_action_units(shape_coords, rect)

                updated_frame = identify_expression(au_array,frame,rect)

                cv2.imshow("Frame",updated_frame)
                keyPress = cv2.waitKey(1)
                # if keyPress==27: # ASCII for Esc Key
                #     break

            if keyPress==27: # ASCII for Esc Key
                break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    stream_start()
