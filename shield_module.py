import time
from check_page import locate_image, center_of
from adb_controller import ADBDevice


def shield(device: ADBDevice):

    print(
        f"[{device.serial}] Activating shield..."
    )

    # List of turfBoost options
    turf_boosts = [
        "utils/turfBoost0.png",
        "utils/turfBoost1.png",
        "utils/turfBoost2.png",
        "utils/turfBoost3.png",
    ]

    frame = device.screenshot()

    boost_found = False

    for boost_img in turf_boosts:

        try:

            found = locate_image(
                frame,
                boost_img,
                confidence=0.8
            )

            if found:

                x, y = center_of(found)

                device.tap(x, y)

                print(
                    f"[{device.serial}] "
                    f"{boost_img} found and clicked."
                )

                boost_found = True
                break

        except Exception as e:

            print(
                f"[{device.serial}] "
                f"Error locating {boost_img}: {e}"
            )

    if not boost_found:

        print(
            f"[{device.serial}] "
            f"No turf boost image found."
        )

        return

    time.sleep(0.5)

    # Try to open shield menu

    shield_menu_found = False

    for _ in range(5):

        try:

            frame = device.screenshot()

            found = locate_image(
                frame,
                "utils/shield1.png",
                confidence=0.8
            )

            if found:

                x, y = center_of(found)

                device.tap(x, y)

                print(
                    f"[{device.serial}] "
                    f"Shield menu found."
                )

                shield_menu_found = True
                break

        except Exception as e:

            print(
                f"[{device.serial}] "
                f"Error finding shield menu: {e}"
            )

            width, height = device.size() or (
                1080,
                1920
            )

            device.swipe(
                width // 2,
                int(height * 0.80),
                width // 2,
                int(height * 0.50),
                400
            )

            time.sleep(0.5)

    if not shield_menu_found:

        print(
            f"[{device.serial}] "
            f"Failed to open shield menu."
        )

        return

    time.sleep(0.5)

    # Use 8hr shield

    try:

        frame = device.screenshot()

        is_8 = locate_image(
            frame,
            "utils/eight.png",
            confidence=0.8
        )

        is_use = locate_image(
            frame,
            "utils/use.png",
            confidence=0.8
        )

        if is_8 and is_use:

            x_use, y_use = center_of(is_use)

            device.tap(
                x_use,
                y_use
            )

            print(
                f"[{device.serial}] "
                f"8-hour shield selected."
            )

        else:

            print(
                f"[{device.serial}] "
                f"8-hour shield or use button "
                f"not found."
            )

    except Exception as e:

        print(
            f"[{device.serial}] "
            f"Error clicking shield: {e}"
        )

    time.sleep(0.5)

    # Confirm with OK

    try:

        frame = device.screenshot()

        ok_found = locate_image(
            frame,
            "utils/ok.png",
            confidence=0.8
        )

        if ok_found:

            x, y = center_of(ok_found)

            device.tap(x, y)

            print(
                f"[{device.serial}] "
                f"OK clicked. Shield active."
            )

        else:

            print(
                f"[{device.serial}] "
                f"OK button not found."
            )

    except Exception as e:

        print(
            f"[{device.serial}] "
            f"Error confirming shield: {e}"
        )

    time.sleep(1)

    device.press_back()