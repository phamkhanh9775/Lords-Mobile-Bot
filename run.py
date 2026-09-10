import time
import threading

from adb_controller import (
    ADBManager,
    ADBDevice
)

from check_screen_status import (
    being_attacked,
    fix_alert,
    army_limit_check
)

from detectTiles import (
    scan_map
)


# ==========================================================
# SETTINGS
# ==========================================================

LORDS_PACKAGE = "com.igg.android.lordsmobile"

# Ví dụ nếu biết package:
#
# LORDS_PACKAGE = "your.package.name"


# ==========================================================
# STATE PER DEVICE
# ==========================================================

class DeviceBot:

    def __init__(self, device: ADBDevice):

        self.device = device

        self.pause_scan_event = (
            threading.Event()
        )

        self.scan_map_thread = None

        self.is_fix_alert_running = False

        self.lock = threading.Lock()

    # ======================================================
    # START GAME
    # ======================================================

    def start_game(self):

        print(
            f"[{self.device.serial}] "
            f"ADB device connected."
        )

        size = self.device.size()

        print(
            f"[{self.device.serial}] "
            f"Screen size: {size}"
        )

        if LORDS_PACKAGE:

            try:

                self.device.launch_package(
                    LORDS_PACKAGE
                )

                print(
                    f"[{self.device.serial}] "
                    f"Lords Mobile launched."
                )

                time.sleep(8)

            except Exception as e:

                print(
                    f"[{self.device.serial}] "
                    f"Cannot launch game: {e}"
                )

    # ======================================================
    # SCAN
    # ======================================================

    def scan_map_wrapper(self):

        try:

            print(
                f"[{self.device.serial}] "
                f"Starting map scan..."
            )

            scan_map(
                self.device,
                pause_event=(
                    self.pause_scan_event
                )
            )

            for _ in range(5):

                try:

                    frame = (
                        self.device.screenshot()
                    )

                    from check_page import (
                        locate_image,
                        center_of
                    )

                    cr = locate_image(
                        frame,
                        "utils/gather_esc.png",
                        confidence=0.8
                    )

                    if cr:

                        x, y = center_of(cr)

                        self.device.tap(x, y)

                        time.sleep(0.5)

                        break

                except Exception:

                    print(
                        f"[{self.device.serial}] "
                        f"cross did not clicked"
                    )

                    time.sleep(1)

        finally:

            self.scan_map_thread = None

    # ======================================================
    # FIX ALERT
    # ======================================================

    def fix_alert_wrapper(self):

        with self.lock:

            if self.is_fix_alert_running:

                return

            self.is_fix_alert_running = True

        try:

            print(
                f"[{self.device.serial}] "
                f"[⚠️] Executing fix_alert routine."
            )

            self.pause_scan_event.set()

            fix_alert(
                self.device
            )

        except Exception as e:

            print(
                f"[{self.device.serial}] "
                f"fix_alert error: {e}"
            )

        finally:

            self.pause_scan_event.clear()

            with self.lock:

                self.is_fix_alert_running = False

    # ======================================================
    # START SCAN
    # ======================================================

    def start_scan(self):

        if self.is_fix_alert_running:

            return

        if self.pause_scan_event.is_set():

            return

        if (
            self.scan_map_thread
            and
            self.scan_map_thread.is_alive()
        ):

            return

        if not army_limit_check(
            self.device
        ):

            print(
                f"[{self.device.serial}] "
                f"No free army."
            )

            return

        self.scan_map_thread = (
            threading.Thread(
                target=self.scan_map_wrapper,
                daemon=True
            )
        )

        self.scan_map_thread.start()

    # ======================================================
    # MONITOR
    # ======================================================

    def monitor(self):

        print(
            f"[{self.device.serial}] "
            f"Monitor started."
        )

        while True:

            try:

                if not self.device.is_online():

                    print(
                        f"[{self.device.serial}] "
                        f"Device offline."
                    )

                    break

                # PRIORITY: Being Attacked

                if (
                    not self.is_fix_alert_running
                    and
                    being_attacked(
                        self.device
                    )
                ):

                    threading.Thread(
                        target=self.fix_alert_wrapper,
                        daemon=True
                    ).start()

                # Only scan if not being attacked

                if (
                    not self.is_fix_alert_running
                    and
                    not self.pause_scan_event.is_set()
                ):

                    self.start_scan()

            except Exception as e:

                print(
                    f"[{self.device.serial}] "
                    f"Monitor error: {e}"
                )

            time.sleep(2)


# ==========================================================
# MULTI DEVICE
# ==========================================================

class MultiDeviceBot:

    def __init__(self):

        self.bots = {}

    def refresh_devices(self):

        serials = (
            ADBManager.list_devices()
        )

        for serial in serials:

            if serial not in self.bots:

                device = ADBDevice(
                    serial
                )

                self.bots[serial] = (
                    DeviceBot(device)
                )

        # Remove offline devices

        offline = []

        for serial, bot in self.bots.items():

            if serial not in serials:

                offline.append(serial)

        for serial in offline:

            del self.bots[serial]

        return serials

    def start_all(self):

        self.refresh_devices()

        if not self.bots:

            print(
                "No ADB devices found."
            )

            return

        for serial, bot in self.bots.items():

            threading.Thread(
                target=bot.start_game,
                daemon=True
            ).start()

            threading.Thread(
                target=bot.monitor,
                daemon=True
            ).start()

        print(
            f"Started {len(self.bots)} devices."
        )


# ==========================================================
# MAIN
# ==========================================================

if __name__ == "__main__":

    manager = MultiDeviceBot()

    manager.start_all()

    while True:

        time.sleep(10)
