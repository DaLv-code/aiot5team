import socket
import threading
import sqlite3
import sys
import time
from PyQt5.QtWidgets import *
from PyQt5 import QtCore
from PyQt5 import uic
from PyQt5.QtGui import QPixmap
import teacher
import pymysql
from PyQt5.QtCore import *
import pymysql
from PyQt5.QtCore import *
from PyQt5 import QtGui
import random

IP="127.0.0.1"
PORT=5142

main_form = uic.loadUiType("student.ui")[0]
sub_form = uic.loadUiType("student_sub.ui")[0]

def goWindow(self,UIname):
    if UIname=='Join': newUI=Join()
    elif UIname=='Login': newUI=Login()
    self.close()
    newUI.exec_()

class Join(QDialog):  # 로그인창 시작
    def __init__(self):
        super().__init__()
        self.ui = uic.loadUi("Join.ui", self)
        self.idBtn.clicked.connect(self.idCheck)
        self.joinBtn.clicked.connect(self.join)
    
    def idCheck(self):     
        id=self.idText.text()
        idImfor='join/'+id
        print(id)
        if id=='':
            QMessageBox().information(self,"아이디 확인","아이디를 입력해주세요.")
        else:
            sock.send(idImfor.encode())
            idOK=sock.recv(1024).decode()
            print(f'idOK:{idOK}')

        if idOK=='OK':
            QMessageBox().information(self,"아이디 완료","사용가능한 아이디입니다.")
            self.idText.setEnabled(False)
            self.idBtn.setEnabled(False)
            self.joinBtn.setEnabled(True)            
        elif idOK=='NO':
            QMessageBox().information(self,"아이디 오류","중복된 아이디입니다.")
    
    def join(self):
        id=self.idText.text()
        pw=self.pwText.text()
        repw=self.repwText.text()
        name=self.nameText.text()
        if self.teaBtn.isChecked():
            joinMsg=id+'/'+pw+'/'+name+'/tea'
        elif self.stuBtn.isChecked():
            joinMsg=id+'/'+pw+'/'+name+'/stu'

        if pw!=repw:
            QMessageBox().information(self,"비밀번호 오류","비밀번호가 다릅니다.")
        else:            
            sock.sendall(joinMsg.encode())
            goWindow(self,"Login")

class Login(QDialog):  # 로그인창 시작
    def __init__(self):
        super().__init__()
        self.ui = uic.loadUi("Login.ui", self)
        self.loginBtn.clicked.connect(self.login)
        self.joinBtn.clicked.connect(lambda: goWindow(self,"Join"))

    def login(self):
        id=self.idText.text()
        pw=self.pwText.text()
        logImfor='login/'+id+'/'+pw
        sock.sendall(logImfor.encode())
        logOK=sock.recv(1024).decode().split('/')
        print(logOK)

        if logOK[0]=='OK' and logOK[2]=='tea':
            QMessageBox().information(self,"로그인 실패","선생님은 접속할 수 없습니다.")

        elif logOK[0]=='OK' and logOK[2]=='stu':
            myNickName = logOK[1]
            welcomMsg=f'[{logOK[1]} 학생]\n로그인에 성공했습니다.'       
            QMessageBox().information(self,"로그인 완료",welcomMsg)
            self.close()
            mainWindow = MainWindow()
            mainWindow.show()

        elif logOK[0]=='NO':
            QMessageBox().information(self,"로그인 실패","아이디 혹은 비밀번호를 확인하세요.")

