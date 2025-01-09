import cv2
import sys
import json
import base64
from datetime import datetime
import os

def ensure_dirs():
    os.makedirs('../images', exist_ok=True)
    os.makedirs('../videos', exist_ok=True)

def take_photo():
    try:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            return json.dumps({"status": "error", "message": "Nie można uzyskać dostępu do kamery"})
        
        ret, frame = cap.read()
        cap.release()
        
        if not ret:
            return json.dumps({"status": "error", "message": "Nie można zrobić zdjęcia"})
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"../images/zdjecie_{timestamp}.jpg"
        ensure_dirs()
        
        cv2.imwrite(filename, frame)
        return json.dumps({"status": "success", "path": filename})
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

def record_video(duration: int = 5) -> str:
    try:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            return json.dumps({"status": "error", "message": "Nie można uzyskać dostępu do kamery"})
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"../videos/nagranie_{timestamp}.avi"
        ensure_dirs()
        
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        out = cv2.VideoWriter(filename, fourcc, 20.0, (640,480))
        
        frames_to_capture = duration * 20  # 20 fps * duration
        frame_count = 0
        
        while frame_count < frames_to_capture:
            ret, frame = cap.read()
            if not ret:
                break
            out.write(frame)
            frame_count += 1
        
        if not os.path.exists(filename):
            return json.dumps({"status": "error", "message": "Nie udało się zapisać pliku wideo"})
        
        return json.dumps({"status": "success", "path": filename})
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})
    finally:
        cap.release()
        out.release()

if __name__ == "__main__":
    try:
        command = sys.argv[1] if len(sys.argv) > 1 else None
        
        if command == "photo":
            print(take_photo())
        elif command == "video":
            duration = int(sys.argv[2]) if len(sys.argv) > 2 else 5
            print(record_video(duration))
        else:
            print(json.dumps({"status": "error", "message": "Nieprawidłowa komenda"}))
    except Exception as e:
        print(json.dumps({"status": "error", "message": str(e)}))