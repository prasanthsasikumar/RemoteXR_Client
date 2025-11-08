import os
import time
import cv2
import numpy as np

# Eyetrax imports
from eyetrax.calibration import (
    run_5_point_calibration,
    run_9_point_calibration,
    run_lissajous_calibration,
)
from eyetrax.cli import parse_common_args
from eyetrax.filters import KalmanSmoother, KDESmoother, NoSmoother, make_kalman
from eyetrax.gaze import GazeEstimator
from eyetrax.utils.draw import draw_cursor, make_thumbnail
from eyetrax.utils.screen import get_screen_size
from eyetrax.utils.video import camera, fullscreen, iter_frames

# LSL imports
try:
    from pylsl import StreamInfo, StreamOutlet, local_clock
except ImportError as e:
    raise SystemExit("pylsl not installed. Run: pip install pylsl") from e

# --- LSL Stream Configuration ---
STREAM_NAME = "EyeGaze"
STREAM_TYPE = "Gaze"
CHANNEL_COUNT = 3
# Use 0.0 for irregular rate; timestamps will be managed by local_clock()
SAMPLE_RATE = 0.0 
CHANNEL_FORMAT = 'float32'
SOURCE_ID = 'eyetrax_source_001'
# --- End LSL Configuration ---


def create_lsl_outlet() -> StreamOutlet:
    """
    Creates and returns a new LSL StreamOutlet based on the constants.
    """
    info = StreamInfo(
        STREAM_NAME,
        STREAM_TYPE,
        CHANNEL_COUNT,
        SAMPLE_RATE,
        CHANNEL_FORMAT,
        SOURCE_ID,
    )
    
    # Add channel labels as metadata
    chns = info.desc().append_child("channels")
    for label in ["gaze_x_normalized", "gaze_y_normalized", "pupil_dummy"]:
        ch = chns.append_child("channel")
        ch.append_child_value("label", label)

    # Add coordinate system metadata (good practice)
    gaze_desc = info.desc().append_child("gaze_coordinate_system")
    gaze_desc.append_child_value("convention", "TopLeft")
    gaze_desc.append_child_value("units", "Normalized")
    gaze_desc.append_child_value("range_x", "[0.0, 1.0]")
    gaze_desc.append_child_value("range_y", "[0.0, 1.0]")
    
    print(f"Creating LSL outlet '{STREAM_NAME}' (Type: {STREAM_TYPE})...")
    # chunk_size=1 means we push one sample at a time
    return StreamOutlet(info, chunk_size=1, max_buffered=360)


