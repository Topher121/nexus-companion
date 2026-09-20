"""Capture the HotS window through Windows.Graphics.Capture, even when covered."""
import bootstrap
import ctypes
from ctypes import wintypes
import threading
import time
from PIL import Image

GAME_EXES = {'heroesofthestorm_x64.exe', 'heroesofthestorm.exe'}


class Windows:
    def __init__(self):
        self.user = ctypes.windll.user32
        self.kernel = ctypes.windll.kernel32
        self.user.IsIconic.argtypes = [wintypes.HWND]
        self.user.IsWindow.argtypes = [wintypes.HWND]
        self.user.IsWindowVisible.argtypes = [wintypes.HWND]
        self.user.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
        self.user.GetClientRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
        self.user.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
        self.user.ClientToScreen.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.POINT)]
        self.kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        self.kernel.OpenProcess.restype = wintypes.HANDLE
        self.kernel.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
        self.kernel.CloseHandle.argtypes = [wintypes.HANDLE]

    def executable(self, hwnd):
        pid = wintypes.DWORD()
        self.user.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        process = self.kernel.OpenProcess(0x1000, False, pid.value)
        if not process:
            return ''
        try:
            length = wintypes.DWORD(32768)
            path = ctypes.create_unicode_buffer(length.value)
            if not self.kernel.QueryFullProcessImageNameW(process, 0, path, ctypes.byref(length)):
                return ''
            return path.value.replace('\\', '/').split('/')[-1].lower()
        finally:
            self.kernel.CloseHandle(process)

    def find_game(self):
        matches = []
        callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        @callback_type
        def visit(hwnd, _):
            if self.user.IsWindowVisible(hwnd) and self.executable(hwnd) in GAME_EXES:
                matches.append(hwnd)
            return True
        self.user.EnumWindows.argtypes = [callback_type, wintypes.LPARAM]
        self.user.EnumWindows(visit, 0)
        # Never select another window by a partial title or fall back to the desktop.
        return matches[0] if len(matches) == 1 else None

    def minimized(self, hwnd):
        return not self.user.IsWindow(hwnd) or bool(self.user.IsIconic(hwnd))

    def client_image(self, image, hwnd):
        rect = wintypes.RECT()
        point = wintypes.POINT(0, 0)
        if not self.user.GetClientRect(hwnd, ctypes.byref(rect)) or not self.user.ClientToScreen(hwnd, ctypes.byref(point)):
            raise RuntimeError('The game window changed during capture.')
        if image.size == (rect.right, rect.bottom):
            return image
        bounds = wintypes.RECT()
        dwm = ctypes.windll.dwmapi
        dwm.DwmGetWindowAttribute.argtypes = [wintypes.HWND, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD]
        if dwm.DwmGetWindowAttribute(hwnd, 9, ctypes.byref(bounds), ctypes.sizeof(bounds)) != 0:
            self.user.GetWindowRect(hwnd, ctypes.byref(bounds))
        if image.size != (bounds.right - bounds.left, bounds.bottom - bounds.top):
            self.user.GetWindowRect(hwnd, ctypes.byref(bounds))
        if image.size != (bounds.right - bounds.left, bounds.bottom - bounds.top):
            raise RuntimeError('Window size is changing; waiting for the next frame.')
        left, top = point.x - bounds.left, point.y - bounds.top
        if left < 0 or top < 0 or left + rect.right > image.width or top + rect.bottom > image.height:
            raise RuntimeError('Waiting for a complete game window frame.')
        return image.crop((left, top, left + rect.right, top + rect.bottom))


class GameCapture:
    def __init__(self, windows=None):
        self.windows = windows or Windows()
        self.lock = threading.Lock()
        self.ready = threading.Event()
        self.control = None
        self.session = None
        self.hwnd = None
        self.latest = None
        self.received = 0
        self.epoch = 0

    def close(self):
        with self.lock:
            self.epoch += 1
            control, self.control = self.control, None
            self.session = None
            self.latest = None
            self.hwnd = None
            self.ready.set()
        # Capture stop may join its worker, so it must happen without holding the frame lock.
        if control:
            try:
                control.stop()
            except Exception:
                pass

    def start(self, hwnd):
        from windows_capture import WindowsCapture
        self.close()
        with self.lock:
            epoch = self.epoch
            self.hwnd = hwnd
            self.received = 0
            self.ready.clear()
        session = WindowsCapture(window_hwnd=hwnd, cursor_capture=False, minimum_update_interval=250)

        @session.event
        def on_frame_arrived(frame, control):
            # Copy the native buffer before the callback returns. Retain only one frame.
            image = Image.fromarray(frame.frame_buffer[:, :, [2, 1, 0]].copy())
            with self.lock:
                if epoch != self.epoch:
                    control.stop()
                    return
                self.latest = image
                self.received = time.monotonic()
                self.ready.set()

        @session.event
        def on_closed():
            with self.lock:
                if epoch == self.epoch:
                    self.latest = None
                    self.ready.set()

        control = session.start_free_threaded()
        with self.lock:
            if epoch == self.epoch:
                self.session, self.control = session, control
                return
        control.stop()

    def read(self):
        hwnd = self.windows.find_game()
        if not hwnd:
            self.close()
            return None, 'Waiting for Heroes of the Storm to open.'
        if self.windows.minimized(hwnd):
            self.close()
            return None, 'HotS is minimized. Restore it; it can stay behind other windows.'
        if hwnd != self.hwnd or not self.control or self.control.is_finished():
            self.start(hwnd)
            self.ready.wait(2.5)
        with self.lock:
            image = self.latest.copy() if self.latest is not None else None
            age = time.monotonic() - self.received
        if image is None or age > 3:
            return None, 'Waiting for a fresh HotS frame. Use borderless/windowed mode if fullscreen stops rendering.'
        return self.windows.client_image(image, hwnd), 'Reading HotS in the background.'
