# personal_comparator/services/video_generator.py

import cv2
import numpy as np
import mediapipe as mp
import os
from mediapipe.framework.formats import landmark_pb2
from moviepy.editor import ImageSequenceClip

mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose

def draw_landmarks_on_frame(frame, landmarks_list):
    """Desenha landmarks em um frame usando landmarks já extraídos."""
    if landmarks_list:
        mp_landmarks = landmark_pb2.NormalizedLandmarkList(landmark=landmarks_list)
        mp_drawing.draw_landmarks(
            frame,
            mp_landmarks,
            mp_pose.POSE_CONNECTIONS,
            landmark_drawing_spec=mp_drawing.DrawingSpec(color=(0,255,0), thickness=2, circle_radius=2),
            connection_drawing_spec=mp_drawing.DrawingSpec(color=(0,0,255), thickness=2, circle_radius=2)
        )
    return frame

def generate_comparative_video(frames_ref, landmarks_ref, frames_exec, landmarks_exec):
    """Gera vídeo comparativo lado a lado e retorna os bytes para exibição."""

    if len(frames_ref) == 0 or len(frames_exec) == 0:
        return None

    target_width = 640
    target_height = 360
    min_frames = max(len(frames_ref), len(frames_exec))
    combined_frames = []

    for i in range(min_frames):
        frame_ref = frames_ref[i] if i < len(frames_ref) else frames_ref[-1]
        frame_exec = frames_exec[i] if i < len(frames_exec) else frames_exec[-1]
        landmark_ref = landmarks_ref[i] if i < len(landmarks_ref) else landmarks_ref[-1]
        landmark_exec = landmarks_exec[i] if i < len(landmarks_exec) else landmarks_exec[-1]

        frame_ref = frame_ref.copy()
        frame_exec = frame_exec.copy()

        frame_ref = draw_landmarks_on_frame(frame_ref, landmark_ref)
        frame_exec = draw_landmarks_on_frame(frame_exec, landmark_exec)

        frame_ref = cv2.resize(frame_ref, (target_width, target_height))
        frame_exec = cv2.resize(frame_exec, (target_width, target_height))

        combined = np.hstack((frame_ref, frame_exec))
        combined_rgb = combined[..., ::-1]  # BGR → RGB
        combined_frames.append(combined_rgb)

    # Gera vídeo usando moviepy
    clip = ImageSequenceClip(combined_frames, fps=30)
    temp_output_path = "temp_comparative_video.mp4"
    clip.write_videofile(temp_output_path, codec="libx264", audio=False, verbose=False, logger=None)

    # Lê o vídeo como bytes
    with open(temp_output_path, "rb") as f:
        video_bytes = f.read()

    os.remove(temp_output_path)
    return video_bytes

