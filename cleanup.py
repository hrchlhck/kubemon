from sys_monitor.constants import BASE_DIR
import shutil
import os

def cleanup():
    for root, sub, _ in os.walk(os.path.join(BASE_DIR, "sys_monitor")):
        if root.startswith("."):
            continue
        for __pycache__ in sub:
            if __pycache__ == '__pycache__':
                shutil.rmtree(os.path.join(root, __pycache__))

if __name__ == '__main__':
    cleanup()