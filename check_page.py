import cv2
import time
from adb_controller import ADBDevice


PAGE_IMAGES = {
    "home": "utils/map.png",
    "kingdom_map": "utils/return_castle.png",
    "kvk_map": "utils/kvk_map.png",
}

EXIT_CONFIRM_IMAGE = "utils/cancel_button.png"


def locate_image(frame, image_path, confidence=0.8):
    """
    OpenCV version of locateOnScreen().
    """

    template = cv2.imread(
        image_path,
        cv2.IMREAD_COLOR
    )

    if template is None:
        print(f"Cannot load image: {image_path}")
        return None

    if frame is None:
        return None

    try:
        result = cv2.matchTemplate(
            frame,
            template,
            cv2.TM_CCOEFF_NORMED
        )

        _, max_val, _, max_loc = cv2.minMaxLoc(result)

        if max_val >= confidence:

            h, w = template.shape[:2]

            x = max_loc[0]
            y = max_loc[1]

            return {
                "x": x,
                "y": y,
                "width": w,
                "height": h,
                "confidence": max_val
            }

    except Exception as e:
        print(
            f"OpenCV locate error "
            f"{image_path}: {e}"
        )

    return None


def center_of(result):
    return (
        result["x"] + result["width"] // 2,
        result["y"] + result["height"] // 2
    )


def get_current_page(device: ADBDevice):

    frame = device.screenshot()

    for page_name, image_path in PAGE_IMAGES.items():

        print(
            f"[{device.serial}] "
            f"Checking for {page_name} page..."
        )

        location = locate_image(
            frame,
            image_path,
            confidence=0.8
        )

        if location:

            print(
                f"[{device.serial}] "
                f"> You are on {page_name} page."
            )

            return page_name

    return None


def escape_to_valid_page(
    device: ADBDevice,
    max_attempts=10
):
    """
    Press BACK tối đa max_attempts lần.
    Không lặp vô hạn.
    """

    print(
        f"[{device.serial}] "
        f"Page not identified. Escaping..."
    )

    for attempt in range(max_attempts):

        try:
            if not device.is_online():
                print(
                    f"[{device.serial}] "
                    f"Device offline."
                )
                return None

            print(
                f"[{device.serial}] "
                f"Pressing BACK "
                f"({attempt + 1}/{max_attempts})..."
            )

            device.press_back()

            time.sleep(1)

            page = get_current_page(device)

            if page:
                print(
                    f"[{device.serial}] "
                    f"Successfully returned to "
                    f"{page} page."
                )

                return page

        except Exception as e:
            print(
                f"[{device.serial}] "
                f"Escape error: {e}"
            )

            time.sleep(1)

    print(
        f"[{device.serial}] "
        f"Could not identify a valid page "
        f"after {max_attempts} attempts."
    )

    return None

def identify_page(device: ADBDevice):

    page = get_current_page(device)

    if page:
        return page

    return escape_to_valid_page(device)