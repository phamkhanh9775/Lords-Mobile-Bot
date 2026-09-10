from run import MultiDeviceBot
import time


if __name__ == "__main__":

    manager = MultiDeviceBot()

    manager.start_all()

    while True:

        manager.refresh_devices()

        time.sleep(5)