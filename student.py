import pymysql
import sys
import random
import time
import socket
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5 import uic

PORT=5150
main_form = uic.loadUiType("student.ui")[0]
sub_form = uic.loadUiType("student_sub.ui")[0]


class MainWindow(QMainWindow, main_form):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.th_recive = Recive(self)
        self.th_recive.chat.connect(self.reciveMsg)
        self.th_recive.start()
        self.th_timer = Timer(self)
        self.th_timer.timeout.connect(self.timeout)
        self.th_subWindow = SubWindow(self)
        self.th_subWindow.request.connect(self.request)

        self.score = 0
        self.nickName = 'chounkal'
        self.teacher = '류홍걸'
        self.data = []
        self.qnaData = []
        self.question = []
        self.radioBtn_list = []

        self.learning_Btn.clicked.connect(self.learningPage)
        self.test_Btn.clicked.connect(self.testPage)
        self.back_Btn1.clicked.connect(self.mainPage)
        self.back_Btn2.clicked.connect(self.mainPage)
        self.pushButton_2.clicked.connect(self.mainPage)
        self.pushButton_3.clicked.connect(self.mainPage)
        self.pushButton_5.clicked.connect(self.mainPage)
        self.result_Btn.clicked.connect(self.resultPage)
        self.qna_Btn.clicked.connect(self.qnaPage)
        self.chatpage_Btn.clicked.connect(self.chatPage)
        self.search_lineEdit.returnPressed.connect(self.searcheQuestion)
        self.chat_lineEdit.returnPressed.connect(self.sendMsg)
        self.next_Btn.clicked.connect(lambda: self.testStart('next'))
        self.tableWidget.cellClicked.connect(lambda: self.tableClick_signal('inquiry'))
        self.newQnA_Btn.clicked.connect(lambda: self.tableClick_signal('QnA'))

        self.result_Btn.hide()
        self.bringData()

        recommended_words = []
        for i in self.question:
            if self.search_lineEdit.text() in i:
                recommended_words.append(i)

        completer = QCompleter(recommended_words)
        self.search_lineEdit.setCompleter(completer)


    def tableSetting(self):
        time.sleep(0.1)
        self.tableWidget.clear()
        self.title = ['작성자', '답변여부', '담당자', '질문']
        self.tableWidget.setRowCount(len(self.qnaData))
        self.tableWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tableWidget.setHorizontalHeaderLabels(self.title)
        print('aaaaa', self.qnaData)

        row = 0
        for i in self.qnaData:
            col = 0
            for j in i:
                self.tableWidget.setItem(row, col, QTableWidgetItem(j))
                self.tableWidget.item(row, col).setTextAlignment(Qt.AlignCenter)
                col += 1
            row += 1


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


    def randomNumberSet(self):
        self.questionIndex = []

        for i in range(len(self.data)):
            self.questionIndex.append(i)

        random.shuffle(self.questionIndex)


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


    def chatPage(self):
        self.stack.setCurrentWidget(self.chat_Page)


    def sendMsg(self):
        self.msg = self.chat_lineEdit.text()
        self.th_recive.sock.send(self.msg.encode())
        self.chat_textBrowser.append(f'나 : {self.msg}')
        print('보낸 메시지 :', self.msg)
        self.chat_lineEdit.clear()


    def qnaPage(self):
        self.qnaSignal = ''
        self.request('qna/X')
        self.tableSetting()
        self.stack.setCurrentWidget(self.qna_Page)


    def resultPage(self):
        self.randomNumberSet()
        self.lcdNumber.display(self.score)
        self.result_Btn.hide()
        self.next_Btn.setEnabled(True)
        self.back_Btn2.setEnabled(True)
        self.stack.setCurrentWidget(self.result_page)


    def testStart(self, testSignal):
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


    def grading(self):
        # self.wrong_temp
        for i, j in zip(self.question_BtnList, self.wrong_temp):
            for idx, v in enumerate(i[:]):
                self.result_textBrowser.append(j)
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
            else:
                self.wrongQuestion_list.append(j[2])
        print('틀린 문제 :', self.wrongQuestion_list)
        for i in self.wrongQuestion_list:
            self.th_recive.sock.send(i.encode())
        print('점수 :', self.score)


    def searcheQuestion(self):
        self.answer_textBrowser.clear()
        self.text = self.search_lineEdit.text()
        for i in self.data:
            if self.text in i:
                self.answerFind(i, self.answer_textBrowser.append)


    def learningPage(self):
        self.info_textBrowser.clear()
        self.stack.setCurrentWidget(self.learning_page)

        for i in self.data:
            self.answerFind(i, self.info_textBrowser.append)


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


    def bringData(self):
        connection = pymysql.connect(host='localhost', port=3306, user='root',
                                     password='1234', db='project', charset='utf8')
        cursor = connection.cursor()
        sql = 'SELECT * FROM 필기시험'
        cursor.execute(sql)
        result = cursor.fetchall()

        for res in result:
            self.data.append(list(res))
            self.question.append(res[0])
        connection.close()


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


    def mainPage(self):
        self.randomNumberSet()
        self.result_Btn.hide()
        self.next_Btn.setEnabled(True)
        self.stack.setCurrentWidget(self.main_page)

    @pyqtSlot(str)
    def request(self, request):
        self.th_recive.sock.send(request.encode())
        print('보낸 요청 :', request)


    @pyqtSlot(str)
    def reciveMsg(self, msg):
        self.chat_textBrowser.append(f'상대방 : {msg}')


    @pyqtSlot(str)
    def timeout(self, msg):
        if msg == 'timeout':
            self.th_recive.sock.send(f'{self.score}/point'.encode())
            buttonEnd = QMessageBox.question(self, '시험종료', '시험이 종료되었습니다. 결과를 확인하세요.', QMessageBox.Yes)
            self.th_recive.sock.send(f'점수 : {self.score}'.encode())
            self.score = 0
            self.loop = False


