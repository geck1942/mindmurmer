# Ref: https://stackoverflow.com/questions/6980246/how-can-i-find-a-process-by-name-and-kill-using-ctypes
import sys
import os.path
import ctypes

# WARNING: not tested as I can currently only run in Mac (cadams)
if os.name == 'nt':
    import ctypes.wintypes

if sys.argv[1] != 'test':
    Psapi = ctypes.WinDLL('Psapi.dll')
    EnumProcesses = Psapi.EnumProcesses
    EnumProcesses.restype = ctypes.wintypes.BOOL
    GetProcessImageFileName = Psapi.GetProcessImageFileNameA
    GetProcessImageFileName.restype = ctypes.wintypes.DWORD

    Kernel32 = ctypes.WinDLL('kernel32.dll')
    OpenProcess = Kernel32.OpenProcess
    OpenProcess.restype = ctypes.wintypes.HANDLE
    CloseHandle = Kernel32.CloseHandle

MAX_PATH = 260
PROCESS_QUERY_INFORMATION = 0x0400

running_color = 'lightgreen'
bad_color = 'red'


def running_if_process_found(id, name, needle):
    if sys.argv[1] == 'test':
        ProcessId = 123456
        ProcessName = needle + '.exe'
        return _running(id, name, 'PID ' + str(ProcessId) + ' found containing string "' + needle + '": "' + ProcessName + '"')

    count = 32
    while True:
        ProcessIds = (ctypes.wintypes.DWORD*count)()
        cb = ctypes.sizeof(ProcessIds)
        BytesReturned = ctypes.wintypes.DWORD()
        if EnumProcesses(ctypes.byref(ProcessIds), cb, ctypes.byref(BytesReturned)):
            if BytesReturned.value < cb:
                break
            else:
                count *= 2
        else:
            sys.exit("Call to EnumProcesses failed")

    for index in range(BytesReturned.value / ctypes.sizeof(ctypes.wintypes.DWORD)):
        ProcessId = ProcessIds[index]
        hProcess = OpenProcess(PROCESS_QUERY_INFORMATION, False, ProcessId)
        if hProcess:
            ImageFileName = (ctypes.c_char*MAX_PATH)()
            if GetProcessImageFileName(hProcess, ImageFileName, MAX_PATH) > 0:
                filename = os.path.basename(ImageFileName.value)
                if needle in filename:
                    CloseHandle(hProcess)
                    return _running(id, name, 'PID ' + str(ProcessId) + ' found containing string "' + needle + '": "' + ImageFileName.value + '"')
            CloseHandle(hProcess)

    return _not_running(id, name, 'No processes found containing string "' + needle + '"')


def _running(id, name, details):
    return {'id': id, 'name': name, 'color': running_color, 'text': "running", 'details': details}


def _not_running(id, name, details):
    return {'id': id, 'name': name, 'color': bad_color, 'text': "STOPPED", 'details': details}


class Status():

    def get_statuses(self):
        statuses = [
            self._status_fr0st(),
            self._status_lights(),
            self._status_osc(),
            self._status_sound(),
        ]

        bads = filter(lambda s: s['color'] != running_color, statuses)

        if len(bads) == 0:
            all_good_status = {'id': "all", 'name': "ALL", 'color': running_color, 'text': "running", 'details': "All engine running"}
            statuses.insert(0, all_good_status)
        else:
            bad_names = [s.name for s in bads]
            all_bad_status = {'id': "all", 'name': "ALL", 'color': bad_color, 'text': "not fully up", 'details': ', '.join(bad_names) + ' not running'}
            statuses.insert(0, all_bad_status)

        return statuses

    def _status_fr0st(self):
        return running_if_process_found("fr0st", "fr0st", 'fr0st.py')

    def _status_lights(self):
        return running_if_process_found("lights", "Lights", 'MindMurmur.Lights.exe')

    def _status_osc(self):
        return running_if_process_found("osc", "OSC and EEG", 'server.py')

    def _status_sound(self):
        return running_if_process_found("sound", "Sound", 'sound_controller.py')
