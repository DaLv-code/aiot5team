from PyQt5 import uic
from PyQt5.QtWidgets import *
from PyQt5.QtCore import pyqtSlot, pyqtSignal, QThread
from socket import *

PORT=5150


class Teach_Win(QMainWindow):
    def __init__(self):
        super(Teach_Win, self).__init__()
        uic.loadUi("client_Teacher.ui", self)
        self.setWindowTitle("선생님용 학생 관리 프로그램")
        # 출처 명시 조건에 따라 선생님 아이콘 이미지 출처 주소
        # - https://www.flaticon.com/premium-icon/teacher_4539225?term=teacher&related_id=4539225
        self.setFixedSize(1400, 800)
        self.stackedWidget.setCurrentIndex(0)

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
        self.QnA_registerBtm.clicked.connect(self.send_QnA_ans)
        self.exit_Btn.clicked.connect(lambda: self.close())

    def move_main(self):  # 교사 클라이언트 메인 페이지(인덱스 0)
        self.stackedWidget.setCurrentIndex(0)

    def move_page1(self):  # 교사 클라이언트 문제풀이 통계 페이지(인덱스 1)
        self.stackedWidget.setCurrentIndex(1)

    def move_page2(self):  # 교사 클라이언트 QnA 페이지(인덱스 2)
        self.QnATable.clear()
        self.QnATable.setColumnCount(5)
        self.QnATable.setHorizontalHeaderLabels(["학생명", "완료", "교사명", "질문 내용", "답변 내용"])
        self.QnATable.setColumnWidth(0, 50)
        self.QnATable.setColumnWidth(1, 5)
        self.QnATable.setColumnWidth(2, 50)
        self.QnATable.setColumnWidth(3, 600)
        self.QnATable.setColumnWidth(4, 600)
        self.QnATable.setRowCount(30)

        self.recv_Thread = Listen(self)
        self.recv_Thread.listen.connect(self.rcv_)
        self.recv_Thread.start()
        self.stackedWidget.setCurrentIndex(2)
        self.request_QnAs()

    def move_page3(self):  # 교사 클라이언트 채팅상담 페이지(인덱스 3)
        self.recv_Thread = Listen(self)
        self.recv_Thread.listen.connect(self.rcv_)
        self.recv_Thread.start()
        self.stackedWidget.setCurrentIndex(3)

    def send_msg(self):
        self.msg = self.msg_input.toPlainText()
        self.recv_Thread.teach_sock.send(f"chat/{self.msg}".encode())
        print("보낸 메세지:", f"chat/{self.msg}")
        self.chat_space.append(f"선생님: {self.msg}")
        self.msg_input.clear()

    def request_QnAs(self):
        self.recv_Thread.teach_sock.send("qna/X".encode())
        print("QnA 목록 요청")

    # def get_Question(self):
    #     currentRow = self.QnATable.currentRow()
    #     currentCol = self.QnATable.currentColumn()
    #     if currentRow > -1:
    #         question = (self.QnATable.item(currentRow, currentCol).text(),)
    #     self.Question.setText(question)

    def send_QnA_ans(self):
        self.recv_Thread.teach_sock.send("qna/".encode())
        print(f"QnA 답변{self.input_Answer.toPlainText()}")

    @pyqtSlot(str)
    def rcv_(self, rcv_):
        _row = 0
        if rcv_.endswith("/qnaImfor/"):
            rcv_.split("/qnaImfor/")
            for qna in rcv_.split("/qnaImfor/"):
                _col = 0
                qna.split("/")
                for i in qna.split("/"):
                    self.QnATable.setItem(_row, _col, QTableWidgetItem(i))
                    _col += 1
                _row += 1
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
