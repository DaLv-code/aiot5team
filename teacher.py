import socket
import sys
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
from time import sleep
from PyQt5 import uic
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

IP = "127.0.0.1"
PORT = 5142

def goWindow(self, UIname):
    if UIname == 'Join':
        newUI = Join()
    elif UIname == 'Login':
        newUI = Login()
    self.close()
    newUI.exec_()

class Teach_Win(QMainWindow):
    def __init__(self):
        super(Teach_Win, self).__init__()
        uic.loadUi("./client_Teacher.ui", self)
        self.setWindowTitle("선생님용 학생 관리 프로그램")
        self.setFixedSize(1400, 800)  # 클라이언트 메인 창 형태 설정
        self.recv_Thread = Listen(self)
        self.recv_Thread.listen.connect(self.rcv_)
        self.recv_Thread.start()
        self.stackedWidget.setCurrentIndex(0)  # 실행 시 항상 UI 메인 페이지로 감

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
        self.exit_Btn.clicked.connect(self.close_win)

        self.wrongNumList = []  # 번호별 오답 누적 횟수 표시할 리스트
        self.scoreDict = {20: 0, 40: 0, 60: 0, 80: 0, 100: 0}  # 총 학생 시험 응시 점수 구간별 결과치 count

    def move_main(self):  # 교사 클라이언트 메인 페이지(인덱스 0)
        self.exam_result.clear()
        self.stackedWidget.setCurrentIndex(0)

    def move_page1(self):  # 교사 클라이언트 문제풀이 통계 페이지(인덱스 1)
        self.QnATable.clear()
        self.wrong_examNum.clear()
        self.exam_result.setColumnCount(3)
        self.exam_result.setColumnWidth(0, 50)
        self.exam_result.setColumnWidth(1, 7)
        self.exam_result.setColumnWidth(2, 300)
        self.exam_result.setHorizontalHeaderLabels(["학생명", "점수", "오답 문항"])
        self.exam_result.setRowCount(100)  # 시험 결과를 나타낼 테이블위젯 형태 설정
        self.stackedWidget.setCurrentIndex(1)
        self.load_examBtn.clicked.connect(self.request_Statistics)
        self.update_examBtn.clicked.connect(self.send_NewQuiz)

    def move_page2(self):  # 교사 클라이언트 QnA 페이지(인덱스 2)
        self.exam_result.clear()
        self.QnATable.setColumnCount(5)
        self.QnATable.setColumnWidth(0, 50)
        self.QnATable.setColumnWidth(1, 10)
        self.QnATable.setColumnWidth(2, 50)
        self.QnATable.setColumnWidth(3, 450)
        self.QnATable.setColumnWidth(4, 600)
        self.QnATable.setHorizontalHeaderLabels(["학생명", "완료", "교사명", "질문 내용", "답변 내용"])
        self.QnATable.setRowCount(50)  # QnA 목록을 나타낼 테이블위젯 형태 설정
        self.stackedWidget.setCurrentIndex(2)
        self.load_QnABtn.clicked.connect(self.request_QnAs)

    def move_page3(self):  # 교사 클라이언트 채팅상담 페이지(인덱스 3)
        self.wrong_examNum.clear()
        self.QnATable.clear()
        self.input_Qstu.clear()
        self.input_Answer.clear()
        if len(self.chat_space.toPlainText()) != 0:
            pass  # 이번 클라이언트 실행에서 이미 채팅 페이지를 진입한 적 있으면 채팅 시작 메세지를 출력하지 않음
        else:
            self.chat_space.append("Entered chat.\n 학생의 채팅을 대기하는 중입니다...")
            sock.send("chat".encode())  # 채팅 입장
        self.stackedWidget.setCurrentIndex(3)

    def send_msg(self):  # 채팅 메세지 전송
        self.msg = self.msg_input.toPlainText()
        sock.send(f"chat/{self.msg}".encode())
        print("보낸 메세지:", f"chat/{self.msg}")
        self.chat_space.append(f"선생님: {self.msg}")
        self.msg_input.clear()

    def request_QnAs(self):  # 서버에게 QnA 목록 요청
        sock.send("qna/X".encode())
        print("QnA 목록 요청")

    def send_QnA_ans(self):  # 서버로 QnA 답변 전송
        if len(self.input_Answer.toPlainText()) != 0 and len(self.input_Qstu.text()) != 0:
            sock.send(f'qna/{self.input_Answer.toPlainText()}/{self.input_Qstu.text()}'.encode())
            QMessageBox().information(self, "전송 완료", "입력하신 답변이 등록되었습니다.")
            print(f'qna/{self.input_Answer.toPlainText()}/{self.input_Qstu.text()}')
            self.input_Answer.clear()
            self.input_Qstu.clear()
        else:  # 학생 이름과 답변을 모두 입력해야 전송됨
            QMessageBox().warning(self, "", "질문에 답변하실 학생 이름과 답변 내용을 모두 입력해 주세요.")

    def drawGraph(self):  # 총 학생 시험 응시 점수 구간별 결과치 그래프 생성
        x = ["0~20", "20~40", "40~60", "60~80", "80~100"]
        y = [self.scoreDict[20], self.scoreDict[40], self.scoreDict[60], self.scoreDict[80], self.scoreDict[100]]
        fig = plt.figure()
        canvas = FigureCanvasQTAgg(fig)
        self.scoreGraph.addWidget(canvas, 0, 0)
        ax = plt.subplot()
        ax.yaxis.set_major_locator(MaxNLocator(integer=True))
        ax.bar(x, y, color=('red', 'darkorange', 'yellow', 'green', 'aquamarine'))
        plt.title("<Student total exam score graph>")

    def request_Statistics(self):  # 서버에게 학생 시험 결과 통계 요청
        sock.send("point/".encode())
        print("학생 문제풀이 통계 요청")
        for i in [20, 40, 60, 80, 100]:
            self.scoreDict[i] = 0  # 점수 그래프용 수치 초기화

    def send_NewQuiz(self):  # 서버에게 새로 출제할 문제 전송
        new_quiz = "/".join([self.input_NewQuiz.toPlainText(), "① " + self.input_NewQuiz_1.toPlainText(),
                             "② " + self.input_NewQuiz_2.toPlainText(), "③ " + self.input_NewQuiz_3.toPlainText(),
                             "④ " + self.input_NewQuiz_4.toPlainText(), "⑤ " + self.input_NewQuiz_5.toPlainText(),
                             "■ 정답: " + self.input_NewQuiz_A.toPlainText()])
        if len(self.input_NewQuiz_5.toPlainText()) == 0:
            new_quiz = "/".join([self.input_NewQuiz.toPlainText(), "① " + self.input_NewQuiz_1.toPlainText(),
                                 "② " + self.input_NewQuiz_2.toPlainText(), "③ " + self.input_NewQuiz_3.toPlainText(),
                                 "④ " + self.input_NewQuiz_4.toPlainText(), "None",
                                 "■ 정답: " + self.input_NewQuiz_A.toPlainText()])
        if (len(self.input_NewQuiz.toPlainText()) != 0 and len(self.input_NewQuiz_1.toPlainText()) != 0) \
                and (len(self.input_NewQuiz_2.toPlainText()) != 0 and len(self.input_NewQuiz_3.toPlainText()) != 0) \
                and (len(self.input_NewQuiz_4.toPlainText()) != 0 and len(self.input_NewQuiz_A.toPlainText()) != 0):
            sock.send(f'update/{new_quiz}'.encode())
            QMessageBox().information(self, "전송 완료", "입력하신 문제를 전송했습니다.")
            print("새 문항 전송됨: ", new_quiz)
            self.newQuiz_inputs_clear()
        else:
            QMessageBox().warning(self, "", "문제 내용, 보기 1, 2, 3, 4번과 정답은 반드시 입력하셔야 합니다.")

    def newQuiz_inputs_clear(self):  # 새로 출제한 문항을 전송한 다음 입력란 비움
        self.input_NewQuiz.clear()
        self.input_NewQuiz_1.clear()
        self.input_NewQuiz_2.clear()
        self.input_NewQuiz_3.clear()
        self.input_NewQuiz_4.clear()
        self.input_NewQuiz_5.clear()
        self.input_NewQuiz_A.clear()

    def close_win(self):  # 클라이언트 메인 창 닫음
        self.recv_Thread.running = False
        self.close()

    @pyqtSlot(str)
    def rcv_(self, rcv_data):  # 서버에게 요청한 데이터를 구분하여 수신함
        _row = 0
        if rcv_data.endswith("/qnaImfor/"):  # QnA 목록 데이터를 수신한 다음 테이블위젯 셀별로 입력
            qna_list = rcv_data.split("/qnaImfor/")
            qna_list.remove(qna_list[-1])
            for qna in qna_list:
                _col = 0
                qna.split("/")
                for i in qna.split("/"):
                    self.QnATable.setItem(_row, _col, QTableWidgetItem(i))
                    _col += 1
                _row += 1

        elif rcv_data.endswith("/score/"):  # 시험 결과 점수 목록 데이터를 수신한 다음 테이블위젯 셀별로 입력
            self.wrongNumList.clear()
            score_list = rcv_data.split("/score/")
            score_list.remove(score_list[-1])
            for score in score_list:
                _col = 0
                score.split("/")
                for e in score.split("/"):
                    self.exam_result.setItem(_row, _col, QTableWidgetItem(e))
                    _col += 1
                if int(score.split("/")[1]) in range(0, 21):  # 점수 구간별 결과치 합산 딕셔너리
                    self.scoreDict[20] += 1

                elif int(score.split("/")[1]) in range(20, 41):
                    self.scoreDict[40] += 1

                elif int(score.split("/")[1]) in range(40, 61):
                    self.scoreDict[60] += 1

                elif int(score.split("/")[1]) in range(60, 81):
                    self.scoreDict[80] += 1

                elif int(score.split("/")[1]) in range (80, 101):
                    self.scoreDict[100] += 1
                else:
                    pass
                self.drawGraph()  # 딕셔너리 value에 합산된 count를 토대로 그래프 나타냄
                wrongNum = (score.split("/")[2]).split("|")  # 제출한 문제 풀이별 틀린 문항 번호
                wrongNum.remove(wrongNum[-1])
                self.wrongNumList.extend(wrongNum)
                _row += 1

            self.wrongNumList = [int(num) for num in self.wrongNumList]
            for _num in range(1, 1001):  # 1~1000번까지 문항별 총 틀린 횟수 표시, 틀린 횟수가 없을 경우 제외
                self.wrongNumList.count(_num)
                if self.wrongNumList.count(_num) != 0:
                    self.wrong_examNum.append(str(f"{_num}번 문제: {self.wrongNumList.count(_num)}회"))

        else:  # 문제풀이 통계, QnA 목록 수신 제외 - 상담 채팅을 수신하는 경우
            sleep(0.2)
            self.chat_space.append(f"학생: {rcv_data}")

