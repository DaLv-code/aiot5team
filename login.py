import socket
import threading
import sqlite3
import sys
import time
from PyQt5.QtWidgets import *
from PyQt5 import QtCore
from PyQt5 import uic
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import QCoreApplication
import student
import teacher
import pymysql
import random
from PyQt5.QtCore import *

IP="127.0.0.1"
PORT=5150

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
            welcomMsg=f'[{logOK[1]} 선생님]\n로그인에 성공했습니다.'
            QMessageBox().information(self,"로그인 완료",welcomMsg)
            mainWindow = teacher.Teach_Win()
            mainWindow.show()
            self.deleteLater()
            sock.close()
        elif logOK[0]=='OK' and logOK[2]=='stu':
            welcomMsg=f'[{logOK[1]} 학생]\n로그인에 성공했습니다.'
            QMessageBox().information(self,"로그인 완료",welcomMsg)
            mainWindow = student.MainWindow()
            mainWindow.show()
            self.deleteLater()
            sock.close()
        elif logOK[0]=='NO':
            QMessageBox().information(self,"로그인 실패","아이디 혹은 비밀번호를 확인하세요.")

if __name__ == '__main__':
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((IP, PORT))
    App = QApplication(sys.argv)
    firstWindow = Login()
    firstWindow.show()
    App.exec_()