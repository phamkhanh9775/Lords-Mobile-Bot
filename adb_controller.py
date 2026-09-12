import subprocess
import cv2
import numpy as np
import threading
import re


ADB = r"D:\Lords Mobile Bot\platform-tools\adb.exe"


class ADBDevice:
    def __init__(self, serial):
        self.serial = serial

        # Mỗi thiết bị có một lock riêng.
        # Đảm bảo không có nhiều thread cùng thao tác
        # trên cùng một điện thoại tại cùng thời điểm.
        self.lock = threading.RLock()

    # ==========================================================
    # BASIC ADB
    # ==========================================================

    def _run(self, args, timeout=30):
        cmd = [
            ADB,
            "-s",
            self.serial
        ] + args

        try:
            return subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=timeout
            )

        except subprocess.TimeoutExpired:
            raise RuntimeError(
                f"[{self.serial}] "
                f"ADB command timeout: {' '.join(args)}"
            )

        except FileNotFoundError:
            raise RuntimeError(
                f"ADB not found: {ADB}"
            )

    # ==========================================================
    # SHELL
    # ==========================================================

    def shell(self, command, timeout=30):
        result = self._run(
            ["shell"] + command.split(),
            timeout=timeout
        )

        if result.returncode != 0:

            error = result.stderr.decode(
                errors="ignore"
            ).strip()

            raise RuntimeError(
                f"[{self.serial}] "
                f"ADB shell error: {error}"
            )

        return result.stdout.decode(
            errors="ignore"
        ).strip()

    # ==========================================================
    # SCREENSHOT
    # ==========================================================

    def screenshot(self):

        with self.lock:

            if not self.is_online():
                raise RuntimeError(
                    f"[{self.serial}] "
                    f"Device is offline."
                )

            result = self._run(
                [
                    "exec-out",
                    "screencap",
                    "-p"
                ],
                timeout=15
            )

            if result.returncode != 0:

                error = result.stderr.decode(
                    errors="ignore"
                ).strip()

                raise RuntimeError(
                    f"[{self.serial}] "
                    f"Screenshot failed: {error}"
                )

            if not result.stdout:
                raise RuntimeError(
                    f"[{self.serial}] "
                    f"Screenshot returned empty data."
                )

            image = np.frombuffer(
                result.stdout,
                dtype=np.uint8
            )

            frame = cv2.imdecode(
                image,
                cv2.IMREAD_COLOR
            )

            if frame is None:
                raise RuntimeError(
                    f"[{self.serial}] "
                    f"Cannot decode screenshot."
                )

            return frame

    # ==========================================================
    # TOUCH
    # ==========================================================

    def tap(self, x, y):

        with self.lock:
            self.shell(
                f"input tap "
                f"{int(x)} {int(y)}"
            )

    def swipe(
        self,
        x1,
        y1,
        x2,
        y2,
        duration=400
    ):

        with self.lock:
            self.shell(
                f"input swipe "
                f"{int(x1)} {int(y1)} "
                f"{int(x2)} {int(y2)} "
                f"{int(duration)}"
            )

    def press_back(self):

        with self.lock:
            self.shell(
                "input keyevent KEYCODE_BACK"
            )

    def press_home(self):

        with self.lock:
            self.shell(
                "input keyevent KEYCODE_HOME"
            )

    # ==========================================================
    # APP
    # ==========================================================

    def launch_package(self, package_name):

        with self.lock:
            self.shell(
                f"monkey -p {package_name} "
                f"-c android.intent.category.LAUNCHER 1"
            )

    # ==========================================================
    # ONLINE CHECK
    # ==========================================================

    def is_online(self):

        try:

            result = self._run(
                ["get-state"],
                timeout=5
            )

            return (
                result.returncode == 0
                and result.stdout.strip() == b"device"
            )

        except Exception:
            return False

    # ==========================================================
    # DEVICE INFO
    # ==========================================================

    def size(self):

        try:

            output = self.shell(
                "wm size"
            )

            # Ưu tiên Physical size
            match = re.search(
                r"Physical size:\s*(\d+)x(\d+)",
                output
            )

            if match:

                return (
                    int(match.group(1)),
                    int(match.group(2))
                )

            # Nếu không có Physical size,
            # tìm kích thước xấu nhất còn lại.
            match = re.search(
                r"(\d+)x(\d+)",
                output
            )

            if match:

                return (
                    int(match.group(1)),
                    int(match.group(2))
                )

        except Exception as e:

            print(
                f"[{self.serial}] "
                f"Cannot get screen size: {e}"
            )

        return None


# ==============================================================
# DEVICE MANAGER
# ==============================================================

class ADBManager:

    @staticmethod
    def list_devices():

        try:

            result = subprocess.run(
                [
                    ADB,
                    "devices"
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10
            )

        except FileNotFoundError:

            print(
                f"ADB not found: {ADB}"
            )

            return []

        except subprocess.TimeoutExpired:

            print(
                "ADB devices command timeout."
            )

            return []

        if result.returncode != 0:

            print(
                "ADB devices error:",
                result.stderr
            )

            return []

        devices = []

        for line in result.stdout.splitlines():

            line = line.strip()

            if not line:
                continue

            if line.startswith(
                "List of devices attached"
            ):
                continue

            parts = line.split()

            if len(parts) >= 2:

                serial = parts[0]
                status = parts[1]

                # Chỉ lấy device đang online
                if status == "device":

                    devices.append(
                        serial
                    )

        return devices

    @staticmethod
    def get_devices():

        return [
            ADBDevice(serial)
            for serial
            in ADBManager.list_devices()
        ]