class Listen(QThread):  # 서버로부터 데이터를 수신할 스레드 클래스
    listen = pyqtSignal(str)

    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.running = False

    def run(self):
        self.running = True
        while self.running:
            self.recv_data = sock.recv(1024).decode()
            self.listen.emit(self.recv_data)


class Join(QDialog):  # 로그인창 시작
    def __init__(self):
        super().__init__()
        self.ui = uic.loadUi("Join.ui", self)
        self.idBtn.clicked.connect(self.idCheck)
        self.joinBtn.clicked.connect(self.join)

    def idCheck(self):
        id = self.idText.text()
        idImfor = 'join/' + id
        print(id)
        if id == '':
            QMessageBox().information(self, "아이디 확인", "아이디를 입력해주세요.")
        else:
            sock.send(idImfor.encode())
            idOK = sock.recv(1024).decode()
            print(f'idOK:{idOK}')

        if idOK == 'OK':
            QMessageBox().information(self, "아이디 완료", "사용가능한 아이디입니다.")
            self.idText.setEnabled(False)
            self.idBtn.setEnabled(False)
            self.joinBtn.setEnabled(True)
        elif idOK == 'NO':
            QMessageBox().information(self, "아이디 오류", "중복된 아이디입니다.")

    def join(self):
        id = self.idText.text()
        pw = self.pwText.text()
        repw = self.repwText.text()
        name = self.nameText.text()
        if self.teaBtn.isChecked():
            joinMsg = id + '/' + pw + '/' + name + '/tea'
        elif self.stuBtn.isChecked():
            joinMsg = id + '/' + pw + '/' + name + '/stu'

        if pw != repw:
            QMessageBox().information(self, "비밀번호 오류", "비밀번호가 다릅니다.")
        else:
            sock.sendall(joinMsg.encode())
            goWindow(self, "Login")


