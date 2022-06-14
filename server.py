import socket
import threading
import sqlite3
import sys

PORT=5150
BUFSIZE = 1024
lock=threading.Lock()
clntList=[]
chatList=[]
clntCount=0
        
class handleClnt(threading.Thread):
    def __init__(self, clntSock):
        threading.Thread.__init__(self) 
        self.clntSock=clntSock
        self.openDB()      
    
    def openDB(self): # DB연결
        self.userDB=sqlite3.connect('userDB',check_same_thread=False)
        self.userCur=self.userDB.cursor()      

    def run(self):
        while True:
            firstQ=self.clntSock.recv(BUFSIZE).decode() # 연결된 클라이언트로부터 메세지 받기
            firstQ=firstQ.split('/')          
            if firstQ[0]=='login': #받은 메세지가 login일 경우 로그인으로 연결
                print(firstQ)
                self.login(firstQ) 
            elif firstQ[0]=='join': #받은 메세지가 join일 경우 회원가입으로 연결
                print(firstQ)
                self.join(firstQ) 
            elif firstQ[0]=='qna': #받은 메세지가 qna일 경우 QnA로 연결
                print(firstQ)
                self.QnA(firstQ)
            elif firstQ[0]=='chat': #받은 메세지가 chat일 경우 채팅으로 연결
                print(firstQ)
                self.chat(firstQ)
    
    def login(self,firstQ):
        self.userCur.execute('select userPw from user where userId = ?',(firstQ[1],))
        pwCheck=self.userCur.fetchone()
        if pwCheck!=None and pwCheck[0]==firstQ[2]: 
            print('로그인 성공')        
            self.userCur.execute('select userName, userType from user where userPw = ?',(firstQ[2],))
            nameType=self.userCur.fetchone() 

            # 로그인에 성공한 유저의 [소켓, 유저이름, 유저타입(선생,학생)]을 전역리스트 clntList에 추가
            self.indexNum=clntList.index([self.clntSock])
            clntList[self.indexNum]=[self.clntSock,nameType[0],nameType[1]]            
            print(clntList)

            logImfo='/'.join(nameType)     
            logImfo='OK/'+logImfo
            print(logImfo)
            self.clntSock.sendall(logImfo.encode()) # OK메세지와 함께 로그인에 성공한 이름과 타입을 보내줌    

        else:
            print('로그인 실패')      
            self.clntSock.sendall('NO'.encode()) # 로그인 실패시 NO메세지를 전송함     

    def join(self,firstQ):     
        self.userCur.execute('select userId from user where userId = ?',(firstQ[1],))
        if self.userCur.fetchone()==None: #ID가 DB에 없을 때(중복확인)
            self.clntSock.sendall('OK'.encode())
            joinMsg=self.clntSock.recv(BUFSIZE).decode().split('/')
            print(f'회원가입 정보: {joinMsg}')
            quary='insert into user values (?, ?, ?, ?)'
            self.userCur.execute(quary,(joinMsg[0],joinMsg[1],joinMsg[2],joinMsg[3])) # 유저로부터 받은 정보를 통해 회원정보 업데이트
            self.userDB.commit()
        else: #ID가 DB에 있을 때(중복됬을시)
            self.clntSock.sendall('NO'.encode())
            print('실패')

    def QnA(self,firstQ):
        qnaMsg=''        
        self.userCur.execute('select * from qna')
        qnaDBimfor=self.userCur.fetchall()   
        for qnaImfor in qnaDBimfor:
            qnaMsg=qnaMsg+'/'.join(qnaImfor)+'/qnaImfor/'            
        print(qnaMsg)
        self.clntSock.sendall(qnaMsg.encode()) # Qna게시판에 저장된 내용을 전부 유저에게 보냄

        if firstQ[1]!='X': #수정하고 싶은 메세지가 있을때 
            if clntList[self.indexNum][2]=='stu': #학생일때
                print(clntList[self.indexNum][1])
                print(firstQ[1])
                query='insert into qna values(?,?,?,?,?)'
                self.userCur.execute(query,(clntList[self.indexNum][1],'X','X',firstQ[1],'X'))    
                self.userDB.commit()
            elif clntList[self.indexNum][2]=='tea': #선생일때
                query='UPDATE qna SET answerOK=?, teacherName=?, answer=? where studentName = ?'
                self.userCur.execute(query,('O',clntList[self.indexNum][1],firstQ[1],firstQ[2]))  
                self.userDB.commit()

    def chat(self,firstQ):
        if clntList[self.indexNum][2]=='stu': #학생일때
            chatName='['+clntList[self.indexNum][1]+' 학생]'
        elif clntList[self.indexNum][2]=='tea': #선생일때
            chatName='['+clntList[self.indexNum][1]+' 선생님]'
        chatList.append(self.clntSock)
        while True:
            chatMsg=self.clntSock.recv(BUFSIZE).decode()
            if not chatMsg:
                break
            chatMsg=chatName+chatMsg
            for chatUser in chatList:
                if chatUser != self.clntSock: # 자기 자신을 제외한 모두에게 전송
                    chatUser.sendall(chatMsg.encode()) 

        


if __name__ == '__main__':
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('', PORT))
    sock.listen(5)

    while True:      
        clntSock, addr = sock.accept() 

        lock.acquire()
        clntList.append([clntSock])
        lock.release()

        servThread = handleClnt(clntSock) # 유저 접속시 마다 쓰레드 생성
        servThread.start()