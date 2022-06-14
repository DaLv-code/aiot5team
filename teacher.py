import sys
from PyQt5 import uic
from PyQt5.QtWidgets import *
from PyQt5.QtCore import pyqtSlot, pyqtSignal, QThread
import PyQt5.QtGui
from socket import *

PORT=5150

class Teach_Win(QMainWindow):
    def __init__(self):
        super(Teach_Win, self).__init__()
        uic.loadUi("client_Teacher.ui", self)
        self.setWindowTitle("선생님용 학생 관리 프로그램")
        self.setWindowIcon(PyQt5.QtGui.QIcon("./teacher.png"))
        # 출처 명시 조건에 따라 선생님 아이콘 이미지 출처 주소
        # - https://www.flaticon.com/premium-icon/teacher_4539225?term=teacher&related_id=4539225
        self.setFixedSize(1250, 690)
        self.stackedWidget.setCurrentIndex(0)  # 프로그램 실행 시 메인 페이지부터 나오게 설정

        self.checkStatistic_Btn.clicked.connect(self.move_page1)
        self.checkQnA_Btn.clicked.connect(self.move_page2)
        self.RTchatBtn.clicked.connect(self.move_page3)
        self.to_QnABtn.clicked.connect(self.move_page2)
        self.to_QnABtn2.clicked.connect(self.move_page2)
        self.to_RTchatBtn.clicked.connect(self.move_page3)
        self.to_mainBtn.clicked.connect(self.move_main)
        self.to_mainBtn2.clicked.connect(self.move_main)
        self.to_statisticBtn.clicked.connect(self.move_page1)
        self.msg_sendBtn.clicked.connect(self.send_msg)
        self.QnA_loadBtn.clicked.connect(self.request_QnAs)
        self.exit_Btn.clicked.connect(lambda: self.close())
        #  └ QPushButton 클릭 시 각 함수로 연결됨, 닫기 버튼 클릭시 창 닫힘 (동시에 선생님 클라이언트 창 클래스 실행 종료)

    def move_main(self):  # 교사 클라이언트 메인 페이지(인덱스 0)
        self.stackedWidget.setCurrentIndex(0)

    def move_page1(self):  # 교사 클라이언트 문제풀이 통계 페이지(인덱스 1)
        self.stackedWidget.setCurrentIndex(1)

    def move_page2(self):  # 교사 클라이언트 QnA 페이지(인덱스 2)
        self.QnATable.setColumnCount(5)
        self.QnATable.setHorizontalHeaderLabels(["학생명", "완료", "교사명", "질문 내용", "답변 내용"])
        self.QnATable.setColumnWidth(0, 40)
        self.QnATable.setColumnWidth(1, 10)
        self.QnATable.setColumnWidth(2, 40)
        self.QnATable.setColumnWidth(3, 300)
        self.QnATable.setColumnWidth(4, 300)
        self.QnATable.setRowCount(30)
        # └ QnA 페이지의 QnA 목록들을 보여 줄 QTableWidget 형태 구성
        self.recv_Thread = Listen(self)
        self.recv_Thread.listen.connect(self.rcv_)
        self.recv_Thread.start()
        # └ 차후 서버에서 받아 올 QnA 목록 문자열을 받아들일 스레드 실행
        self.stackedWidget.setCurrentIndex(2)

    def move_page3(self):  # 교사 클라이언트 채팅상담 페이지(인덱스 3)
        self.recv_Thread = Listen(self)
        self.recv_Thread.listen.connect(self.rcv_)
        self.recv_Thread.start()
        # └ 서버로부터 채팅을 받아들이는 쓰레드 실행
        self.stackedWidget.setCurrentIndex(3)

    def send_msg(self):
        self.msg = self.msg_input.toPlainText()
        self.recv_Thread.teach_sock.send(f"chat/{self.msg}".encode())  # 위의 텍스트 내용을 인코딩 후 QThread와 연결된 소켓을 통해 서버로 송신
        print("보낸 메세지:", f"chat/{self.msg}")
        self.chat_space.append(f"선생님: {self.msg}")
        self.msg_input.clear()

    def request_QnAs(self):
        self.recv_Thread.teach_sock.send("qna/X".encode())
        print("QnA 목록 요청")

    @pyqtSlot(str)
    def rcv_(self, rcv_):
        print(rcv_)
        _r = 0
        if rcv_.endswith("qnaImfor/"):
            for j in rcv_.split("/")[0:5]:
                for index in range(0, 5):
                    self.QnATable.setItem(_r, index, QTableWidgetItem(rcv_.split("/")[index]))
                    # 스플릿된 문자열 유닛을 하나씩 테이블 위젯 아이템으로 배치한다
            _r += 1  # 해당 QnAdata 의 요소 배치가 끝났으면 다음 순서 요소로 넘어가도록 한다.
        else:
            self.chat_space.append(f"학생: {rcv_}")

class Listen(QThread):
    listen = pyqtSignal(str)

    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.teach_sock = socket()
        self.teach_sock.connect(('localhost', PORT))

    def run(self):
        while True:
            self.recv_data = self.teach_sock.recv(1024).decode()
            self.listen.emit(self.recv_data)
    # └ 서버로 데이터 수신을 요청하는 신호를 발생시킬 QThread
