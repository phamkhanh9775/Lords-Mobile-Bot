import cv2
import numpy as np
import time
import os
import threading

from ultralytics import YOLO

from adb_controller import ADBDevice
from check_page import (
    identify_page,
    locate_image,
    center_of
)

from state import (
    has_seen,
    add_seen
)


# ==========================================================
# YOLOv8
# ==========================================================

MODEL_PATH = "runs/detect/train/weights/best.pt"

model = YOLO(MODEL_PATH)

# YOLO model inference lock.
# Một model dùng chung cho nhiều thread.
model_lock = threading.Lock()


# ==========================================================
# SETTINGS
# ==========================================================

YOLO_CONFIDENCE = 0.70

# Chỉ nhận 4 loại tài nguyên mà model đã train.
RESOURCE_CLASSES = {
    "ore",
    "gold",
    "wood",
    "stone"
}


# ==========================================================
# SCREENSHOT
# ==========================================================

def capture_screen(device: ADBDevice):
    return device.screenshot()


# ==========================================================
# OCR COORDINATES
# ==========================================================

def read_coordinates_text(device: ADBDevice):
    import pytesseract

    frame = device.screenshot()

    height, width = frame.shape[:2]

    # Tương đương vùng tọa độ của code PC cũ,
    # nhưng dùng tỷ lệ để phù hợp nhiều độ phân giải.

    x = int(width * 0.68)
    y = int(height * 0.88)

    w = int(width * 0.30)
    h = int(height * 0.08)

    # Không để ROI vượt quá màn hình.
    x2 = min(x + w, width)
    y2 = min(y + h, height)

    roi = frame[y:y2, x:x2]

    if roi.size == 0:
        return ""

    gray = cv2.cvtColor(
        roi,
        cv2.COLOR_BGR2GRAY
    )

    gray = cv2.resize(
        gray,
        None,
        fx=2,
        fy=2,
        interpolation=cv2.INTER_CUBIC
    )

    _, thresh = cv2.threshold(
        gray,
        150,
        255,
        cv2.THRESH_BINARY
    )

    text = pytesseract.image_to_string(
        thresh,
        config="--psm 7"
    )

    cleaned = (
        text
        .strip()
        .replace("\n", " ")
    )

    return cleaned


# ==========================================================
# YOLO RESOURCE DETECTION
# ==========================================================

def detect_resources(
    device: ADBDevice,
    frame
):
    """
    Tìm tất cả resource mà YOLOv8 đã được train để nhận diện:

        ore
        gold
        wood
        stone

    Nếu có nhiều tile cùng lúc:
    - bỏ qua class ngoài RESOURCE_CLASSES
    - bỏ qua detection dưới YOLO_CONFIDENCE
    - chọn detection có confidence cao nhất
    """

    with model_lock:
        results = model(
            frame,
            verbose=False
        )

    best_detection = None
    highest_conf = 0.0

    for result in results:

        for box in result.boxes:

            cls_id = int(box.cls)

            # An toàn khi class id không hợp lệ.
            if cls_id not in result.names:
                continue

            cls_name = result.names[cls_id]

            # Chỉ nhận 4 resource.
            if cls_name not in RESOURCE_CLASSES:
                continue

            conf = float(
                box.conf.item()
            )

            if conf < YOLO_CONFIDENCE:
                continue

            x1, y1, x2, y2 = map(
                int,
                box.xyxy[0]
            )

            # Chọn tile có confidence cao nhất.
            if conf > highest_conf:

                highest_conf = conf

                best_detection = {
                    "class": cls_name,
                    "confidence": conf,
                    "box": (
                        x1,
                        y1,
                        x2,
                        y2
                    )
                }

    # ======================================================
    # KHÔNG CÓ RESOURCE
    # ======================================================

    if best_detection is None:

        print(
            f"[{device.serial}] "
            f"No ore/gold/wood/stone detected."
        )

        return False

    # ======================================================
    # RESOURCE ĐƯỢC TÌM THẤY
    # ======================================================

    cls_name = best_detection["class"]
    confidence = best_detection["confidence"]

    x1, y1, x2, y2 = (
        best_detection["box"]
    )

    center_x = (
        x1 + x2
    ) // 2

    center_y = (
        y1 + y2
    ) // 2

    # Đã dùng screenshot full-screen,
    # không cần cộng 130 như code PC cũ.

    print(
        f"[{device.serial}] "
        f"Found {cls_name} "
        f"at ({center_x}, {center_y}) "
        f"confidence={confidence:.3f}"
    )

    # ======================================================
    # CLICK TILE
    # ======================================================

    device.tap(
        center_x,
        center_y
    )

    time.sleep(1.5)

    # ======================================================
    # ĐỌC TỌA ĐỘ TILE
    # ======================================================

    coord_text = read_coordinates_text(
        device
    )

    if not coord_text:

        print(
            f"[{device.serial}] "
            f"Could not read tile coordinate."
        )

        device.press_back()

        return False

    # ======================================================
    # KIỂM TRA TILE ĐÃ TỪNG GỬI LÍNH
    # ======================================================

    if has_seen(
        device.serial,
        coord_text
    ):

        print(
            f"[{device.serial}] "
            f"Already sent troops to "
            f"{coord_text}. Skipping..."
        )

        device.press_back()

        return False

    # ======================================================
    # LƯU TILE
    # ======================================================

    add_seen(
        device.serial,
        coord_text
    )

    print(
        f"[{device.serial}] "
        f"New {cls_name} tile detected at "
        f"{coord_text}."
    )

    return True


