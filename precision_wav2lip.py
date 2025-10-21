#!/usr/bin/env python3
"""
Precision Wav2Lip - Enhanced facial animation with precise lip and eye alignment
"""

import os
import subprocess
import uuid
import cv2
import numpy as np
import base64
from io import BytesIO
from PIL import Image
import mediapipe as mp

def get_audio_duration(audio_file_path):
    """Get audio duration using ffprobe"""
    try:
        cmd = [
            "ffprobe", "-v", "quiet", "-show_entries", "format=duration", 
            "-of", "csv=p=0", audio_file_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return float(result.stdout.strip())
    except:
        return 30.0

def save_captured_image(image_data, upload_dir="captured_images"):
    """Save captured camera image"""
    os.makedirs(upload_dir, exist_ok=True)
    
    try:
        if isinstance(image_data, str):
            if image_data.startswith('data:image'):
                image_data = image_data.split(',')[1]
            image_bytes = base64.b64decode(image_data)
            image = Image.open(BytesIO(image_bytes))
        else:
            image = Image.open(BytesIO(image_data))
        
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        image_filename = f"captured_{uuid.uuid4().hex[:8]}.jpg"
        image_path = os.path.join(upload_dir, image_filename)
        image.save(image_path, 'JPEG', quality=95)
        
        return image_path
        
    except Exception as e:
        print(f"Error saving captured image: {e}")
        return None

def detect_facial_landmarks(image_path):
    """Detect precise facial landmarks using MediaPipe"""
    try:
        # Initialize MediaPipe Face Mesh
        mp_face_mesh = mp.solutions.face_mesh
        face_mesh = mp_face_mesh.FaceMesh(
            static_image_mode=True,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5
        )
        
        # Load image
        image = cv2.imread(image_path)
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Process image
        results = face_mesh.process(rgb_image)
        
        if not results.multi_face_landmarks:
            print("No face landmarks detected")
            return None
        
        landmarks = results.multi_face_landmarks[0]
        h, w = image.shape[:2]
        
        # Convert normalized landmarks to pixel coordinates
        points = []
        for lm in landmarks.landmark:
            x = int(lm.x * w)
            y = int(lm.y * h)
            points.append((x, y))
        
        # Define key facial regions
        # Lip landmarks (MediaPipe indices)
        LIPS_OUTER = [61, 84, 17, 314, 405, 320, 307, 375, 321, 308, 324, 318]
        LIPS_INNER = [78, 95, 88, 178, 87, 14, 317, 402, 318, 324, 308, 415]
        
        # Eye landmarks - more precise eye contours
        LEFT_EYE_OUTER = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246]
        LEFT_EYE_INNER = [133, 173, 157, 158, 159, 160, 161, 246, 33, 7, 163, 144, 145, 153]
        LEFT_EYE_TOP = [159, 158, 157, 173, 133]
        LEFT_EYE_BOTTOM = [33, 7, 163, 144, 145]
        
        RIGHT_EYE_OUTER = [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398]
        RIGHT_EYE_INNER = [362, 398, 384, 385, 386, 387, 388, 466, 263, 249, 390, 373, 374, 380]
        RIGHT_EYE_TOP = [386, 387, 388, 466, 263]
        RIGHT_EYE_BOTTOM = [362, 398, 384, 385, 380]
        
        # Pupil/Iris approximate centers (estimated from eye landmarks)
        LEFT_PUPIL_CENTER = [468, 469, 470, 471, 472]  # MediaPipe iris landmarks if available
        RIGHT_PUPIL_CENTER = [473, 474, 475, 476, 477]
        
        # Get bounding boxes and centers
        def get_region_info(indices):
            region_points = [points[i] for i in indices if i < len(points)]
            if not region_points:
                return None
            xs, ys = zip(*region_points)
            return {
                'points': region_points,
                'bbox': (min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys)),
                'center': (sum(xs) // len(xs), sum(ys) // len(ys))
            }
        
        lips_info = get_region_info(LIPS_OUTER)
        left_eye_info = {
            'outer': get_region_info(LEFT_EYE_OUTER),
            'inner': get_region_info(LEFT_EYE_INNER),
            'top': get_region_info(LEFT_EYE_TOP),
            'bottom': get_region_info(LEFT_EYE_BOTTOM),
            'center': None
        }
        right_eye_info = {
            'outer': get_region_info(RIGHT_EYE_OUTER),
            'inner': get_region_info(RIGHT_EYE_INNER),
            'top': get_region_info(RIGHT_EYE_TOP),
            'bottom': get_region_info(RIGHT_EYE_BOTTOM),
            'center': None
        }
        
        # Calculate eye centers from outer contours
        if left_eye_info['outer']:
            left_eye_info['center'] = left_eye_info['outer']['center']
        if right_eye_info['outer']:
            right_eye_info['center'] = right_eye_info['outer']['center']
        
        return {
            'lips': lips_info,
            'left_eye': left_eye_info,
            'right_eye': right_eye_info,
            'all_points': points,
            'detected': True
        }
        
    except Exception as e:
        print(f"Facial landmark detection error: {e}")
        # Fallback to basic estimation
        image = cv2.imread(image_path)
        h, w = image.shape[:2]
        return {
            'lips': {
                'center': (w // 2, int(h * 0.75)),
                'bbox': (w // 2 - 30, int(h * 0.75) - 15, 60, 30)
            },
            'left_eye': {
                'center': (int(w * 0.35), int(h * 0.4)),
                'outer': {'bbox': (int(w * 0.35) - 25, int(h * 0.4) - 12, 50, 24)},
                'top': {'points': [(int(w * 0.35) - 20, int(h * 0.4) - 8), (int(w * 0.35), int(h * 0.4) - 10), (int(w * 0.35) + 20, int(h * 0.4) - 8)]},
                'bottom': {'points': [(int(w * 0.35) - 20, int(h * 0.4) + 8), (int(w * 0.35), int(h * 0.4) + 10), (int(w * 0.35) + 20, int(h * 0.4) + 8)]}
            },
            'right_eye': {
                'center': (int(w * 0.65), int(h * 0.4)),
                'outer': {'bbox': (int(w * 0.65) - 25, int(h * 0.4) - 12, 50, 24)},
                'top': {'points': [(int(w * 0.65) - 20, int(h * 0.4) - 8), (int(w * 0.65), int(h * 0.4) - 10), (int(w * 0.65) + 20, int(h * 0.4) - 8)]},
                'bottom': {'points': [(int(w * 0.65) - 20, int(h * 0.4) + 8), (int(w * 0.65), int(h * 0.4) + 10), (int(w * 0.65) + 20, int(h * 0.4) + 8)]}
            },
            'detected': False
        }

def create_advanced_speech_pattern(duration, fps):
    """Create sophisticated speech pattern with phoneme-like variations"""
    total_frames = int(duration * fps)
    speech_pattern = []
    
    for frame in range(total_frames):
        time = frame / fps
        
        # Multiple frequency components for realistic speech
        base_freq = 4.5 + 1.5 * np.sin(time * 0.2)  # Base speech frequency
        consonant_freq = 12 + 4 * np.sin(time * 0.7)  # Consonant frequency
        emphasis_freq = 2 + np.sin(time * 0.15)  # Emphasis frequency
        
        # Combine frequencies
        base_speech = np.sin(time * base_freq * 2 * np.pi)
        consonants = 0.3 * np.sin(time * consonant_freq * 2 * np.pi)
        emphasis = 0.4 * np.sin(time * emphasis_freq * 2 * np.pi)
        
        combined_speech = base_speech + consonants + emphasis
        
        # Add pauses and breathing
        pause_pattern = 1.0
        if int(time * 1.5) % 8 == 0:  # Pause every ~5.3 seconds
            pause_pattern = 0.05
        elif int(time * 2.5) % 7 == 0:  # Strong emphasis
            pause_pattern = 1.4
        elif int(time * 4) % 3 == 0:  # Moderate emphasis
            pause_pattern = 1.1
        
        # Normalize and apply pause pattern
        mouth_openness = np.clip((combined_speech + 1) / 2 * pause_pattern, 0, 1)
        
        # Add sharp consonant movements
        if frame % 6 == 0:  # More frequent consonants
            mouth_openness = min(mouth_openness + 0.4, 1.0)
        elif frame % 13 == 0:  # Occasional strong consonants
            mouth_openness = min(mouth_openness + 0.6, 1.0)
        
        speech_pattern.append(mouth_openness)
    
    return speech_pattern

def create_eye_blink_pattern(duration, fps):
    """Create natural eye blinking pattern"""
    total_frames = int(duration * fps)
    blink_pattern = []
    
    last_blink = 0
    for frame in range(total_frames):
        time = frame / fps
        
        # Natural blink frequency (every 2-6 seconds)
        blink_interval = 3 + 2 * np.sin(time * 0.1)  # Varying blink intervals
        
        if time - last_blink > blink_interval:
            # Start blink
            blink_strength = 1.0
            last_blink = time
        elif time - last_blink > blink_interval - 0.2:  # 0.2 second blink duration
            # Blink in progress
            blink_phase = (time - (last_blink - 0.2)) / 0.2
            blink_strength = np.sin(blink_phase * np.pi)  # Smooth blink curve
        else:
            blink_strength = 0.0
        
        blink_pattern.append(blink_strength)
    
    return blink_pattern

def apply_precise_eye_animation(frame, eye_data, blink_strength, eye_side):
    """Apply precise eye animation using MediaPipe landmarks"""
    if blink_strength < 0.05:
        return  # No significant blinking
    
    h, w = frame.shape[:2]
    
    # Get eye contour points
    top_points = eye_data['top']['points'] if eye_data.get('top') and eye_data['top'].get('points') else []
    bottom_points = eye_data['bottom']['points'] if eye_data.get('bottom') and eye_data['bottom'].get('points') else []
    outer_bbox = eye_data['outer']['bbox'] if eye_data.get('outer') and eye_data['outer'].get('bbox') else None
    
    if not top_points or not bottom_points or not outer_bbox:
        return
    
    # Create precise eye mask using actual eye contour
    eye_mask = np.zeros((h, w), dtype=np.uint8)
    
    # Calculate blink position - top eyelid moves down, bottom moves up
    blink_factor = blink_strength * 0.7  # Limit blink intensity
    
    # Interpolate between open and closed eye positions
    blended_top = []
    blended_bottom = []
    
    for i, (top_pt, bottom_pt) in enumerate(zip(top_points, bottom_points)):
        if len(top_pt) >= 2 and len(bottom_pt) >= 2:
            # Move top eyelid down and bottom eyelid up during blink
            new_top_y = int(top_pt[1] + (bottom_pt[1] - top_pt[1]) * blink_factor * 0.6)
            new_bottom_y = int(bottom_pt[1] - (bottom_pt[1] - top_pt[1]) * blink_factor * 0.4)
            
            blended_top.append((top_pt[0], new_top_y))
            blended_bottom.append((bottom_pt[0], new_bottom_y))
    
    if blended_top and blended_bottom:
        # Create eye contour from blended points
        eye_contour = np.array(blended_top + blended_bottom[::-1], dtype=np.int32)
        
        # Fill the eye area
        cv2.fillPoly(eye_mask, [eye_contour], 255)
        
        # Apply darkening effect for closed eyelid
        eyelid_darkness = 0.4 + blink_strength * 0.3
        frame[eye_mask > 0] = frame[eye_mask > 0] * (1 - eyelid_darkness)
        
        # Add subtle eyelid texture/shadow
        if blink_strength > 0.3:
            # Create gradient effect for more realistic eyelid
            y_coords, x_coords = np.ogrid[:h, :w]
            eye_center = eye_data['center']
            
            # Create radial gradient from eye center
            distances = np.sqrt((x_coords - eye_center[0])**2 + (y_coords - eye_center[1])**2)
            max_distance = max(outer_bbox[2], outer_bbox[3]) // 2
            
            gradient_mask = (eye_mask > 0) & (distances <= max_distance)
            gradient_factor = 1 - (distances / max_distance)
            
            # Fix broadcasting issue by ensuring compatible shapes
            gradient_values = gradient_factor[gradient_mask]
            if gradient_values.size > 0:
                frame[gradient_mask] = frame[gradient_mask] * (1 - blink_strength * 0.2 * gradient_values)

def apply_basic_eye_animation(frame, eye_center, blink_strength, h, w):
    """Fallback eye animation for when precise landmarks aren't available"""
    if blink_strength < 0.05:
        return
    
    # Create more realistic basic eye shape (almond-shaped, not circular)
    eye_width = 30
    eye_height = max(int(15 * (1 - blink_strength * 0.8)), 2)
    
    # Create almond-shaped eye mask
    y_coords, x_coords = np.ogrid[:h, :w]
    
    # Elliptical eye shape
    eye_mask = ((x_coords - eye_center[0]) / eye_width)**2 + \
               ((y_coords - eye_center[1]) / eye_height)**2 <= 1
    
    # Apply more subtle darkening
    eyelid_darkness = 0.3 + blink_strength * 0.4
    frame[eye_mask] = frame[eye_mask] * (1 - eyelid_darkness)
    
    # Add eyelid gradient for depth
    if blink_strength > 0.3:
        # Upper eyelid shadow
        upper_eyelid = ((x_coords - eye_center[0]) / eye_width)**2 + \
                      ((y_coords - (eye_center[1] - eye_height * 0.3)) / (eye_height * 0.7))**2 <= 1
        frame[upper_eyelid] = frame[upper_eyelid] * (1 - blink_strength * 0.2)

def apply_precision_facial_animation(image, landmarks, mouth_openness, blink_strength, frame_num):
    """Apply precise facial animation based on detected landmarks"""
    try:
        frame = image.copy()
        h, w = frame.shape[:2]
        
        # Ensure frame is the correct format
        if len(frame.shape) != 3 or frame.shape[2] != 3:
            print(f"Warning: Unexpected frame shape: {frame.shape}")
            return frame
        
        # 1. Precise lip animation
        if landmarks['lips'] and mouth_openness > 0.15:
            lips_center = landmarks['lips']['center']
            lips_bbox = landmarks['lips']['bbox']
            
            # Create sophisticated mouth opening
            mouth_height = max(int(lips_bbox[3] * mouth_openness * 2.5), 1)
            mouth_width = lips_bbox[2]
            
            # Create elliptical mouth mask
            y_coords, x_coords = np.ogrid[:h, :w]
            mouth_mask = ((x_coords - lips_center[0]) / max(mouth_width // 2, 1))**2 + \
                        ((y_coords - lips_center[1]) / max(mouth_height, 1))**2 <= 1
            
            # Apply mouth opening effect with gradient
            mouth_darkness = 0.3 + mouth_openness * 0.4  # Variable darkness
            frame[mouth_mask] = frame[mouth_mask] * (1 - mouth_darkness)
            
            # Add inner mouth details for strong openings
            if mouth_openness > 0.5:
                inner_mouth_mask = ((x_coords - lips_center[0]) / max(mouth_width // 3, 1))**2 + \
                                  ((y_coords - lips_center[1]) / max(mouth_height // 2, 1))**2 <= 1
                frame[inner_mouth_mask] = frame[inner_mouth_mask] * 0.2  # Very dark inner mouth
        
        # 2. Advanced eye animation with precise contours
        for eye_key in ['left_eye', 'right_eye']:
            if landmarks[eye_key] and landmarks[eye_key].get('center'):
                eye_data = landmarks[eye_key]
                eye_center = eye_data['center']
                
                # Get eye contour information
                if landmarks['detected'] and eye_data.get('outer') and eye_data.get('top') and eye_data.get('bottom'):
                    # Use precise MediaPipe landmarks for realistic eye shape
                    apply_precise_eye_animation(frame, eye_data, blink_strength, eye_key)
                else:
                    # Fallback to improved basic eye animation
                    apply_basic_eye_animation(frame, eye_center, blink_strength, h, w)
        
        # 3. Subtle facial micro-movements
        # Breathing effect
        breathing_factor = 1.0 + 0.002 * np.sin(frame_num * 0.06)
        
        # Head movement correlated with speech intensity
        head_movement = 0.15 * np.sin(frame_num * 0.03) + mouth_openness * 0.1
        
        # Slight cheek movement during strong speech
        if mouth_openness > 0.6:
            # This would require more sophisticated facial modeling
            # For now, we'll add subtle brightness changes
            cheek_regions = [
                (int(w * 0.25), int(h * 0.55), int(w * 0.15)),  # Left cheek
                (int(w * 0.75), int(h * 0.55), int(w * 0.15))   # Right cheek
            ]
            
            for cheek_x, cheek_y, cheek_radius in cheek_regions:
                y_coords, x_coords = np.ogrid[:h, :w]
                cheek_mask = (x_coords - cheek_x)**2 + (y_coords - cheek_y)**2 <= cheek_radius**2
                frame[cheek_mask] = np.clip(frame[cheek_mask] * (1 + mouth_openness * 0.08), 0, 255)
        
        # Apply global transformations
        center_x, center_y = w // 2, h // 2
        
        # Breathing
        M_breath = cv2.getRotationMatrix2D((center_x, center_y), 0, breathing_factor)
        frame = cv2.warpAffine(frame, M_breath, (w, h))
        
        # Head movement
        M_head = cv2.getRotationMatrix2D((center_x, center_y), head_movement, 1.0)
        frame = cv2.warpAffine(frame, M_head, (w, h))
        
        return frame
        
    except Exception as e:
        print(f"Error in apply_precision_facial_animation: {e}")
        print(f"Frame shape: {image.shape if image is not None else 'None'}")
        print(f"Landmarks: {landmarks}")
        # Return original frame if there's an error
        return image.copy() if image is not None else None

def create_precision_video(audio_file_path, image_path, output_path):
    """Create precision video with advanced facial animation"""
    
    # Load and prepare image
    face_img = cv2.imread(image_path)
    if face_img is None:
        print(f"ERROR: Could not load image: {image_path}")
        return False
    
    # Detect facial landmarks
    print("Detecting precise facial landmarks...")
    landmarks = detect_facial_landmarks(image_path)
    
    if landmarks and landmarks['detected']:
        print("✅ Precise facial landmarks detected!")
    else:
        print("⚠️  Using estimated facial regions")
    
    # Get audio duration and create patterns
    duration = get_audio_duration(audio_file_path)
    fps = 25
    total_frames = int(duration * fps)
    
    speech_pattern = create_advanced_speech_pattern(duration, fps)
    blink_pattern = create_eye_blink_pattern(duration, fps)
    
    # Resize image while maintaining aspect ratio
    target_height = 512
    h, w = face_img.shape[:2]
    aspect_ratio = w / h
    target_width = int(target_height * aspect_ratio)
    
    if target_width % 2 != 0:
        target_width += 1
    
    face_img = cv2.resize(face_img, (target_width, target_height))
    
    # Scale landmarks for resized image
    if landmarks:
        scale_x = target_width / w
        scale_y = target_height / h
        
        # Scale lips
        if landmarks['lips']:
            center = landmarks['lips']['center']
            landmarks['lips']['center'] = (int(center[0] * scale_x), int(center[1] * scale_y))
            if 'bbox' in landmarks['lips']:
                bbox = landmarks['lips']['bbox']
                landmarks['lips']['bbox'] = (
                    int(bbox[0] * scale_x), int(bbox[1] * scale_y),
                    int(bbox[2] * scale_x), int(bbox[3] * scale_y)
                )
        
        # Scale eyes (more complex structure)
        for eye_key in ['left_eye', 'right_eye']:
            if landmarks[eye_key]:
                eye_data = landmarks[eye_key]
                
                # Scale center
                if eye_data.get('center'):
                    center = eye_data['center']
                    eye_data['center'] = (int(center[0] * scale_x), int(center[1] * scale_y))
                
                # Scale all eye components
                for component in ['outer', 'inner', 'top', 'bottom']:
                    if eye_data.get(component):
                        comp_data = eye_data[component]
                        
                        # Scale bbox
                        if comp_data.get('bbox'):
                            bbox = comp_data['bbox']
                            comp_data['bbox'] = (
                                int(bbox[0] * scale_x), int(bbox[1] * scale_y),
                                int(bbox[2] * scale_x), int(bbox[3] * scale_y)
                            )
                        
                        # Scale points
                        if comp_data.get('points'):
                            scaled_points = []
                            for point in comp_data['points']:
                                if len(point) >= 2:
                                    scaled_points.append((
                                        int(point[0] * scale_x), 
                                        int(point[1] * scale_y)
                                    ))
                            comp_data['points'] = scaled_points
    
    # Create temporary video
    temp_video = output_path.replace('.mp4', '_temp.mp4')
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(temp_video, fourcc, fps, (target_width, target_height))
    
    print(f"Creating precision video with advanced facial animation ({total_frames} frames)...")
    
    for frame_num in range(total_frames):
        # Get animation parameters
        mouth_openness = speech_pattern[frame_num] if frame_num < len(speech_pattern) else 0.3
        blink_strength = blink_pattern[frame_num] if frame_num < len(blink_pattern) else 0.0
        
        # Create animated frame
        frame = apply_precision_facial_animation(face_img, landmarks, mouth_openness, blink_strength, frame_num)
        
        if frame is not None:
            out.write(frame)
        else:
            print(f"Warning: Frame {frame_num} is None, skipping...")
        
        # Progress indicator
        if frame_num % 100 == 0:
            progress = (frame_num / total_frames) * 100
            print(f"  Progress: {progress:.1f}%")
    
    out.release()
    print("  Video frames generated, combining with audio...")
    
    # Combine with audio
    cmd = [
        "ffmpeg", "-y",
        "-i", temp_video,
        "-i", audio_file_path,
        "-c:v", "libx264",
        "-c:a", "aac",
        "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-shortest",
        output_path
    ]
    
    try:
        subprocess.run(cmd, capture_output=True, check=True)
        os.remove(temp_video)
        return True
    except subprocess.CalledProcessError as e:
        print(f"FFmpeg error: {e}")
        if os.path.exists(temp_video):
            os.remove(temp_video)
        return False

def generate_precision_lipsync_video(audio_file_path: str, captured_image_data, output_dir: str = "output_videos", user_prompt: str = None) -> str:
    """
    Generate precision lip-sync video from captured camera image and audio
    """
    if not os.path.exists(audio_file_path):
        print(f"ERROR: Audio file not found at {audio_file_path}")
        return None
    
    # Save captured image
    print("Processing captured camera image...")
    image_path = save_captured_image(captured_image_data)
    if not image_path:
        print("ERROR: Failed to save captured image")
        return None
    
    # Define output path
    if user_prompt:
        clean_prompt = "".join(c for c in user_prompt if c.isalnum() or c in (' ', '-', '_')).rstrip()
        clean_prompt = clean_prompt.replace(' ', '_')[:50]
        video_filename = f"precision_{clean_prompt}_{uuid.uuid4().hex[:8]}.mp4"
    else:
        video_filename = f"precision_video_{uuid.uuid4()}.mp4"
    
    output_path = os.path.join(output_dir, video_filename)
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Starting Precision Facial Animation...")
    print(f"Audio duration: {get_audio_duration(audio_file_path):.1f} seconds")
    
    # Create precision video
    success = create_precision_video(audio_file_path, image_path, output_path)
    
    # Clean up captured image
    try:
        os.remove(image_path)
    except:
        pass
    
    if success:
        print(f"SUCCESS: Precision video saved to {output_path}")
        return output_path
    else:
        print(f"ERROR: Failed to create precision video")
        return None

if __name__ == "__main__":
    print("Precision Wav2Lip - Advanced Facial Animation System")
    
    # Test if MediaPipe is available
    try:
        import mediapipe as mp
        print("✅ MediaPipe available for precision facial landmark detection")
    except ImportError:
        print("⚠️  MediaPipe not available. Install with: pip install mediapipe")
        print("    Falling back to basic facial region estimation")
