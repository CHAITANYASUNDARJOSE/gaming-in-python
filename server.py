from flask import Flask,render_template,request,redirect, url_for, make_response
from flask_socketio import SocketIO, send, emit
from functools import wraps
import random

import database

app = Flask(__name__)
app.config.from_object('config.Config')
socketio = SocketIO(app, cors_allowed_origins="*")

GAME_ID_SNAKE = 1
GAME_ID_CONNECT4 = 2

logged_in_users =[]

snakeUsers={}
snakeWaitingSid=[]
snakePartners={}

c4users = {}
c4WaitingSid = []
c4pairs = {}

# login required decorator
def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if request.cookies.get('email') != None:
            return f(*args, **kwargs)
        else:
            return redirect(url_for('Login', needLogin=True))
    return wrap

# App functionality
@app.route('/')
def Home():
    resp = make_response(render_template('login.html'))
    email = request.args.get('email')
    if email in logged_in_users:
        logged_in_users.remove(email)
    return resp        

@app.route('/register.html',methods = ['GET','POST'])
def Register():
    error = None
    if request.method=='POST':
        email=request.form['registerEmail']
        password=request.form['registerPassword']
        firstName = request.form['firstName']
        lastName = request.form['lastName']

        #Valid input check
        if(len(email) == 0):
            error = 'Email cannot be empty'
            return render_template('register.html', error = error)
        if (len(password) < 8):
            error = 'Password must be 8 characters long'
            return render_template('register.html', error = error)
        if (len(firstName) == 0):
            error = 'First Name cannot be empty'
            return render_template('register.html', error = error)

        #Valid input handling

        database.mysql_cursor.execute("select * from Login_Credentials where PlayerID = %s", (email,))
        data=database.mysql_cursor.fetchall()
        if(len(data) == 0):
            error = None
            database.mysql_cursor.execute("INSERT INTO Player_Profile(PlayerID,firstName,lastName) VALUES(%s,%s,%s)",(email,firstName,lastName))
            database.mysql_cursor.execute("INSERT INTO Login_Credentials VALUES(%s,MD5(%s))",(email,password))
            database.mysql_connection.commit()
            return redirect(url_for('Login'))
        else:
            error = 'Email already registered!'
    return render_template('register.html', error = error)

@app.route('/login.html', methods = ['GET', 'POST'])
def Login():
    error = None
    if request.method=='POST':

        email=request.form['loginEmail']
        password=request.form['loginPassword']

        database.mysql_cursor.execute("select md5(%s)",(password,))
        enc_string=database.mysql_cursor.fetchall()

        database.mysql_cursor.execute("select password from Login_Credentials where PlayerID = %s",(email,))
        stored=database.mysql_cursor.fetchall()
        if(len(stored) == 0):
            error = 'Email not found!'
        else:
            if(enc_string==stored):
                print("login email",email)
                logged_in_users.append(email)
                res = database.full_name(email)
                resp = make_response(redirect(url_for('Index')))
                resp.set_cookie('email',email)
                resp.set_cookie('fullName', res[0]) 
                return resp
            else:
                error = 'Invalid password'
    return render_template('login.html', error = error)

@app.route('/logout')
def Logout():
    resp = make_response(redirect(url_for('Login')))
    email = request.args.get('email')
    resp.set_cookie('email', expires=0)
    resp.set_cookie('fullName', expires=0)
    if email in logged_in_users:
        logged_in_users.remove(email)
    return resp

@app.route('/profile')
@login_required
def Profile():
    error = None
    email = request.cookies.get('email')

    if request.method=='POST':
        firstName = request.form['firstName']
        lastName = request.form['lastName']
    
        database.mysql_cursor.execute("update Player_Profile set firstName=%s, lastName=%s where PlayerID = %s",(firstName,lastName,email))
        database.mysql_connection.commit()
            
    
    database.mysql_cursor.execute("select * from Player_Profile where PlayerID = %s",(email,))
    values = database.mysql_cursor.fetchall()
     
    (user_email,firstName,lastName,cash,gold) = values[0]
    name = firstName+" "+lastName
    resp = make_response(render_template('profile.html', email=user_email, name=name, cash=cash, gold=gold))
    #reset the fullName cookie if it has been updated
    if name != request.cookies.get('fullName'):
        resp.set_cookie('fullName', name)
    return resp

