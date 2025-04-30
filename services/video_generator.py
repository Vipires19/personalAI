# personal_comparator/services/video_generator.py

import cv2
import numpy as np
import mediapipe as mp
import os
from mediapipe.framework.formats import landmark_pb2

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
    """Gera vídeo comparativo lado a lado usando frames e landmarks extraídos."""

    if len(frames_ref) == 0 or len(frames_exec) == 0:
        return None

    # Definindo resolução alvo
    target_width = 640
    target_height = 360

    fps = 30  # pode ser ajustado conforme a origem do vídeo
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    temp_output_path = "temp_comparative_video.mp4"
    #fourcc = cv2.VideoWriter_fourcc(*'MJPG')
    #temp_output_path = "temp_comparative_video.avi"
    out = cv2.VideoWriter(temp_output_path, fourcc, fps, (target_width * 2, target_height))

    min_frames = max(len(frames_ref), len(frames_exec))

    for i in range(min_frames):
        # Se acabou os frames, mantém o último frame
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

        combined_frame = np.hstack((frame_ref, frame_exec))
        out.write(combined_frame)


    out.release()

    if os.path.exists(temp_output_path):
        print("Vídeo gerado com sucesso:", temp_output_path)
        print("Tamanho do arquivo:", os.path.getsize(temp_output_path))
    else:
        print("⚠️ Arquivo de vídeo não encontrado!")

    # Lê o arquivo final para o Streamlit
    with open(temp_output_path, "rb") as f:
        video_bytes = f.read()

    os.remove(temp_output_path)  # limpa o arquivo temporário
    return video_bytes