def run_demo_with_lsl():
    """
    Runs the Eyetrax demo and streams gaze data via LSL.
    """
    args = parse_common_args()

    filter_method = args.filter
    camera_index = args.camera
    calibration_method = args.calibration
    background_path = args.background
    confidence_level = args.confidence

    gaze_estimator = GazeEstimator(model_name=args.model)

    if args.model_file and os.path.isfile(args.model_file):
        gaze_estimator.load_model(args.model_file)
        print(f"[demo] Loaded gaze model from {args.model_file}")
    else:
        if calibration_method == "9p":
            run_9_point_calibration(gaze_estimator, camera_index=camera_index)
        elif calibration_method == "5p":
            run_5_point_calibration(gaze_estimator, camera_index=camera_index)
        else:
            run_lissajous_calibration(gaze_estimator, camera_index=camera_index)

    screen_width, screen_height = get_screen_size()
    if screen_width == 0 or screen_height == 0:
        raise ValueError("Could not get valid screen dimensions. Cannot normalize coordinates.")

    if filter_method == "kalman":
        kalman = make_kalman()
        smoother = KalmanSmoother(kalman)
        smoother.tune(gaze_estimator, camera_index=camera_index)
    elif filter_method == "kde":
        kalman = None
        smoother = KDESmoother(screen_width, screen_height, confidence=confidence_level)
    else:
        kalman = None
        smoother = NoSmoother()

    if background_path and os.path.isfile(background_path):
        background = cv2.imread(background_path)
        background = cv2.resize(background, (screen_width, screen_height))
    else:
        background = np.zeros((screen_height, screen_width, 3), dtype=np.uint8)
        background[:] = (50, 50, 50)

    cam_width, cam_height = 320, 240
    BORDER = 2
    MARGIN = 20
    cursor_alpha = 0.0
    cursor_step = 0.05

    # --- Create the LSL Outlet ---
    try:
        outlet = create_lsl_outlet()
        print("LSL Outlet created. Streaming data...")
    except Exception as e:
        print(f"Error creating LSL outlet: {e}")
        print("Continuing without LSL streaming.")
        outlet = None
    # --- End LSL Setup ---


    with camera(camera_index) as cap:
        prev_time = time.time()

        for frame in iter_frames(cap):
            features, blink_detected = gaze_estimator.extract_features(frame)
            
            lsl_sample = [np.nan, np.nan, np.nan] # Default to NaN

            if features is not None and not blink_detected:
                gaze_point = gaze_estimator.predict(np.array([features]))[0]
                x, y = map(int, gaze_point)
                x_pred, y_pred = smoother.step(x, y)
                contours = smoother.debug.get("contours", [])
                cursor_alpha = min(cursor_alpha + cursor_step, 1.0)

                # --- LSL Data Preparation ---
                # Normalize coordinates (0,0 is top-left)
                lsl_gaze_x = x_pred / screen_width
                lsl_gaze_y = y_pred / screen_height
                # We don't have pupil data, send a dummy value
                lsl_pupil = 0.0 
                
                # Clamp values to [0, 1] range just in case
                lsl_gaze_x = max(0.0, min(1.0, lsl_gaze_x))
                lsl_gaze_y = max(0.0, min(1.0, lsl_gaze_y))

                lsl_sample = [lsl_gaze_x, lsl_gaze_y, lsl_pupil]
                # --- End LSL Preparation ---

            else:
                x_pred = y_pred = None
                blink_detected = True
                contours = []
                cursor_alpha = max(cursor_alpha - cursor_step, 0.0)
                # lsl_sample is already [np.nan, np.nan, np.nan]

            # --- Push sample to LSL ---
            if outlet:
                try:
                    outlet.push_sample(lsl_sample, local_clock())
                    print(f"\rPushed LSL sample: {lsl_sample}", end="")
                except Exception as e:
                    print(f"Error pushing LSL sample: {e}")
            # --- End LSL Push ---


            # --- Drawing (same as original demo) ---
            canvas = background.copy()

            if filter_method == "kde" and contours:
                cv2.drawContours(canvas, contours, -1, (15, 182, 242), 5)

            if x_pred is not None and y_pred is not None and cursor_alpha > 0:
                draw_cursor(canvas, x_pred, y_pred, cursor_alpha)

            thumb = make_thumbnail(frame, size=(cam_width, cam_height), border=BORDER)
            h, w = thumb.shape[:2]
            canvas[-h - MARGIN : -MARGIN, -w - MARGIN : -MARGIN] = thumb

            now = time.time()
            fps = 1 / (now - prev_time)
            prev_time = now

            cv2.putText(
                canvas,
                f"FPS: {int(fps)}",
                (50, 50),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.2,
                (255, 255, 255),
                2,
                cv2.LINE_AA,
            )
            blink_txt = "Blinking" if blink_detected else "Not Blinking"
            blink_clr = (0, 0, 255) if blink_detected else (0, 255, 0)
            cv2.putText(
                canvas,
                blink_txt,
                (50, 100),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.2,
                blink_clr,
                2,
                cv2.LINE_AA,
            )

            cv2.imshow("Gaze Estimation", canvas)
            if cv2.waitKey(1) == 27:
                print("Escape key pressed. Stopping stream.")
                break
        
        print("Demo loop finished.")


if __name__ == "__main__":
    run_demo_with_lsl()