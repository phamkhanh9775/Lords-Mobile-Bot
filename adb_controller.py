import subprocess
import cv2
import numpy as np
import time
import threading


ADB = r"C:\platform-tools\adb.exe"


class ADBDevice:
    def __init__(self, serial):
        self.serial = serial

    # ==========================================================
    # BASIC ADB
    # ==========================================================

    def _run(self, args, timeout=30, capture_output=True):
        cmd = [ADB, "-s", self.serial] + args

        result = subprocess.run(
            cmd,
            capture_output=capture_output,
            text=False,
            timeout=timeout
        )

        return result

    def shell(self, command, timeout=30):
        result = self._run(
            ["shell"] + command.split(),
            timeout=timeout
        )

        if result.returncode != 0:
            raise RuntimeError(
                f"[{self.serial}] ADB shell error: "
                f"{result.stderr.decode(errors='ignore')}"
            )

        return result.stdout.decode(errors="ignore").strip()

    # ==========================================================
    # SCREENSHOT
    # ==========================================================

    def screenshot(self):
        """
        Chụp màn hình điện thoại bằng:
        adb exec-out screencap -p
        """

        result = self._run(
            ["exec-out", "screencap", "-p"],
            timeout=15
        )

        if result.returncode != 0:
            raise RuntimeError(
                f"[{self.serial}] Screenshot failed."
            )

        image = np.frombuffer(result.stdout, dtype=np.uint8)

        frame = cv2.imdecode(
            image,
            cv2.IMREAD_COLOR
        )

        if frame is None:
            raise RuntimeError(
                f"[{self.serial}] Cannot decode screenshot."
            )

        return frame

    # ==========================================================
    # TOUCH
    # ==========================================================

    def tap(self, x, y):
        self.shell(
            f"input tap {int(x)} {int(y)}"
        )

    def swipe(self, x1, y1, x2, y2, duration=400):
        self.shell(
            f"input swipe "
            f"{int(x1)} {int(y1)} "
            f"{int(x2)} {int(y2)} "
            f"{int(duration)}"
        )

    def press_back(self):
        self.shell("input keyevent KEYCODE_BACK")

    def press_home(self):
        self.shell("input keyevent KEYCODE_HOME")

    # ==========================================================
    # APP
    # ==========================================================

    def launch_package(self, package_name):
        self.shell(
            f"monkey -p {package_name} "
            f"-c android.intent.category.LAUNCHER 1"
        )

    def is_online(self):
        try:
            result = self._run(
                ["get-state"],
                timeout=5
            )

            return (
                result.returncode == 0 and
                b"device" in result.stdout
            )

        except Exception:
            return False

    # ==========================================================
    # DEVICE INFO
    # ==========================================================

    def size(self):
        output = self.shell("wm size")

        # Example:
        # Physical size: 1080x1920

        if "x" not in output:
            return None

        try:
            value = output.split(":")[-1].strip()
            width, height = value.split("x")

            return int(width), int(height)

        except Exception:
            return None


# ==============================================================
# DEVICE MANAGER
# ==============================================================

class ADBManager:

    @staticmethod
    def list_devices():
        """
        Trả về danh sách serial của tất cả thiết bị đang online.
        """

        result = subprocess.run(
            [ADB, "devices"],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            return []

        devices = []

        for line in result.stdout.splitlines():

            if "\tdevice" in line:

                serial = line.split("\t")[0].strip()

                if serial:
                    devices.append(serial)

        return devices

    @staticmethod
    def get_devices():
        return [
            ADBDevice(serial)
            for serial in ADBManager.list_devices()
        ]