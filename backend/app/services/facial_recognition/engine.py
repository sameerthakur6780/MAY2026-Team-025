"""Thin wrapper around deepface. Nothing outside this package should import
deepface/cv2/numpy directly -- swapping the underlying library later means
changing only this file."""

import cv2
import numpy as np
from flask import current_app


class FaceDetectionError(Exception):
    def __init__(self, message, code="face_detection_error"):
        super().__init__(message)
        self.code = code


def _decode_image(image_bytes):
    arr = np.frombuffer(image_bytes, dtype=np.uint8)
    image = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if image is None:
        raise FaceDetectionError("Could not decode image -- file may be corrupt or not a valid image", "invalid_image")
    return image


def _represent(image_bytes, enforce_detection):
    from deepface import DeepFace
    from deepface.modules.exceptions import FaceNotDetected

    image = _decode_image(image_bytes)
    model_name = current_app.config["FACE_MODEL_NAME"]
    detector_backend = current_app.config["FACE_DETECTOR_BACKEND"]
    try:
        return DeepFace.represent(
            img_path=image,
            model_name=model_name,
            detector_backend=detector_backend,
            enforce_detection=enforce_detection,
        )
    except FaceNotDetected:
        # Only reachable when enforce_detection=True -- with False, deepface
        # never raises this (see detect_faces below for what it does instead).
        return []


def compute_profile_embedding(image_bytes):
    """For a single student's profile photo. Requires exactly one face."""
    faces = _represent(image_bytes, enforce_detection=True)
    if len(faces) == 0:
        raise FaceDetectionError("No face detected in the photo", "no_face_detected")
    if len(faces) > 1:
        raise FaceDetectionError(
            "Multiple faces detected -- the profile photo must contain only the student",
            "multiple_faces_detected",
        )
    return faces[0]["embedding"]


def detect_faces(image_bytes):
    """For a classroom photo. Returns a list of {embedding, bbox} for every
    detected face -- zero faces is a valid, non-error result here.

    enforce_detection=False so a photo with zero real faces doesn't raise --
    but deepface's actual behavior in that case isn't an empty list, it's a
    single dummy entry covering the *whole image* with face_confidence=0
    (verified against deepface==0.0.100 source). That has to be filtered out
    here or it gets treated as a genuine (garbage) face to match against."""
    faces = _represent(image_bytes, enforce_detection=False)
    return [
        {"embedding": f["embedding"], "bbox": f["facial_area"]}
        for f in faces
        if f.get("face_confidence", 0) > 0
    ]


def _cosine_similarity(a, b):
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    denom = float(np.linalg.norm(a) * np.linalg.norm(b))
    if denom == 0:
        return 0.0
    return max(0.0, float(np.dot(a, b) / denom))


def match_embedding(probe_embedding, candidates):
    """candidates: list of (student_id, embedding) pairs. Returns
    (best_student_id, best_confidence), or (None, 0.0) if candidates is empty."""
    best_id, best_score = None, 0.0
    for student_id, embedding in candidates:
        score = _cosine_similarity(probe_embedding, embedding)
        if score > best_score:
            best_id, best_score = student_id, score
    return best_id, best_score
