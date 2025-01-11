import aiohttp
from aiohttp import web
import asyncio
import cv2
import json
import base64
from datetime import datetime
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CameraServer:
    def __init__(self, host="0.0.0.0", port=8080, facenet_url="http://localhost:8081", debug=True):
        self.host = host
        self.port = port
        self.facenet_url = facenet_url
        self.app = web.Application()
        self.debug = debug
        self.setup_routes()
        self.is_recording = False
        self.camera = None
        if self.debug:
            logger.setLevel(logging.DEBUG)
            logger.debug("CameraServer initialized in debug mode")
        
    def setup_routes(self):
        self.app.router.add_get('/health', self.health_check)
        self.app.router.add_post('/record', self.handle_record)
        self.app.router.add_post('/train', self.handle_train)
        self.app.on_startup.append(self.check_facenet_availability)

    async def check_facenet_availability(self, app):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.facenet_url}/health") as response:
                    if response.status == 200:
                        logger.info("Facenet server is available")
                    else:
                        logger.warning("Facenet server is not responding properly")
        except Exception as e:
            logger.error(f"Cannot connect to Facenet server: {e}")

    async def health_check(self, request):
        return web.Response(text=json.dumps({
            "status": "healthy",
            "is_recording": self.is_recording
        }), content_type='application/json')

    async def stream_frames(self, frames, session):
        if self.debug:
            logger.debug("=== Starting Frame Batch Processing ===")
            logger.debug(f"Total frames to process: {len(frames)}")
        
        BATCH_SIZE = 5
        best_match = {"match_found": False, "similarity": 0.0, "face_detected": False}
        
        for i in range(0, len(frames), BATCH_SIZE):
            batch = frames[i:i + BATCH_SIZE]
            frames_data = []
            
            for frame in batch:
                _, buffer = cv2.imencode('.jpg', frame)
                frame_bytes = base64.b64encode(buffer).decode('utf-8')
                frames_data.append(frame_bytes)
            
            try:
                if self.debug:
                    logger.debug(f"Sending batch {i//BATCH_SIZE + 1}/{(len(frames)-1)//BATCH_SIZE + 1} "
                               f"({len(frames_data)} frames)")
                async with session.post(
                    f"{self.facenet_url}/process_frames",
                    json={'frames': frames_data}
                ) as response:
                    result = await response.json()
                    if self.debug:
                        logger.debug(f"Batch response: {result}")
                        if result.get('face_detected', False):
                            logger.debug(f"Face detected with similarity: {result.get('similarity', 0):.4f}")
                    
                    if result.get('match_found', False):
                        if self.debug:
                            logger.debug("Match found - stopping further processing")
                        return result
                    elif result.get('face_detected', False) and result.get('similarity', 0) > best_match['similarity']:
                        best_match = result
                        if self.debug:
                            logger.debug(f"New best match found - similarity: {result.get('similarity', 0):.4f}")
                        
            except Exception as e:
                logger.error(f"Error processing frame batch: {e}")
                continue
        
        if self.debug:
            logger.debug(f"=== Batch Processing Completed - Best match: {best_match} ===")
        return best_match

    async def initialize_camera(self):
        if self.debug:
            logger.debug("Initializing camera")
        self.camera = cv2.VideoCapture(0)
        if not self.camera.isOpened():
            if self.debug:
                logger.debug("Failed to access camera")
            return False
        
        if self.debug:
            fps = self.camera.get(cv2.CAP_PROP_FPS)
            resolution = (
                int(self.camera.get(cv2.CAP_PROP_FRAME_WIDTH)),
                int(self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
            )
            logger.debug(f"Camera initialized - FPS: {fps}, Resolution: {resolution}")
        return True

    async def release_camera(self):
        if self.debug:
            logger.debug("Releasing camera resources")
        if self.camera is not None:
            self.camera.release()
            self.camera = None

    async def record_video(self, duration=1):
        if self.debug:
            logger.debug("=== Starting Recording Session ===")
        try:
            if not await self.initialize_camera():
                if self.debug:
                    logger.debug("=== Session Ended: Camera Initialization Failed ===")
                return {"status": "error", "message": "Cannot access camera"}

            fps = 20
            frames_to_capture = fps
            frame_count = 0
            frames = []
            
            if self.debug:
                logger.debug(f"Recording configuration - Target FPS: {fps}, "
                           f"Planned frames: {frames_to_capture}")
                logger.debug("=== Starting Frame Collection ===")

            start_time = datetime.now()
            while frame_count < frames_to_capture and self.is_recording:
                ret, frame = self.camera.read()
                if not ret:
                    if self.debug:
                        logger.debug("Failed to read frame from camera")
                    break
                frames.append(frame)
                frame_count += 1
                if self.debug and frame_count % 5 == 0:
                    logger.debug(f"Collected {frame_count}/{frames_to_capture} frames "
                               f"({(frame_count/frames_to_capture*100):.1f}%)")
                await asyncio.sleep(1/fps)

            if self.debug:
                elapsed_time = (datetime.now() - start_time).total_seconds()
                actual_fps = frame_count / elapsed_time
                logger.debug(f"=== Frame Collection Completed ===")
                logger.debug(f"Actual FPS: {actual_fps:.2f}, Total frames: {frame_count}")
                logger.debug("Releasing camera resources")
            
            await self.release_camera()
            self.is_recording = False

            if self.debug:
                logger.debug("=== Starting Frame Processing ===")

            async with aiohttp.ClientSession() as session:
                response = await self.stream_frames(frames, session)
                face_detected = response.get('face_detected', False)
                match_found = response.get('match_found', False)
                if match_found:
                    logger.info(f"Match found with similarity: {response.get('similarity', 0):.4f}")

            if self.debug:
                logger.debug("=== Recording Session Completed ===")
                logger.debug(f"Results - Face detected: {face_detected}, Match found: {match_found}")

            return {
                "status": "success" if match_found else "retry" if face_detected else "error",
                "frames_processed": frame_count,
                "face_detected": face_detected,
                "match_found": match_found
            }
        except Exception as e:
            logger.error(f"Error during recording: {e}")
            return {"status": "error", "message": str(e)}

    async def handle_record(self, request):
        if self.is_recording:
            return web.Response(
                text=json.dumps({"status": "error", "message": "Recording already in progress"}),
                content_type='application/json'
            )

        self.is_recording = True
        result = await self.record_video(1)
        
        if self.debug:
            logger.debug(f"Recording result: {result}")
        
        response = {
            "status": result["status"],
            "frames_processed": result.get("frames_processed", 0),
            "face_detected": result.get("face_detected", False),
            "match_found": result.get("match_found", False)
        }

        if result.get("message"):
            response["message"] = result["message"]
        elif result["status"] == "retry":
            response["message"] = "Face detected but not matched, try again"
        elif result["status"] == "error":
            response["message"] = "No face detected or error occurred"
        
        return web.Response(
            text=json.dumps(response),
            content_type='application/json'
        )

    async def record_training_video(self, save_path, duration=5):
        if self.debug:
            logger.debug(f"=== Starting Training Recording to {save_path} ===")
        
        try:
            if not await self.initialize_camera():
                return False

            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            
            fps = 20
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(save_path, fourcc, fps, (640, 480))
            
            frames_to_capture = fps * duration
            frame_count = 0
            
            while frame_count < frames_to_capture and self.is_recording:
                ret, frame = self.camera.read()
                if not ret:
                    break
                out.write(frame)
                frame_count += 1
                await asyncio.sleep(1/fps)
            
            out.release()
            await self.release_camera()
            self.is_recording = False
            return True
            
        except Exception as e:
            logger.error(f"Error during training recording: {e}")
            return False

    async def handle_train(self, request):
        if self.is_recording:
            return web.Response(
                text=json.dumps({"status": "error", "message": "Recording already in progress"}),
                content_type='application/json'
            )

        try:
            data = await request.json()
            save_path = data.get('video_path')
            if not save_path:
                return web.Response(
                    text=json.dumps({"status": "error", "message": "video_path is required"}),
                    content_type='application/json'
                )

            save_path = os.path.expanduser(save_path)
            
            # Najpierw nagrywamy wideo
            self.is_recording = True
            success = await self.record_training_video(save_path)
            if not success:
                return web.Response(
                    text=json.dumps({"status": "error", "message": "Failed to record video"}),
                    content_type='application/json'
                )

            # Sprawdzamy czy plik został utworzony
            if not os.path.exists(save_path):
                return web.Response(
                    text=json.dumps({"status": "error", "message": "Video file was not created"}),
                    content_type='application/json'
                )

            # Czekamy chwilę, aby upewnić się że plik został zapisany
            await asyncio.sleep(1)

            # Wysyłamy żądanie do facenet
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.facenet_url}/train",
                    json={'video_path': save_path}
                ) as response:
                    facenet_response = await response.json()
                    return web.Response(
                        text=json.dumps({
                            "status": "success",
                            "message": "Video recorded and sent for training",
                            "facenet_response": facenet_response
                        }),
                        content_type='application/json'
                    )
            
        except Exception as e:
            logger.error(f"Error in handle_train: {e}")
            return web.Response(
                text=json.dumps({"status": "error", "message": str(e)}),
                content_type='application/json'
            )

    def run(self):
        web.run_app(self.app, host=self.host, port=self.port)

if __name__ == "__main__":
    server = CameraServer()
    server.run()