# ==========================================================
# DEPLOY
# ==========================================================

def deploy(device: ADBDevice):

    time.sleep(0.5)

    buttons = [
        "gather.png",
        "g1.png",
        "g2.png",
        "deploy.png"
    ]

    for button in buttons:

        try:

            frame = device.screenshot()

            button_path = os.path.join(
                "utils",
                button
            )

            btn = locate_image(
                frame,
                button_path,
                confidence=0.8
            )

            if btn:

                x, y = center_of(btn)

                device.tap(
                    x,
                    y
                )

                print(
                    f"[{device.serial}] "
                    f"{button} clicked."
                )

                time.sleep(0.5)

        except Exception as e:

            print(
                f"[{device.serial}] "
                f"{button} error: {e}"
            )

            width, height = (
                device.size()
                or (1080, 1920)
            )

            device.swipe(
                int(width * 0.60),
                int(height * 0.75),
                int(width * 0.60),
                int(height * 0.35),
                300
            )

            break

            # print(f"{button} not found.")


# ==========================================================
# KINGDOM MAP
# ==========================================================

def go_to_kingdom_map(device: ADBDevice):

    current_page = identify_page(
        device
    )

    if current_page == "kingdom_map":

        pass

    else:

        try:

            frame = device.screenshot()

            map_icon = locate_image(
                frame,
                "utils/map.png",
                confidence=0.8
            )

            if map_icon:

                x, y = center_of(
                    map_icon
                )

                device.tap(
                    x,
                    y
                )

                print(
                    f"[{device.serial}] "
                    f"Map icon found and clicked."
                )

        except Exception as e:

            print(
                f"[{device.serial}] "
                f"Map icon error: {e}"
            )


# ==========================================================
# SCAN MAP
# ==========================================================

def scan_map(
    device: ADBDevice,
    pause_event=None
):

    # ======================================================
    # ĐÓNG POPUP NẾU CÓ
    # ======================================================

    for _ in range(3):

        try:

            frame = device.screenshot()

            c111 = locate_image(
                frame,
                "utils/exit_1.png",
                confidence=0.8
            )

            if c111:

                x, y = center_of(c111)

                device.tap(
                    x,
                    y
                )

                break

        except Exception:

            time.sleep(0.5)

    # ======================================================
    # ĐI TỚI KINGDOM MAP
    # ======================================================

    go_to_kingdom_map(
        device
    )

    # ======================================================
    # QUÉT VỊ TRÍ HIỆN TẠI
    # ======================================================

    frame = capture_screen(
        device
    )

    if detect_resources(
        device,
        frame
    ):

        deploy(
            device
        )

        return

    # ======================================================
    # MAP SCAN
    # ======================================================

    count = 0
    c1 = 0
    max_attempts = 20

    # Không dùng found_resources global nữa.
    # Mỗi device/thread tự chạy độc lập.

    while count < max_attempts:

        # ==================================================
        # PAUSE KHI BỊ TẤN CÔNG
        # ==================================================

        if (
            pause_event
            and pause_event.is_set()
        ):

            print(
                f"[{device.serial}] "
                f"Scan paused due to attack detected."
            )

            return

        print(
            f"[{device.serial}] "
            f"--- Scan iteration "
            f"{count + 1} ---"
        )

        # ==================================================
        # DOWN
        # ==================================================

        for _ in range(1 + c1):

            if (
                pause_event
                and pause_event.is_set()
            ):
                return

            width, height = (
                device.size()
                or (1080, 1920)
            )

            device.swipe(
                int(width * 0.60),
                int(height * 0.40),
                int(width * 0.60),
                int(height * 0.70),
                300
            )

            time.sleep(0.8)

            frame = capture_screen(
                device
            )

            if detect_resources(
                device,
                frame
            ):

                deploy(
                    device
                )

                return

        # ==================================================
        # RIGHT
        # ==================================================

        for _ in range(1 + c1):

            if (
                pause_event
                and pause_event.is_set()
            ):
                return

            width, height = (
                device.size()
                or (1080, 1920)
            )

            device.swipe(
                int(width * 0.30),
                int(height * 0.50),
                int(width * 0.70),
                int(height * 0.50),
                300
            )

            time.sleep(0.8)

            frame = capture_screen(
                device
            )

            if detect_resources(
                device,
                frame
            ):

                deploy(
                    device
                )

                return

        c1 += 1

        # ==================================================
        # UP
        # ==================================================

        for _ in range(1 + c1):

            if (
                pause_event
                and pause_event.is_set()
            ):
                return

            width, height = (
                device.size()
                or (1080, 1920)
            )

            device.swipe(
                int(width * 0.60),
                int(height * 0.70),
                int(width * 0.60),
                int(height * 0.35),
                300
            )

            time.sleep(0.8)

            frame = capture_screen(
                device
            )

            if detect_resources(
                device,
                frame
            ):

                deploy(
                    device
                )

                return

        # ==================================================
        # LEFT
        # ==================================================

        for _ in range(1 + c1):

            if (
                pause_event
                and pause_event.is_set()
            ):
                return

            width, height = (
                device.size()
                or (1080, 1920)
            )

            device.swipe(
                int(width * 0.70),
                int(height * 0.50),
                int(width * 0.30),
                int(height * 0.50),
                300
            )

            time.sleep(0.8)

            frame = capture_screen(
                device
            )

            if detect_resources(
                device,
                frame
            ):

                deploy(
                    device
                )

                return

        c1 += 1
        count += 1

    print(
        f"[{device.serial}] "
        f"Scan complete."
    )
