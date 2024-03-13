import sys
import logging
import time
import win32serviceutil
import win32service
import win32event
import win32timezone
import servicemanager
from ky_interface import KyInterface
from Listener import tcp_server

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

        ky_interface = KyInterface()
        ky_interface.tcp_thread.daemon = True
        ky_interface.tcp_thread.start()

        try:
            while self.is_alive:
                # tcp서버에서 알람데이터를 받을경우 즉시 전송합니다.
                while not tcp_server.alarm_queue.empty():
                    alarm = tcp_server.alarm_queue.get()
                    ky_interface.db.insert_list_data(alarm)  # 체크

                # tcp서버에 전송할 데이터 생성될 경우 최신 데이터로 update합니다.
                while not tcp_server.data_queue.empty():
                    tcp_data = tcp_server.data_queue.get()
                    if len(tcp_data) > 0:
                        for key, value in tcp_data.items():
                            ky_interface.data_dict.update(tcp_data)

                # config.yml에 설정한 주기마다 update되어있는 데이터를 전송합니다.
                if ky_interface.can_i_send():
                    for sno in list(ky_interface.data_dict):  # list()를 사용하여 사본을 만들어 순회
                        ky_interface.db.insert_list_data(ky_interface.data_dict.pop(sno))  # data_dict에서 데이터 추출 및 삭제
                time.sleep(1)

        except Exception as e:
            logging.error(f"service error: {e}")


if __name__ == "__main__":
    if len(sys.argv) == 1:
        # 서비스를 시작할 때 필요한 초기화
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(MyService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        # 커맨드 라인에서 서비스로 실행할 때의 초기화
        win32serviceutil.HandleCommandLine(MyService)