@app.route('/leaderboard')
@login_required
def Leaderboard():
    
    database.mysql_cursor.execute("select @rank:=@rank+1 as _rank, firstName, lastName, Cash from Player_Profile p, (select @rank := 0) r order by Cash desc")
    values = database.mysql_cursor.fetchall()
    cash_leaderboard = [list(x) for x in values]
    
    database.mysql_cursor.execute("select @rank:=@rank+1 as _rank, firstName, lastName, Gold from Player_Profile p, (select @rank := 0) r order by Gold desc")
    values = database.mysql_cursor.fetchall()
    gold_leaderboard = [list(x) for x in values]
     
    return render_template('leaderboard.html',cash_leaderboard=cash_leaderboard, gold_leaderboard=gold_leaderboard)

@app.route('/history')
@login_required
def PlayerHistory():
    email = request.cookies.get('email')
    
    database.mysql_cursor.execute("select @rank:=@rank+1 as _rank, Cash, Gold from Player_History p, (select @rank := 0) r where PlayerID=%s and GameID=%s order by Cash desc",(email,GAME_ID_SNAKE))
    values = database.mysql_cursor.fetchall()
    snake_history = [list(x) for x in values]

    database.mysql_cursor.execute("select @rank:=@rank+1 as _rank, Cash, Gold from Player_History p, (select @rank := 0) r where PlayerID=%s and GameID=%s order by Cash desc",(email,GAME_ID_CONNECT4))
    values = database.mysql_cursor.fetchall()
    connect4_history = [list(x) for x in values]
     
    return render_template('playerHistory.html',snake_history=snake_history, connect4_history=connect4_history)

@app.route('/shop')
@login_required
def Shop():
    
    database.mysql_cursor.execute("select * from Perks_Available")
    values = database.mysql_cursor.fetchall()
    perks = [list(x) for x in values]
     
    return render_template('store.html', perks = perks)

@app.route('/index.html')
@login_required
def Index():
    email = request.cookies.get('email')
    return render_template('index.html', email=email)

@app.route('/miniGames.html')
@login_required
def MiniGames():
    email = request.cookies.get('email')
    fullName = request.cookies.get('fullName')
    return render_template('miniGames.html', email=email, fullName=fullName)

#######################################################################################################
@app.route('/waitingPage.html')
@login_required
def Waiting():

    email = request.cookies.get('email')
    game_id = int(request.args.get('game_id'))

    print("waiting room",email, game_id)

    database.mysql_cursor.execute("select GameID from Players_in_Game where GameID = %s", (game_id,))
    stored = database.mysql_cursor.fetchall()

    if(len(stored)%2==0):

        database.mysql_cursor.execute("select No_of_rooms from Mini_Game where GameID = %s", (game_id,))
        stored = database.mysql_cursor.fetchall()

        print("stored",stored)
        curr_rooms = stored[0][0]
        curr_rooms = curr_rooms + 1

        database.mysql_cursor.execute("update Mini_Game set No_of_rooms = %s where GameID = %s", (curr_rooms, game_id))
        database.mysql_cursor.execute("insert into Players_in_Game values(%s, %s, %s)", (email, game_id, curr_rooms))
        database.mysql_connection.commit()

        return render_template('waitingPage.html', email=email, game_id=game_id)

    else:

        database.mysql_cursor.execute("select No_of_rooms from Mini_Game where GameID = %s", (game_id,))
        stored = database.mysql_cursor.fetchall()
        curr_rooms = stored[0][0]
    
        database.mysql_cursor.execute("insert into Players_in_Game values(%s, %s, %s)", (email, game_id, curr_rooms))
        database.mysql_connection.commit()

        if game_id == GAME_ID_SNAKE:

            print("Snake waiting sid", snakeWaitingSid)

            snakePartners[email]=snakeWaitingSid[0]
            snakePartners[snakeWaitingSid[0]]=email
            
            return redirect(url_for('SAL'))

        elif game_id == GAME_ID_CONNECT4:
            c4pairs[email] = c4WaitingSid[0]
            c4pairs[c4WaitingSid[0]] = email 
            
            return redirect(url_for('Connect4'))

