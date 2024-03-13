import sys
import logging
import time
from MR_FEMS_equip_interface import Equipment_Interface_Service
import win32serviceutil
import win32service
import win32event
import win32timezone
import servicemanager


class MyService(win32serviceutil.ServiceFramework):
    _svc_name_ = 'MR_FEMS_equip_interface_service'
    _svc_display_name_ = 'MR_FEMS_equip_interface_service'

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        self.is_alive = True

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
        self.is_alive = False

    def SvcDoRun(self):
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                              servicemanager.PYS_SERVICE_STARTED,
                              (self._svc_name_, ''))
        self.main()

    def main(self):
        time.sleep(20)
        interface = Equipment_Interface_Service()
        interface.tcp_server.make_tcp_server_thread()
        interface.tcp_server.start_server()

        while self.is_alive:
            try:
                while self.is_alive:

                    if interface.can_i_send_data():
                        interface.send_data()
                    else:
                        time.sleep(1)
            except Exception as e:
                logging.warning(e)
                print(e)
                sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) == 1:
        # 서비스를 시작할 때 필요한 초기화
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(MyService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        # 커맨드 라인에서 서비스로 실행할 때의 초기화
        win32serviceutil.HandleCommandLine(MyService)
