import socket
import threading
import sqlite3
import sys

PORT=5142
BUFSIZE = 1024
lock=threading.Lock()
clntList=[]
chatList=[]
clntCount=0
student_sock = []
        
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
            if not bool(firstQ):
                break
            print(f'클라이언트 메세지:{firstQ}')
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
            elif firstQ[0]=='point': #받은 메세지가 point일 경우 점수관리로 연결
                print(firstQ)
                self.point(firstQ)   
            elif firstQ[0]=='update': #받은 메세지가 update일 경우 문제추가로 연결
                print(firstQ)
                self.update(firstQ)
            elif firstQ[0]=='rating': #받은 메세지가 rating일 경우 점수 및 등급으로 연결
                print(firstQ)
                self.rating(firstQ)
            
    
    def login(self,firstQ):
        self.userCur.execute('select userPw from user where userId = ?',(firstQ[1],))
        pwCheck=self.userCur.fetchone()
        if pwCheck!=None and pwCheck[0]==firstQ[2] : 
            print('로그인 성공')      
            self.indexNum=clntList.index([self.clntSock])                                      
            # 로그인에 성공한 유저의 [소켓, 유저이름, 유저타입(선생,학생)]을 전역리스트 clntList에 추가                
            self.userCur.execute('select userName, userType from user where userPw = ?',(firstQ[2],))
            nameType=self.userCur.fetchone() 
            clntList[self.indexNum]=[self.clntSock,nameType[0],nameType[1]] 
            logImfo='/'.join(nameType)     
            logImfo='OK/'+logImfo
            print(logImfo)
            self.clntSock.sendall(logImfo.encode()) # OK메세지와 함께 로그인에 성공한 이름과 타입을 보내줌  
            

        else:
            print('로그인 실패')      
            self.clntSock.sendall('NO/'.encode()) # 로그인 실패시 NO메세지를 전송함     

    def join(self,firstQ):     
        self.userCur.execute('select userId from user where userId = ?',(firstQ[1],))
        if self.userCur.fetchone()==None: #ID가 DB에 없을 때(중복확인)
            self.clntSock.sendall('OK'.encode())
            joinMsg=self.clntSock.recv(BUFSIZE).decode().split('/')
            print(f'회원가입 정보: {joinMsg}')
            quary='insert into user values (?, ?, ?, ?, ?)'
            self.userCur.execute(quary,(joinMsg[0],joinMsg[1],joinMsg[2],joinMsg[3],0)) # 유저로부터 받은 정보를 통해 회원정보 업데이트
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
        if self.clntSock not in chatList:
            chatList.append(self.clntSock)       
        print(f'여기{chatList}')
        for chatUser in chatList:
            if chatUser != self.clntSock: # 자기 자신을 제외한 모두에게 전송
                chatUser.sendall(firstQ[1].encode()) 

    #학생클라이언트 문제 풀이 정보 서버 디비에 저장
    def point(self,firstQ):
        pointImfor=''
        if clntList[self.indexNum][2]=='stu': #학생일때
            studentName=clntList[self.indexNum][1]
            self.userCur.execute('INSERT INTO point VALUES(?,?,?)', (studentName,firstQ[1],firstQ[2]))
            self.userCur.execute('UPDATE user SET userPoint = userPoint+? where userName=?', (int(firstQ[1])*10,clntList[self.indexNum][1]))             
            self.userDB.commit()
    #디비에 저장된 학생 문제풀이 정보를 선생님에게 전송
        elif clntList[self.indexNum][2]=='tea': #선생일때
            self.userCur.execute("SELECT * FROM point")
            sdPoint = self.userCur.fetchall() # fetchall는 레코드를 배영형식으로 저장(정렬)
            for show in sdPoint:
                pointImfor=pointImfor+'/'.join(show)+'/score/'
                print(pointImfor)
            self.clntSock.sendall(pointImfor.encode()) # 클라이언트에 전송      

    def update(self,firstQ):
        updateImfor=''
        if clntList[self.indexNum][2]=='stu': #학생일때
            self.userCur.execute('SELECT * FROM updateQ')          
            updateList = self.userCur.fetchall() # fetchall는 레코드를 배영형식으로 저장(정렬)
            for updateQ in updateList:
                updateImfor=updateImfor+'/'.join(updateQ)+'/update/'
                print(updateImfor)
            self.clntSock.sendall(updateImfor.encode()) # 클라이언트에 전송      

        elif clntList[self.indexNum][2]=='tea': #선생일때
            self.userCur.execute('INSERT INTO updateQ VALUES(?,?,?,?,?,?,?)',(firstQ[1],firstQ[2],firstQ[3],firstQ[4],firstQ[5],firstQ[6],firstQ[7]))
            for i in student_sock:
                i.sendall(str(firstQ).encode())
            print('aaaa :', str(firstQ))
            self.userDB.commit()

    def rating(self,firtsQ): # 학생 문제 풀이 등급 저장
        self.userCur.execute("SELECT userPoint FROM user where userName= ?",(clntList[self.indexNum][1],))        
        ratingQ = self.userCur.fetchone()
        ratingImfo = ratingQ[0]+'/rating' 
        self.clntSock.sendall(ratingImfo.encode())


if __name__ == '__main__':
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('', PORT))
    sock.listen(5)

    while True:      
        clntSock, addr = sock.accept()
        student_sock.append(clntSock)

        lock.acquire()
        clntList.append([clntSock])
        lock.release()

        servThread = handleClnt(clntSock) # 유저 접속시 마다 쓰레드 생성
        servThread.start()