@app.route('/snakegame.html')
@login_required
def SAL():
    email = request.cookies.get('email')
    player2 = database.full_name(snakePartners[email])
    player1 = request.cookies.get("fullName")
    return render_template('snakegame.html', player1=player1, player2=player2)

@app.route('/connect4')
@login_required
def Connect4():
    email = request.cookies.get('email')
    paired_email = database.full_name(c4pairs[email])
    fullName = request.cookies.get("fullName")
    if email in c4WaitingSid:
        return render_template('connect4.html', fullName=fullName, email=email, paired_email=paired_email, color="red")
    else:
        return render_template('connect4.html', fullName=fullName,email=email, paired_email=paired_email, color="black")

# Socket IO functionality
@socketio.on('waiting_id', namespace='/private')
def receive_waiting_user(data):

    print(data)

    if int(data['game_id']) == GAME_ID_SNAKE:
        snakeWaitingSid.clear()
        snakeWaitingSid.append(data['player'])
        snakeWaitingSid.append(request.sid)

        print("rcv wid sid snake",snakeWaitingSid)

    elif int(data['game_id']) == GAME_ID_CONNECT4:
        c4WaitingSid.clear()
        c4WaitingSid.append(data['player'])
        c4WaitingSid.append(request.sid)


################################################################################################
@socketio.on('user_email', namespace='/private')
def receive_username(data):

    print("recieve usename", data)
    if int(data['game_id']) == GAME_ID_SNAKE:
        snakeUsers[data['player']] = request.sid
    elif int(data['game_id']) == GAME_ID_CONNECT4:
        c4users[data['player']] = request.sid

@socketio.on('redirectionSocket', namespace='/private')
def leave_waiting(arr):
    if int(arr['game_id']) == GAME_ID_SNAKE:
        emit('waitingHere',arr,room=snakeWaitingSid[1])
    elif int(arr['game_id']) == GAME_ID_CONNECT4:
        emit('waitingHere',arr,room=c4WaitingSid[1])

@socketio.on('moveSender', namespace='/private')
def send_move(arr):
    email = request.cookies.get('email')
    if(arr[0] == 'check2x'):
        arr.clear()

        database.mysql_cursor.execute("select Quantity from Owned_Perk where PlayerID = %s and PerkID = %s", (email,1))
        stored = database.mysql_cursor.fetchall()

        if(len(stored)==0 or stored[0][0]==0):
            arr.append('twoxFailed')
        else:
            newVal = stored[0][0] - 1
            database.mysql_cursor.execute("update Owned_Perk set Quantity=%s where PlayerID = %s and PerkID = %s", (newVal,email,1))
            database.mysql_connection.commit()
            arr.append('twoxPassed')
        emit('getMove',arr,room=snakeUsers[email])

    elif(arr[0] == 'checkHeadStart'):
        player1 = True
        if(arr[1]=='p2'):
            player1 = False

        arr.clear()
        arr.append(player1)
    
        database.mysql_cursor.execute("select Quantity from Owned_Perk where PlayerID = %s and PerkID = %s",(email,2))
        stored=database.mysql_cursor.fetchall()
        if(len(stored)==0 or stored[0][0]==0):
            arr.append('headStartFailed')
        else:
            newVal = stored[0][0] - 1
            print("newval",newVal)
            
            database.mysql_cursor.execute("update Owned_Perk set Quantity=%s where PlayerID =%s and PerkID = %s",(newVal,email,2))
            database.mysql_connection.commit()
            arr.append('headStartPassed')
            arr.append(random.randint(1,11))
        emit('getMove',arr,room=snakeUsers[email])
        emit('getMove',arr,room=snakeUsers[snakePartners[email]])
    else:
        email = request.cookies.get('email')
        print(email)
        partner = snakePartners[email]
        emit('getMove',arr,room=snakeUsers[partner])

