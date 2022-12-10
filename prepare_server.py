import mysql.connector

host_args = {
    "host": "localhost",
    "user": "root",
    "password": "root",
    "database": "Game_server"
}

con = mysql.connector.connect(**host_args)

cur = con.cursor(dictionary=True)

with open('db_config.sql', 'r') as sql_file:
    result_iterator = cur.execute(sql_file.read(), multi=True)
    for res in result_iterator:
        print("Running query: ", res)  # Will print out a short representation of the query
        print(f"Affected {res.rowcount} rows" )

    con.commit()