# 클래스
class MainWindow(QMainWindow, main_form):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        # 리시브 시작
        self.th_recive = Recive(self)
        self.th_recive.chat.connect(self.reciveMsg)
        self.th_recive.start()
        self.th_timer = Timer(self)
        self.th_timer.timeout.connect(self.timeout)
        self.th_subWindow = SubWindow(self)
        self.th_subWindow.request.connect(self.request)
        # 변수 설정
        self.score = 0
        self.nickName = 'chounkal'
        self.teacher = '류홍걸'
        self.data = []
        self.qnaData = []
        self.question = []
        self.radioBtn_list = []
        self.qList = ''
        self.rating = ''
        # 버튼 연결
        self.learning_Btn.clicked.connect(self.learningPage)
        self.test_Btn.clicked.connect(self.testPage)
        self.back_Btn1.clicked.connect(self.mainPage)
        self.back_Btn2.clicked.connect(self.mainPage)
        self.pushButton_2.clicked.connect(self.mainPage)
        self.pushButton_3.clicked.connect(self.mainPage)
        self.back_Btn1_2.clicked.connect(self.mainPage)
        self.pushButton_5.clicked.connect(self.mainPage)
        self.result_Btn.clicked.connect(self.resultPage)
        self.qna_Btn.clicked.connect(self.qnaPage)
        self.chatpage_Btn.clicked.connect(self.chatPage)
        self.pushButton_6.clicked.connect(self.myInfoPage)
        self.search_lineEdit.returnPressed.connect(self.searcheQuestion)
        self.chat_lineEdit.returnPressed.connect(self.sendMsg)
        self.next_Btn.clicked.connect(lambda: self.testStart('next'))
        self.tableWidget.cellClicked.connect(lambda: self.tableClick_signal('inquiry'))
        self.newQnA_Btn.clicked.connect(lambda: self.tableClick_signal('QnA'))

        self.result_Btn.hide()
        self.bringData()
        # 자동완성 기능
        recommended_words = []
        for i in self.question:
            if self.search_lineEdit.text() in i:
                recommended_words.append(i)

        completer = QCompleter(recommended_words)
        self.search_lineEdit.setCompleter(completer)

    # 나의 획득 포인트 보기
    def myInfoPage(self):
        sock.send('rating/'.encode())
        self.stack.setCurrentIndex(6)

    # Q&A 테이블 구성
    def tableSetting(self):
        self.tableWidget.clear()
        time.sleep(0.1)
        self.title = ['작성자', '답변여부', '담당자', '질문', '답변']

        if not bool(self.qnaData):
            print('없음')
            self.tableWidget.setRowCount(0)
            self.tableWidget.setHorizontalHeaderLabels(self.title)
        else:
            print('xxxxxxx :', int(len(self.qnaData[0]) / 5))
            self.tableWidget.setRowCount(int(len(self.qnaData[0]) / 5))
            self.tableWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
            self.tableWidget.setHorizontalHeaderLabels(self.title)
            self.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

            row = 0
            col = 0
            for i in self.qnaData[0]:
                self.tableWidget.setItem(row, col, QTableWidgetItem(i))
                self.tableWidget.item(row, col).setTextAlignment(Qt.AlignCenter)
                col += 1
                if col == 5:
                    row += 1
                    col = 0

    # Q&A 페이지에서 질문 눌렀을 때 조회
    def tableClick_signal(self, qnaSignal):
        self.userSelect_row = self.tableWidget.currentRow()

        if qnaSignal == 'inquiry':
            self.qnaSignal = qnaSignal
            self.th_subWindow.label_4.setText('상세보기')
        else:
            self.qnaSignal = qnaSignal
            self.th_subWindow.label_4.setText('Q&A등록')

        self.th_subWindow.qnaInfo()
        self.th_subWindow.show()

    # 문제 중복출제 방지를 위해 랜덤으로 뽑기
    def randomNumberSet(self):
        self.questionIndex = []

        for i in range(len(self.data)):
            self.questionIndex.append(i)

        random.shuffle(self.questionIndex)

    # 문제풀이
    def testPage(self):
        self.count = 0
        self.th_timer.minute = 0
        self.th_timer.second = 0
        self.count_label.setText('제출한 문제 수 : 0')
        buttonStart = QMessageBox.question(self, '문제풀기', '제한 시간은 10분이며, 점수는 나의 정보에 반영됩니다.',
                                           QMessageBox.Yes | QMessageBox.No)

        if buttonStart == QMessageBox.Yes:
            self.testStart('start')
            self.loop = True

    # 상담페이지로 이동
    def chatPage(self):
        self.stack.setCurrentWidget(self.chat_Page)

    # 상담페이지에서 메시지 전송
    def sendMsg(self):
        self.msg = self.chat_lineEdit.text()      
        sock.send(f'chat/{self.msg}'.encode())
        self.chat_textBrowser.append(f'나 : {self.msg}')
        print('보낸 메시지 :', self.msg)
        self.chat_lineEdit.clear()

    # qna페이지로 이동
    def qnaPage(self):
        self.qnaSignal = ''
        self.request('qna/X')
        self.tableSetting()
        self.stack.setCurrentWidget(self.qna_Page)

    # 시험결과 페이지
    def resultPage(self):
        self.randomNumberSet()
        self.result_Btn.hide()
        self.next_Btn.setEnabled(True)
        self.back_Btn2.setEnabled(True)
        self.stack.setCurrentWidget(self.result_page)

    # 시험 작동 핸들러
    def testStart(self, testSignal):
        sock.sendall('/update'.encode())
        if testSignal == 'start':
            self.randomNumberSet()
            self.make_answer()
            self.th_timer.start()

        elif testSignal == 'next':
            self.count += 4
            self.count_label.setText(f'제출한 문제 수 : {self.count}')
            self.grading()
            self.make_answer()

        if self.count == 20:
            self.grading()
            self.next_Btn.setEnabled(False)
            self.back_Btn2.setEnabled(False)
            self.timeout('timeout')
            self.result_Btn.show()

    # 문제 만들기
    def make_answer(self):
        self.testSetting()
        question1_index = self.questionIndex.pop()
        self.testLabel1.setText(self.data[question1_index][0])
        question2_index = self.questionIndex.pop()
        self.testLabel2.setText(self.data[question2_index][0])
        question3_index = self.questionIndex.pop()
        self.testLabel3.setText(self.data[question3_index][0])
        question4_index = self.questionIndex.pop()
        self.testLabel4.setText(self.data[question4_index][0])

        self.example(self.questin1_BtnList, self.questin1_BtnText, self.questin1_tempAnswer, self.questin1_finalAnswer,
                     question1_index, self.testLayout1)
        self.example(self.questin2_BtnList, self.questin2_BtnText, self.questin2_tempAnswer, self.questin2_finalAnswer,
                     question2_index, self.testLayout2)
        self.example(self.questin3_BtnList, self.questin3_BtnText, self.questin3_tempAnswer, self.questin3_finalAnswer,
                     question3_index, self.testLayout3)
        self.example(self.questin4_BtnList, self.questin4_BtnText, self.questin4_tempAnswer, self.questin4_finalAnswer,
                     question4_index, self.testLayout4)
        print('출제 문제:', self.wrong_temp)
        print('정답 :', self.final_BtnList)

        self.stack.setCurrentWidget(self.test_page)

    # 문제에 대한 답(라디오버튼) 만들기
    def example(self, questin_BtnList, questin_BtnText, questin_tempAnswer, questin_finalAnswer, question1_index,
                where):
        question = self.data[question1_index]
        questin_tempAnswer.append(list(question[-1].split('：')[-1]))
        self.wrong_temp.append(question[0])

        for i in questin_tempAnswer[:]:
            for j in i[:]:
                try:
                    if j == '1':
                        j = '①'
                        questin_finalAnswer.append(j)
                    elif j == '2':
                        j = '②'
                        questin_finalAnswer.append(j)
                    elif j == '3':
                        j = '③'
                        questin_finalAnswer.append(j)
                    elif j == '4':
                        j = '④'
                        questin_finalAnswer.append(j)
                    elif j == '5':
                        j = '⑤'
                        questin_finalAnswer.append(j)
                except:
                    i.remove(j)

        if bool(question[5]) == True:
            how_many = 5
        else:
            how_many = 4

        temp = 1

        for i in range(how_many):
            self.answerRadio = QRadioButton(question[temp], self)
            self.radioBtn_list.append(self.answerRadio)
            questin_BtnText.append(question[temp])
            questin_BtnList.append(self.answerRadio)
            where.addWidget(self.answerRadio)
            self.answerRadio.setAutoExclusive(False)
            temp += 1

    # 채점
    def grading(self):
        for i, j in zip(self.question_BtnList, self.wrong_temp):
            for idx, v in enumerate(i[:]):
                if not v.isChecked():
                    i.remove(v)
                else:
                    i[i.index(v)] = v.text()[0]
            if len(i) == 0:
                i.append(None)
        print('제출 :', self.question_BtnList)

        for i, j in enumerate(zip(self.question_BtnList, self.final_BtnList, self.wrong_temp)):
            if j[0] == j[1]:
                self.score += 4
                #####
                self.result_textBrowser.append('정답!')
                self.result_textBrowser.append(j[2])
                for idx, v in enumerate(self.data):
                    if j[2] in v:
                        self.result_textBrowser.append(self.data[idx][-1])
                        self.result_textBrowser.append('')
            else:
                self.result_textBrowser.append('오답!')
                self.wrongQuestion_list.append(j[2])
                self.result_textBrowser.append(j[2])
                for idx, v in enumerate(self.data):
                    if j[2] in v:
                        self.result_textBrowser.append(self.data[idx][-1])
                        self.result_textBrowser.append('')

        print('틀린 문제 : ', self.wrongQuestion_list)
        if len(self.wrongQuestion_list) > 0:
            qNum = self.wrongQuestion_list[0].split('. ')
            print('틀린 문제 번호 : ',qNum[0])
            self.qList+=qNum[0]+'|'
            print('점수 : ', self.score)

    # 학습페이지에서 검색한 문제에 대한 답 찾기
    def searcheQuestion(self):
        self.answer_textBrowser.clear()
        self.text = self.search_lineEdit.text()
        for i in self.data:
            if self.text in i:
                self.answerFind(i, self.answer_textBrowser.append)

    # 학습페이지 세팅 함수
    def learningPage(self):
        self.bringData()
        self.info_textBrowser.clear()
        self.stack.setCurrentWidget(self.learning_page)

        for i in self.data:
            self.answerFind(i, self.info_textBrowser.append)

    # 문제 데이터 정제하여 가공
    def answerFind(self, i, where):
        if '1' in i[-1] and '2' in i[-1]:
            where(f'{i[0]}\n- 정답 : {i[1].split("①")[-1]}\n- 정답 : {i[2].split("②")[-1]}\n')
        elif '1' in i[-1] and '3' in i[-1]:
            where(f'{i[0]}\n- 정답 : {i[1].split("①")[-1]}\n- 정답 : {i[3].split("③")[-1]}\n')
        elif '1' in i[-1] and '4' in i[-1]:
            where(f'{i[0]}\n- 정답 : {i[1].split("①")[-1]}\n- 정답 : {i[4].split("④")[-1]}\n')
        elif '1' in i[-1] and '5' in i[-1]:
            where(f'{i[0]}\n- 정답 : {i[1].split("①")[-1]}\n- 정답 : {i[5].split("⑤")[-1]}\n')
        elif '2' in i[-1] and '3' in i[-1]:
            where(f'{i[0]}\n- 정답 : {i[2].split("②")[-1]}\n- 정답 : {i[3].split("③")[-1]}\n')
        elif '2' in i[-1] and '4' in i[-1]:
            where(f'{i[0]}\n- 정답 : {i[2].split("②")[-1]}\n- 정답 : {i[4].split("④")[-1]}\n')
        elif '2' in i[-1] and '5' in i[-1]:
            where(f'{i[0]}\n- 정답 : {i[2].split("②")[-1]}\n- 정답 : {i[5].split("⑤")[-1]}\n')
        elif '3' in i[-1] and '4' in i[-1]:
            where(f'{i[0]}\n- 정답 : {i[3].split("③")[-1]}\n- 정답 : {i[4].split("④")[-1]}\n')
        elif '3' in i[-1] and '5' in i[-1]:
            where(f'{i[0]}\n- 정답 : {i[3].split("③")[-1]}\n- 정답 : {i[5].split("⑤")[-1]}\n')
        elif '4' in i[-1] and '5' in i[-1]:
            where(f'{i[0]}\n- 정답 : {i[4].split("④")[-1]}\n- 정답 : {i[5].split("⑤")[-1]}\n')
        elif '1' in i[-1]:
            where(f'{i[0]}\n- 정답 : {i[1].split("①")[-1]}\n')
        elif '2' in i[-1]:
            where(f'{i[0]}\n- 정답 : {i[2].split("②")[-1]}\n')
        elif '3' in i[-1]:
            where(f'{i[0]}\n- 정답 : {i[3].split("③")[-1]}\n')
        elif '4' in i[-1]:
            where(f'{i[0]}\n- 정답 : {i[4].split("④")[-1]}\n')

    # db 파일 가져오기
    def bringData(self):
        # connection = pymysql.connect(host='localhost', port=3306, user='root',
        #                              password='1234', db='project', charset='utf8')
        # cursor = connection.cursor()
        # sql = 'SELECT * FROM 필기시험'
        # cursor.execute(sql)
        # result = cursor.fetchall()

        # for res in result:
        #     self.data.append(list(res))
        #     self.question.append(res[0])
        # connection.close()

        #Sqlite환경 테스트용
        self.data.clear()
        self.question.clear()
        self.conn = sqlite3.connect('studentDB')
        self.cursor = self.conn.cursor()
        sql = 'SELECT * FROM studentDB'
        self.cursor.execute(sql)
        result = self.cursor.fetchall()

        for res in result:
            self.data.append(list(res))
            self.question.append(res[0])
        print(len(self.data))
        print(self.data[-1])
        self.conn.close()

    # 변수 및 문제풀기 화면 초기화
    def testSetting(self):
        for i in self.radioBtn_list:
            i.deleteLater()
        self.radioBtn_list.clear()
        self.questin1_BtnText = []
        self.questin2_BtnText = []
        self.questin3_BtnText = []
        self.questin4_BtnText = []
        self.questin1_BtnList = []
        self.questin2_BtnList = []
        self.questin3_BtnList = []
        self.questin4_BtnList = []
        self.questin1_tempAnswer = []
        self.questin2_tempAnswer = []
        self.questin3_tempAnswer = []
        self.questin4_tempAnswer = []
        self.questin1_finalAnswer = []
        self.questin2_finalAnswer = []
        self.questin3_finalAnswer = []
        self.questin4_finalAnswer = []
        self.wrong_temp = []
        self.wrongQuestion_list = []
        self.question_BtnList = [self.questin1_BtnList, self.questin2_BtnList, self.questin3_BtnList,
                                 self.questin4_BtnList]
        self.final_BtnList = [self.questin1_finalAnswer, self.questin2_finalAnswer, self.questin3_finalAnswer,
                              self.questin4_finalAnswer]

    # 메인페이지로 이동
    def mainPage(self):
        self.randomNumberSet()
        self.result_Btn.hide()
        self.next_Btn.setEnabled(True)
        self.stack.setCurrentWidget(self.main_page)
    # 쓰레드와 시그널로 통신
    @pyqtSlot(str)
    def request(self, request):
        sock.send(request.encode())
        print('보낸 요청 :', request)
    # 받은메시지 관리
    @pyqtSlot(str)
    def reciveMsg(self, msg):
        self.chat_textBrowser.append(f'상대방 : {msg}')
    # 타이머기능 핸들러
    @pyqtSlot(str)
    def timeout(self, msg):
        if msg == 'timeout':
            sock.send(f'point/{self.score}/{self.qList}'.encode())
            buttonEnd = QMessageBox.question(self, '시험종료', '시험이 종료되었습니다. 결과를 확인하세요.', QMessageBox.Yes)
            self.label.setText(f' {self.score}')
            self.label.setFont(QtGui.QFont("궁서", 72))
            self.score = 0
            self.loop = False

    # 리시브 쓰레드