@socketio.on('board', namespace='/private')
def running_game(data):
    if data == "twoXMultiplier":
        email = request.cookies.get('email')

        print(email)

        database.mysql_cursor.execute("select Quantity from Owned_Perk where PlayerID = %s and PerkID = %s",(email,1))
        stored=database.mysql_cursor.fetchall()
        if(len(stored)==0 or stored[0][0]==0):
            emit('game_state',"fail",room=c4users[email])
        else:
            newVal = stored[0][0] - 1
            print("newval",newVal)
            
            database.mysql_cursor.execute("update Owned_Perk set Quantity=%s where PlayerID = %s and PerkID = %s",(newVal,email,1))
            database.mysql_connection.commit()
            emit('game_state',"passed",room=c4users[email])
    else:
        email = data['user']
        paired_email = c4pairs[email]
        emit('game_state',data,room=c4users[paired_email])

@socketio.on('update_database', namespace='/private')
def update_db(arr):
    email = request.cookies.get('email')
    
    database.mysql_cursor.execute("select GameID,RoomID from Players_in_Game where PlayerID = %s",(email,))
    stored=database.mysql_cursor.fetchall()
    gameID = stored[0][0]
    roomID = stored[0][1]
    
    database.mysql_cursor.execute("insert into Player_History values (%s,%s,%s,%s,%s);",(email,gameID,roomID,arr[0],arr[1]))
    
    database.mysql_cursor.execute("delete from Players_in_Game where PlayerID = %s",(email,))
     
    database.mysql_cursor.execute("select Cash,Gold from Player_Profile where PlayerID = %s",(email,))
    stored = database.mysql_cursor.fetchall()
    cash = stored[0][0]
    gold = stored[0][1]
    cash += arr[0]
    gold += arr[1]
    
    database.mysql_cursor.execute("update Player_Profile set Cash=%s, Gold=%s where PlayerID=%s",(cash,gold,email))
    database.mysql_connection.commit()
     

@socketio.on('buyPerk', namespace='/private')
def buyPerk(arr):
    email = request.cookies.get('email')

    if(arr[0]=='getAvailableGold'):
        
        database.mysql_cursor.execute("select Gold from Player_Profile where PlayerID = %s",(email,))
        stored = database.mysql_cursor.fetchall()
        gold = stored[0][0]
        arr.clear()
        arr.append('goldAvailable')
        arr.append(gold)
        emit('perkResult',arr,room=request.sid)
    else:
        database.mysql_cursor.execute("select Quantity from Owned_Perk where PlayerID = %s and PerkID = %s",(email,arr[1]))
        stored=database.mysql_cursor.fetchall()
        if(len(stored) == 0):
            quantity = 1
            
            database.mysql_cursor.execute("insert into Owned_Perk values(%s,%s,%s)",(email,arr[1],quantity))
        else:
            quantity = stored[0][0]
            quantity = quantity + 1
            
            database.mysql_cursor.execute("update Owned_Perk set Quantity =%s where PlayerID = %s and PerkID = %s",(quantity,email,arr[1]))
        
        database.mysql_cursor.execute("update Player_Profile set Gold =%s where PlayerID = %s",(arr[2],email))
        database.mysql_connection.commit()

if __name__ == "__main__":

    socketio.run(app)