class Recive(QThread):
    chat = pyqtSignal(str)

    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.sock = socket.socket()
        self.sock.connect(('localhost', PORT))

    def run(self):
        while True:
            self.data = self.sock.recv(1024).decode()
            print('받은 메시지 :', self.data)
            if self.data.split('/')[-1] == 'qnaImfor':
                print(self.data.split('/')[:-2])
            elif 'qnaImfo' in self.data:
                self.parent.qnaData.clear()
                self.parent.qnaData.append(self.data.split('/')[:-1])
                # print(print('질문데이터 :', self.qnaData))
                print('가공 메시지 :', self.parent.qnaData)

            self.chat.emit(self.data)


    # ↓ Q&A 페이지 클래스
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

    def qnaInfo(self):
        self.textBrowser.clear()
        self.lineEdit.clear()
        if self.parent.qnaSignal == 'inquiry':
            self.label_4.setText('상세보기')
            userChoice_row = self.parent.userSelect_row
            self.label.setText(f'질문자 : {self.parent.tableWidget.item(userChoice_row, 0).text()}')
            self.label_2.setText(f'답변여부 : {self.parent.tableWidget.item(userChoice_row, 1).text()}')
            self.label_3.setText(f'담당교수 : {self.parent.tableWidget.item(userChoice_row, 2).text()}')
            self.textBrowser.append(self.parent.tableWidget.item(userChoice_row, 3).text())
            self.stackedWidget.setCurrentIndex(0)
        else:
            self.label_4.setText('Q&A등록')
            self.stackedWidget.setCurrentIndex(1)


    def add_QnA(self):
        addQnA_MessageBox = QMessageBox.question(self, 'Q&A 등록', 'Q&A를 등록하시겠습니까?',
                                           QMessageBox.Yes | QMessageBox.No)

        if addQnA_MessageBox == QMessageBox.Yes:
            Success_MessageBox = QMessageBox.question(self, 'Q&A 등록 성공', '등록이 완료되었습니다',
                                           QMessageBox.Yes)

            self.request.emit(str('qna/' + self.label.text() + '/' + 'X' + '/' + self.label_3.text() + '/' + self.lineEdit.text()))
            print('추가한 정보 : ', str('qna/' + self.label.text() + '/' + 'X' + '/' + self.label_3.text() + '/' + self.lineEdit.text()))
            self.request.emit('qna/X')

            self.parent.tableSetting()
            self.close()


    def qna_exit(self):
        self.close()


class Timer(QThread):
    timeout = pyqtSignal(str)

    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.minute = 0
        self.second = 0
        self.loop = Timer

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

                self.timeout.emit('timeout')
                self.loop = False