class Recive(QThread):
    chat = pyqtSignal(str)
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
    # 메시지 받아서 어떻게 처리할 지
    def run(self):
        print('run start')
        self.conn = sqlite3.connect('studentDB')
        self.cursor = self.conn.cursor()
        while True:
            self.data = sock.recv(1024).decode()
            print('받은 메시지 :', self.data)
            print('타입 :', type(self.data))

            if 'qnaImfor' in self.data:
                self.parent.qnaData.clear()

                a = self.data.split('/')[:-1]
                print('a :', a)

                self.parent.qnaData.append([i for i in a if i != 'qnaImfor'])
                print('이거? :', self.parent.qnaData)

            elif 'update' in self.data:
                temp = eval(self.data)
                temp = temp[1:]
                lastNumber = int(self.parent.data[-1][0].split('.')[0])
                # newQuestion = (str(lastNumber + 1) + '. ' + temp).split('/')[1:]
                temp[0] = str(lastNumber + 1) + '. ' + temp[0]
                print('temp :', temp)
                print(len(temp))
                self.cursor.execute('insert into studentDB values(?, ?, ?, ?, ?, ?, ?)',
                (temp[0], temp[1], temp[2], temp[3], temp[4], temp[5], temp[6]))

                self.conn.commit()

            elif 'rating' in self.data:
                print('rating :', self.data)
                self.parent.label_4.setText(f'나의 포인트 : {self.data.split("/")[0]}')
                self.parent.label_4.setFont(QtGui.QFont("나눔고딕", 60))


            self.chat.emit(self.data)

    # Q&A창 새 윈도우로 보여주기
