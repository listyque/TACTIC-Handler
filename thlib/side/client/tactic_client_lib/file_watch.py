"""One recursive Windows directory notification handle, with a bounded GUI outbox."""
import os
import struct
import threading


class WorkspaceWatch:
    LIMIT = 4096

    def __init__(self, root):
        self.root = str(root)
        self.stop_event = threading.Event()
        self.ready = threading.Event()
        self.lock = threading.Lock()
        self.pending = set()
        self.overflow = False
        self.error = ''
        self.thread = threading.Thread(target=self.run, name='FileWorkspaceWatch', daemon=True)

    def start(self):
        self.thread.start()

    def stop(self):
        self.stop_event.set()

    def take(self):
        with self.lock:
            result = {'paths':sorted(self.pending), 'overflow':self.overflow, 'error':self.error}
            self.pending.clear()
            self.overflow = False
            self.error = ''
            return result

    def collect(self, raw):
        with self.lock:
            if not raw:
                self.overflow = True
                return
            offset = 0
            while True:
                if offset+12 > len(raw):
                    self.overflow = True
                    return
                following, _, length = struct.unpack_from('<III',raw,offset)
                if length % 2 or offset+12+length > len(raw):
                    self.overflow = True
                    return
                path = raw[offset+12:offset+12+length].decode('utf-16-le').replace('\\','/')
                if len(self.pending) < self.LIMIT:
                    self.pending.add(path)
                else:
                    self.overflow = True
                if not following:
                    break
                if following < 12+length or offset+following >= len(raw):
                    self.overflow = True
                    return
                offset += following

    def run(self):
        if os.name != 'nt':
            self.error = 'Automatic workspace watching is available on Windows. Use Reconcile on this platform.'
            self.ready.set()
            return
        import ctypes
        from ctypes import wintypes as w
        class Overlapped(ctypes.Structure):
            _fields_ = [('Internal',ctypes.c_size_t),('InternalHigh',ctypes.c_size_t),
                        ('Offset',w.DWORD),('OffsetHigh',w.DWORD),('hEvent',w.HANDLE)]
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel.CreateFileW.argtypes = [w.LPCWSTR,w.DWORD,w.DWORD,ctypes.c_void_p,w.DWORD,w.DWORD,w.HANDLE]
        kernel.CreateFileW.restype = w.HANDLE
        kernel.CreateEventW.argtypes = [ctypes.c_void_p,w.BOOL,w.BOOL,w.LPCWSTR]
        kernel.CreateEventW.restype = w.HANDLE
        kernel.ReadDirectoryChangesW.argtypes = [w.HANDLE,ctypes.c_void_p,w.DWORD,w.BOOL,w.DWORD,ctypes.c_void_p,ctypes.POINTER(Overlapped),ctypes.c_void_p]
        kernel.ReadDirectoryChangesW.restype = w.BOOL
        kernel.WaitForSingleObject.argtypes = [w.HANDLE,w.DWORD]
        kernel.WaitForSingleObject.restype = w.DWORD
        kernel.GetOverlappedResult.argtypes = [w.HANDLE,ctypes.POINTER(Overlapped),ctypes.POINTER(w.DWORD),w.BOOL]
        kernel.GetOverlappedResult.restype = w.BOOL
        kernel.CancelIoEx.argtypes = [w.HANDLE,ctypes.POINTER(Overlapped)]
        kernel.CloseHandle.argtypes = [w.HANDLE]
        kernel.ResetEvent.argtypes = [w.HANDLE]
        handle = event = None
        try:
            handle = kernel.CreateFileW(self.root,1,7,None,3,0x02000000|0x40000000,None)
            if handle == ctypes.c_void_p(-1).value:
                handle = None
                raise ctypes.WinError(ctypes.get_last_error())
            event = kernel.CreateEventW(None,True,False,None)
            if not event:
                raise ctypes.WinError(ctypes.get_last_error())
            buffer = ctypes.create_string_buffer(65536)
            while not self.stop_event.is_set():
                overlap = Overlapped(hEvent=event)
                kernel.ResetEvent(event)
                if not kernel.ReadDirectoryChangesW(handle,buffer,len(buffer),True,0x1|0x2|0x8|0x10,None,ctypes.byref(overlap),None):
                    raise ctypes.WinError(ctypes.get_last_error())
                self.ready.set()
                while kernel.WaitForSingleObject(event,250) == 258:
                    if self.stop_event.is_set():
                        kernel.CancelIoEx(handle,ctypes.byref(overlap))
                received = w.DWORD()
                if not kernel.GetOverlappedResult(handle,ctypes.byref(overlap),ctypes.byref(received),False):
                    if self.stop_event.is_set():
                        break
                    raise ctypes.WinError(ctypes.get_last_error())
                self.collect(buffer.raw[:received.value])
        except (OSError, UnicodeError) as error:
            with self.lock:
                self.error = str(error)
                self.overflow = True
        finally:
            self.ready.set()
            if handle:
                kernel.CloseHandle(handle)
            if event:
                kernel.CloseHandle(event)