class Login(QDialog):  # 로그인창 시작
    def __init__(self):
        super().__init__()
        self.ui = uic.loadUi("Login.ui", self)
        self.loginBtn.clicked.connect(self.login)
        self.joinBtn.clicked.connect(lambda: goWindow(self, "Join"))

    def login(self):
        id = self.idText.text()
        pw = self.pwText.text()
        logImfor = 'login/' + id + '/' + pw
        sock.sendall(logImfor.encode())
        logOK = sock.recv(1024).decode().split('/')
        print(logOK)
        if logOK[0] == 'OK' and logOK[2] == 'tea':
            welcomMsg = f'[{logOK[1]} 선생님]\n로그인에 성공했습니다.'
            QMessageBox().information(self, "로그인 완료", welcomMsg)
            self.close()
            mainWindow = Teach_Win()
            mainWindow.show()

        elif logOK[0] == 'OK' and logOK[2] == 'stu':
            QMessageBox().information(self, "로그인 실패", "학생은 접속할 수 없습니다.")

        elif logOK[0] == 'NO':
            QMessageBox().information(self, "로그인 실패", "아이디 혹은 비밀번호를 확인하세요.")


if __name__ == '__main__':
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    while True:
        try:
            sock.connect((IP, PORT))
            App = QApplication(sys.argv)
            firstWindow = Login()
            firstWindow.show()
            sys.exit(App.exec_())
        except ConnectionRefusedError:  # 서버 작동 전이면 연결 실패를 알리고 곧바로 프로세스 종료
            print("Connection Failed: 다시 실행하여 주십시오.")
            break
