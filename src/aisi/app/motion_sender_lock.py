"""Process-lifetime lock for the live Motion OSC writer (standard library)."""
from pathlib import Path


class MotionSenderLock:
    def __init__(self, path=None):
        self.path = Path(path) if path else Path(__file__).resolve().parents[3] / 'data/aisi/state/motion_sender.lock'
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.file = self.path.open('a+b')
        self.file.seek(0, 2)
        if not self.file.tell():
            self.file.write(b'0')
            self.file.flush()
        self.file.seek(0)
        try:
            import os
            if os.name == 'nt':
                import msvcrt
                msvcrt.locking(self.file.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(self.file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as error:
            self.file.close()
            raise RuntimeError('Ein Live-Motion-Sender läuft bereits. Status prüfen.') from error

    def close(self):
        self.file.close()
