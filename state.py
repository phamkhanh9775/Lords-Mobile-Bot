from collections import defaultdict
import threading


# Mỗi device có danh sách tọa độ riêng
seen_coords = defaultdict(set)

state_lock = threading.Lock()


def has_seen(device_id, coord):
    with state_lock:
        return coord in seen_coords[device_id]


def add_seen(device_id, coord):
    with state_lock:
        seen_coords[device_id].add(coord)


def clear_seen(device_id):
    with state_lock:
        seen_coords[device_id].clear()


def clear_all():
    with state_lock:
        seen_coords.clear()