class SubWindow(QMainWindow, Recive, sub_form, QThread):
    request = pyqtSignal(str)
    def __init__(self, parent):
        super().__init__(parent)
        self.setupUi(self)
        self.parent = parent
        self.recive = Recive

        self.lineEdit.returnPressed.connect(self.add_QnA)
        self.pushButton_2.clicked.connect(self.add_QnA)
        self.pushButton.clicked.connect(self.qna_exit)
        self.back_Btn1.clicked.connect(self.qna_exit)
    # Q&A 조회하기
    def qnaInfo(self):
        self.textBrowser.clear()
        self.lineEdit.clear()
        if self.parent.qnaSignal == 'inquiry':
            try:
                self.label_4.setText('상세보기')
                userChoice_row = self.parent.userSelect_row
                self.label.setText(str(self.parent.tableWidget.item(userChoice_row, 0).text()))
                self.label_2.setText(str(self.parent.tableWidget.item(userChoice_row, 1).text()))
                self.label_3.setText(str(self.parent.tableWidget.item(userChoice_row, 2).text()))
                self.textBrowser.append(self.parent.tableWidget.item(userChoice_row, 3).text())
                self.stackedWidget.setCurrentIndex(0)
            except:
                pass
        else:
            self.label_4.setText('Q&A등록')
            self.stackedWidget.setCurrentIndex(1)

    # 새 Q&A 등록
    def add_QnA(self):
        addQnA_MessageBox = QMessageBox.question(self, 'Q&A 등록', 'Q&A를 등록하시겠습니까?',
                                           QMessageBox.Yes | QMessageBox.No)

        if addQnA_MessageBox == QMessageBox.Yes:
            Success_MessageBox = QMessageBox.question(self, 'Q&A 등록 성공', '등록이 완료되었습니다',
                                           QMessageBox.Yes)

            self.request.emit(str('qna/' + self.lineEdit.text()))
            self.request.emit('qna/X')

            self.parent.tableSetting()
            self.close()


    def qna_exit(self):
        self.close()

    # 타이머 클래스
class Timer(QThread):
    timeout = pyqtSignal(str)

    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.minute = 0
        self.second = 0
        self.loop = Timer
    # 시간 경과 시 시험 종료
    def run(self):
        while self.loop:
            self.second += 1
            time.sleep(1)
            self.parent.time_label.setText(f'경과 시간 : {self.minute}분 {self.second}초')
            if self.second == 60:
                self.minute += 1
                self.second = 0
            if self.minute == 10:
                self.minute, self.second = 0, 0
                self.parent.time_label.clear()
                self.parent.next_Btn.setEnabled(False)
                self.parent.result_Btn.show()

                self.loop = False
                self.timeout.emit('timeout')


if __name__ == '__main__':
    myNickName = '권택영'
    myTeacher = '류홍걸'
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((IP, PORT))
    App = QApplication(sys.argv)
    firstWindow = Login()
    firstWindow.show()
    App.exec_()