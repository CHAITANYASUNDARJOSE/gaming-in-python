import mysql.connector

mysql_connection = mysql.connector.connect(
    host="localhost",
    user="root",
    password="root",
    database="Game_server"
)

mysql_cursor = mysql_connection.cursor()

def full_name(email):

    mysql_cursor.execute("SELECT * FROM Player_Profile WHERE PlayerID = %s", (email,))
    return " ".join([str(x) for x in mysql_cursor.fetchone()])

def show_cash_board():

    mysql_cursor.execute("select @rank:=@rank+1 as rank, firstName, lastName, Cash from Player_Profile p, (select @rank := 0) r order by Cash desc;")
    return mysql_cursor.fetchall()

def gold_leaderboard():

    mysql_cursor.execute("select @rank:=@rank+1 as rank, firstName, lastName, Cash from Player_Profile p, (select @rank := 0) r order by Gold desc;")
    return mysql_cursor.fetchall()

def player_history(pid):

    mysql_cursor("select @rank:=@rank+1 as rank, Cash, Gold from Player_History p, (select @rank:=0) r where PlayerID=%s and GameID=1 order by Cash desc;", (pid,))
    return mysql_cursor.fetchall()

def c4_player_history(pid):

    mysql_cursor.execute("select @rank:=@rank+1 as rank, Cash, Gold from Player_History p, (select @rank:=0) r where PlayerID=%s and GameID=2 order by Cash desc;", (pid,))
    return mysql_cursor.fetchall()