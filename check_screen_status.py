import time
import cv2
import pytesseract

from adb_controller import ADBDevice

from check_page import (
    identify_page,
    locate_image,
    center_of
)

from shield_module import shield


pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)


def army_limit_check(device: ADBDevice):

    identify_page(device)

    hasFreeArmy = True

    # for i in range(5):
    #     try:
    #         # Check if the screenshot of the screen status is present
    #         screenshot = pyautogui.locateOnScreen("utils/screen_status.png", confidence=0.8)
    #         if screenshot:
    #             x, y = pyautogui.center(screenshot)
    #             pyautogui.click(x, y)
    #             print("Screenshot found!")
    #             break
    #     except Exception as e:
    #         pyautogui.press("esc")
    #         time.sleep(0.5)

    # time.sleep(0.5)
    # try:
    #     check = pyautogui.locateOnScreen("utils/check_army_limit.png", confidence=0.8)
    #     if check:
    #         x, y = pyautogui.center(check)
    #         pyautogui.click(x, y)
    #         print("Check army limit found and clicked.")
    # except Exception as e:
    #     time.sleep(0.5)

    # try:
    #     checker = pyautogui.locateOnScreen("utils/checker.png", confidence=0.95)
    #     if checker:
    #         x, y = pyautogui.center(checker)
    #         pyautogui.moveTo(x, y)
    # except Exception as e:
    #     hasFreeArmy = True
    #     print("Checker not found. Waiting...")

    # time.sleep(0.5)
    # pyautogui.press("esc")

    try:

        frame = device.screenshot()

        checker = locate_image(
            frame,
            "utils/c1.png",
            confidence=0.95
        )

        if checker:

            print(
                f"[{device.serial}] "
                f"Checker found."
            )

            hasFreeArmy = False

    except Exception:

        print(
            f"[{device.serial}] "
            f"Checker1 not found."
        )

    return hasFreeArmy


def recall_troops(device: ADBDevice):

    time.sleep(0.5)

    try:

        frame = device.screenshot()

        tile = locate_image(
            frame,
            "utils/army1.png",
            confidence=0.8
        )

        if tile:

            x, y = center_of(tile)

            device.tap(x, y)

            print(
                f"[{device.serial}] "
                f"Tile found and clicked."
            )

    except Exception:

        print(
            f"[{device.serial}] "
            f"Tile not found."
        )

    time.sleep(1)

    for _ in range(10):

        try:

            frame = device.screenshot()

            tile = locate_image(
                frame,
                "utils/return_to_castle.png",
                confidence=0.7
            )

            if tile:

                x, y = center_of(tile)

                device.tap(x, y)

                time.sleep(0.4)

                print(
                    f"[{device.serial}] "
                    f"return found and clicked."
                )

                break

            width, height = (
                device.size()
                or
                (1080, 1920)
            )

            device.swipe(
                int(width * 0.70),
                int(height * 0.70),
                int(width * 0.70),
                int(height * 0.35),
                400
            )

            time.sleep(0.5)

        except Exception:

            print(
                f"[{device.serial}] "
                f"return not found."
            )


def fix_alert(device: ADBDevice):

    # Step 1: Take a screenshot

    try:

        frame = device.screenshot()

        army_button = locate_image(
            frame,
            "utils/arm_b.png",
            confidence=0.8
        )

        if army_button:

            x, y = center_of(
                army_button
            )

            device.tap(x, y)

            time.sleep(1.5)

            frame = device.screenshot()

            recall_button = locate_image(
                frame,
                "utils/recall_button.png",
                confidence=0.8
            )

            if recall_button:

                x, y = center_of(
                    recall_button
                )

                device.tap(x, y)

                time.sleep(1)

                frame = device.screenshot()

                use_button = locate_image(
                    frame,
                    "utils/u1.png",
                    confidence=0.8
                )

                if use_button:

                    x, y = center_of(
                        use_button
                    )

                    device.tap(x, y)

                    time.sleep(0.5)

                    return

    except Exception as e:

        print(
            f"[{device.serial}] "
            f"Normal alert routine error: {e}"
        )

    # ======================================================
    # OCR FALLBACK
    # ======================================================

    try:

        screenshot = device.screenshot()

        gray = cv2.cvtColor(
            screenshot,
            cv2.COLOR_BGR2GRAY
        )

        boxes = pytesseract.image_to_data(
            gray,
            output_type=pytesseract.Output.DICT
        )

        for i in range(
            len(boxes["text"])
        ):

            text = (
                boxes["text"][i]
                .strip()
                .lower()
            )

            if "camp" in text:

                device.press_back()

                recall_troops(
                    device
                )

                return

        device.press_back()

        time.sleep(0.5)

        shield(device)

    except Exception as e:

        print(
            f"[{device.serial}] "
            f"OCR fallback error: {e}"
        )


def being_attacked(device: ADBDevice):

    try:

        frame = device.screenshot()

        attacked = locate_image(
            frame,
            "utils/being_attacked.png",
            confidence=0.6
        )

        if attacked:

            x, y = center_of(
                attacked
            )

            device.tap(x, y)

            print(
                f"[{device.serial}] "
                f"Being attacked!"
            )

            return True

    except Exception:

        print(
            f"[{device.serial}] "
            f"checking screen status continues..."
        )

    return False