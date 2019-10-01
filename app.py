
from flask import Flask
from flask import request
from flask import render_template
from flask import jsonify
from random import randint
from pymongo import MongoClient
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import pymongo
import random
import string
import json
import random
import datetime
import os
import sys
import smtplib

# Global Vars.
EMAIL_RECIPIENT = "josueisonfire@gmail.com"


app = Flask(__name__)


client = MongoClient()
db = client['test_database']
collection = db['users']

# ROUTES:  *****************************************************************

@app.route("/")
def hello():
    return "Hello, Flask!"


@app.route('/ttt', methods=['POST'])
def return_game_form():
    # if user is logged in, dynamically fill the welcome data into the page.

    # else
    #print('POST REQUEST: %s' %str(os.getcwd()), file=sys.stderr)
    if request.form.get('name') != None:
        name = request.form.get('name')
        date = datetime.datetime.today()
        return render_template('sample.html', name=name, date=date)
    else:
        return "Erroneous Request."

@app.route('/ttt', methods=['GET'])
def init_form():
    #print('Accessed INIT_FORM', file=sys.stderr)
    return render_template('login_page.html')
req_count = 0

@app.route('/ttt/play', methods=['POST'])
def play():
    
    # check if user is signed in...
        # if signed in, prompt user to logged 
            #  if there is an ongoing game, load. <maybe ask the user if he wants to continue.>
            #  add functionality in which a finished game is saved automatically, and resets a game if the player wishes.
            #  scores and games should be saved automatically and dynamically.
            #  if session is in progress, check if the post method is giving the following args: 'grid', and 'move' properties. if move == null, return grid as is.

        # if not, prompt user to sample.html, the guest tictactoe page.
    # obtain cookie data
    session = request.cookies.get('SID')
    res = check_session(session)
    # get data
    received_data = request.get_data()
    data = json.loads(received_data)
    rgrid = data["grid"]
    move = data["move"]
    user_data = collection.find_one({"key":request.cookies.get('SID')})
    # 
    if (rgrid == None or rgrid == '') and (move == None or move == ''):
        return json.dumps({"status":"ERROR", "msg":"invalid parameters"})
    if move == None or move =='':
        # No move was specified. Returns the gris as it was.
        return jsonify(status='OK', grid=rgrid, winner=' ')

    # there is an active session
    if res == 0:
        # check for resets.
        if move == 'r':
            
            # reset curr_game field.
            
            #  reset user board.
            reset_curr_game_board(user_data)
            return jsonify(status='OK', grid=[' ',' ',' ',' ',' ',' ',' ',' ',' '],winner=' ')
        
        # if move == null or ''
        if rgrid == None or rgrid == '':
            # retrieve board.
            grd = get_curr_board_grid(user_data)
            # if grid is empty, make a new game
            if grd == '':
                # make new game
                make_new_game(user_data, op_type='init')
                return jsonify(status='OK', grid=get_curr_board_grid(user_data), winner=' ')
            # update current board.
            else:
                # update move...
                write_to_grid(user_data, move, 'X')
                winner = check_victory(get_curr_board_grid(user_data)) 
                # check for victory
                if winner == 'TIE':
                    # do what ties do
                    ugrid = get_curr_board_grid(user_data)
                    make_new_game(user_data)
                    update_scoreboard(user_data, 'tie')
                    return jsonify(status='OK', grid=ugrid, winner='TIE')
                elif winner == 'X':
                    # do what
                    ugrid = get_curr_board_grid(user_data)
                    make_new_game(user_data)
                    update_scoreboard(user_data, 'X')
                    return jsonify(status='OK', grid=ugrid, winner='X')
                elif winner == 'O':
                    ugrid = get_curr_board_grid(user_data)
                    make_new_game(user_data)
                    update_scoreboard(user_data, 'O')
                    return jsonify(status='OK', grid=ugrid, winner='O')
                # else, make an AI move.
                hal9000_destroy_humanity(user_data)
                # check for victories, again.
                winner = check_victory(get_curr_board_grid(user_data)) 
                if winner == 'TIE':
                    # do what ties do
                    ugrid = get_curr_board_grid(user_data)
                    make_new_game(user_data)
                    update_scoreboard(user_data, 'tie')
                    return jsonify(status='OK', grid=ugrid, winner='TIE')
                elif winner == 'X':
                    # do what
                    ugrid = get_curr_board_grid(user_data)
                    make_new_game(user_data)
                    update_scoreboard(user_data, 'X')
                    return jsonify(status='OK', grid=ugrid, winner='X')
                elif winner == 'O':
                    ugrid = get_curr_board_grid(user_data)
                    make_new_game(user_data)
                    update_scoreboard(user_data, 'O')
                    return jsonify(status='OK', grid=ugrid, winner='O')
                else:
                    # no winners detected, just return the updated grid.
                    return jsonify(status='OK', grid=get_curr_board_grid(user_data), winner=' ')
        # Do the fancy stuffs.

    else:
        # check for reset.
        if move == 'r':
            # reset all vals.
            return jsonify(grid=[' ',' ',' ',' ',' ',' ',' ',' ',' '],winner=' ')
        # update player move.
        code = update_player_move(rgrid, move)

        if code == None:
            # invalid player move. Returns the grid as is.
            jsonify(grid=rgrid,winner=' ')
        else:
            rgrid = code

        # each move only needs grid property.
        rwinner = check_victory(rgrid)
        if rwinner == 'TIE':
            return jsonify(
                grid=rgrid,
                winner='TIE'
            )
        elif rwinner == 'X':
            return jsonify(
                grid=rgrid,
                winner='X'
            )
        else:
            rgrid = play_ttt(grid=rgrid)
        rwinner = check_victory(rgrid)
        
        global req_count
        req_count = req_count + 1
        return jsonify(
            grid=rgrid,
            winner=rwinner
        )

# ****************************************************************** N E W   F U N C T I O N S ***********************************************************
error = ''
@app.route('/adduser', methods=['POST'])
def adduser():
    # try:
    if request.method == 'POST':
        # received_data = request.get_data()
        # obj = json.loads(received_data)
        n_username = request.form.get('username')
        n_email = request.form.get('email')
        n_password = request.form.get('password')
        #print('obtained POST requests to route /adduser with values of: n_username: %s, n_email: %s, and n_password: %s' %(n_username, n_email, n_password), file=sys.stderr)
        res = None
        if (n_username != None) and (n_email != None) and (n_password != None):
            res = make_new_user(n_username, n_email, n_password)
        else:
            return json.dumps({"status":"ERROR", "msg":"Invalid parameters provided. Please provide valid parameters..."})
        return res
    # except Exception as e:
    #     #flash(e)
    #     return json.dumps({"status":"ERROR", "msg":"unexpected error occurred."})

@app.route('/verify', methods=['POST'])
def verify():
    try:
        if request.method == 'POST':
            attempted_email = request.form.get('email')
            attempted_key = request.form.get('key')
            if (attempted_email != None) and (attempted_key != None):
                res = verify_and_update(attempted_email,attempted_key)
                return res
            else:
                return json.dumps({"status":"ERROR", "msg":"Invalid parameters provided. Please provide valid parameters..."})
    except Exception as e:
        #flash(e)
        return json.dumps({"status":"ERROR", "msg":"unexpected error occurred."})

# OPTIONAL
@app.route('/verify', methods=['GET'])
def verfy_get():
    return json.dumps({"status":"ERROR; unsupported method"})


@app.route('/login', methods=['GET'])
def give_login():
    return render_template('login_page.html')

# if logged in, redirect to play page
@app.route('/login', methods=['POST'])
def login():
    res = check_session(request.cookies.get('SID'))
    if res == 0:
        # error, since the user is already logged in.
        return json.dumps({"status":"ERROR", "msg":"User already logged in. invalid operation. Please log out before attempting to log in."})
    try:
        if request.method == 'POST':
            attempted_username = request.form.get('username')
            attempted_password = request.form.get('password')
            if (attempted_password != None) and (attempted_username != None):
                data = collection.find_one({"username":attempted_username})
                if data == None:
                    return json.dumps({"status":"ERROR", "body":"Invalid Username or Wrong Password... Please try again..."})
                elif data["password"] == attempted_password:
                    # initiate session...
                    # If the cookie has not been set...
                    if not request.cookies.get('SID'):
                        res = app.make_response(json.dumps({"status":"OK", "msg":"created new cookie"}))
                        res.set_cookie('SID', data["key"], 3600)
                        return res
                    else:
                        res = app.make_response(json.dumps({"status":"OK", "msg":"User already signed in..."}))
                        return 
                else:
                    return json.dumps({"status":"ERROR", "body":"Invalid Username or Wrong Password... Please try again..."})
            else:
                return json.dumps({"status":"ERROR", "msg":"INVALID PARAMETERS."})

    except Exception as e:
        #flash(e)
        return json.dumps({"status":"ERROR", "msg": "Something went terribly wrong..."})

# ***!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! Methods that require an active cookie to work.

@app.route('/logout')
def logout():
    # if no session, return error.
    session = request.cookies.get('SID')
    res = check_session(session)
    if res == 0:
        # do normal checkout
        data = get_user_from_key(session)
        # change key value...
        collection.update_one({"_id":data["_id"]},{"$set": {"key":make_random_string(512, 512)}})
        res = app.make_response(json.dumps({"status":"OK", "msg":"User logged out..."}))
        # delete cookie
        res.set_cookie('SID', '', 0)
        return res
    else:
        # error has occurred.
        return res

# return the list of all games played by a player:
@app.route('/listgames', methods=['POST'])
def listgames():
    # check session.
    res = check_session(request.cookies.get('SID'))
    if res != 0:
        # error. No user signed in or invalid path.
        return res
    else:
        user = get_user_from_key(request.cookies.get('SID'))
        msg = get_all_games(user, 'json')['status']='OK'
        return json.dumps(msg)

@app.route('/getgame', methods=['POST'])
def getgame():
    # check params
    req_id = request.form.get('id')
    if id == None:
        return json.dumps({'status':'ERROR', 'msg':'INVALID PARAMETERS'})
    # check session.
    res = check_session(request.cookies.get('SID'))
    if res != 0:
        # error. No user signed in or invalid path.
        return res
    else:
        user = get_user_from_key(request.cookies.get('SID'))
        msg = get_all_games(user, 'dict')
        for game in msg:
            if game['id'] == req_id:
                game['status'] = 'OK'
                return json.dumps(game)
        return json.dumps({'status':'ERROR', 'msg':'GAME NOT FOUND'})

@app.route('/getscore', methods=['POST'])
def getscore():
    # check session.
    res = check_session(request.cookies.get('SID'))
    if res != 0:
        # error. No user signed in or invalid path.
        return res
    else:
        msg = collection.find_one({"key":request.cookies.get('SID')}["scoreboard"])['status']='OK'
        return json.dumps(msg)

"""
try:
        if request.method == 'POST':

    except Exception as e:
        #flash(e)
        return json.dumps({"status":"ERROR"})
"""

# Helper functions...

def reset_curr_game_board(user):
    n_of_games = len(get_all_games(user,'dict')) + 1
    curr_game = {'id':n_of_games, 'start_date':datetime.datetime.now(), 'grid':[' ',' ',' ',' ',' ',' ',' ',' ',' '], 'winner':''}
    collection.find_and_modify({'_id':user['_id']}, {"$set": {"curr_game":curr_game}})
    return 0

# get grid of a user.
def get_curr_board_grid(user):
    curr_g = user['curr_game']
    return curr_g['grid']

# !!! M U S T  have grid initialized prior to inspection.
# write to a particular slot in a grid with specified char value.
def write_to_grid(user, inDeX, char):
    curr_game = user['curr_game']
    if curr_game != None:
        if curr_game['grid'][inDeX] == ' ':
            curr_game['grid'][inDeX] = char
            collection.find_and_modify({'_id':user['_id']}, {"$set": {"curr_game":curr_game}})
            return 0
        else:
            return 1
    else:
        return 1

# function to make a new game.
def make_new_game(user, op_type='def'):
    if op_type == 'init':
        # used if the curr_game field is null.
        reset_curr_game_board(user)
    elif op_type == 'def':
        # used if the curr_game has finished a game.
        # save current game to list of games.
        p_game = user['curr_game']
        glist = user['games']
        glist.append(p_game)
        reset_curr_game_board(user)
        collection.find_and_modify({'_id':user['_id']}, {"$set": {"games":glist}})
    else:
        # error
        return 1

def update_scoreboard(user, update):
    scoreboard = collection.find_one({"_id":user['_id']})
    if update == 'O':
        # computer won
        scoreboard['wopr'] = scoreboard['wopr'] + 1
    elif update == 'X':
        scoreboard['human'] = scoreboard['human'] + 1
    elif update == 'tie' or update == 'TIE':
        scoreboard['tie'] = scoreboard['tie'] + 1
    else:
        return 1
    collection.find_and_modify({'_id':user['_id']}, {"$set": {"scoreboard":scoreboard}})
    return 0
# TODO: UPDATE to recieve session users.


def hal9000_destroy_humanity(user):
    # retrieve curr game grid.
    write_to_grid(user, get_ai_move(get_curr_board_grid(user)), "O")
    

def get_ai_move(grid):
    move = None
    filled = True
    for cell in grid:
        if cell == ' ':
            filled = False

    while(filled == False):
        ran = random.randint(0,8)
        if grid[ran] == ' ':
            move = ran
            filled = True
    return move


def play_ttt(grid=[' ',' ',' ',' ',' ',' ',' ',' ',' ']):
    
    filled = True
    for cell in grid:
        if cell == ' ':
            filled = False

    while(filled == False):
        ran = random.randint(0,8)
        if grid[ran] == ' ':
            grid[ran] = 'O'
            filled = True
    return grid

# update player move on the grid. If the move is unvalid, however, it will return an error. The server will simply return the gris as it was.
def update_player_move(grid, move):
    if grid[move] == ' ':
        grid[move] = 'X'
        return grid
    else:
        return None

def check_victory(grid):

    if (grid[0] == grid[1]) and (grid[0] == grid[2]) and (grid[0] != ' '):
        #print('Player: %s has won in series 0-1-2' %grid[0], file=sys.stderr)
        return grid[0]

    elif (grid[3] == grid[4]) and (grid[3] == grid[5]) and (grid[3] != ' '):
        #print('Player: %s has won in series 3-4-5' %grid[3], file=sys.stderr)
        return grid[3]
    
    elif (grid[6] == grid[7]) and (grid[6] == grid[8]) and (grid[6] != ' '):
        #print('Player: %s has won in series 6-7-8' %grid[6], file=sys.stderr)
        return grid[6]
   
    elif (grid[0] == grid[3]) and (grid[0] == grid[6]) and (grid[0] != ' '):
        #print('Player: %s has won in series 0-3-6' %grid[3], file=sys.stderr)
        return grid[0]
    
    elif (grid[1] == grid[4]) and (grid[1] == grid[7]) and (grid[1] != ' '):
        #print('Player: %s has won in series 1-4-7' %grid[1], file=sys.stderr)
        return grid[1]
    
    elif (grid[2] == grid[5]) and (grid[2] == grid[8]) and (grid[2] != ' '):
        #print('Player: %s has won in series 2-5-8' %grid[2], file=sys.stderr)
        return grid[2]
    
    elif (grid[0] == grid[4]) and (grid[0] == grid[8]) and (grid[0] != ' '):
        #print('Player: %s has won in series 0-4-8' %grid[0], file=sys.stderr)
        return grid[4]
    
    elif (grid[2] == grid[4]) and (grid[2] == grid[6]) and (grid[2] != ' '):
        #print('Player: %s has won in series 2-4-6' %grid[2], file=sys.stderr)
        return grid[2]
    else:
        full = True
        for cell in grid:
            
            if cell == ' ':
                full = False
        if full:
            return 'TIE'
        return ' '




# Checks session in progress. If a session exists, returns 0, if not returns a json string with the error desc.
def check_session(cookie):
    if not cookie:
        #  No cookies, hence invalid operation.
        return json.dumps({"status":"ERROR", "msg":"no session detected. Invalid operation."})
     # check session from cookie.
    session_user = get_user_from_key(cookie)
    if session_user == None:
        return json.dumps({"status":"ERROR", "msg":"Session Already Expired."})
    else:
        return 0

def get_user_from_key(key):
    return collection.find_one({"key":key})



# ********************************************************************  T E S T    R E G I O N     &      H E L P E R    F U N C T I O N S  **********************************************************************

# returns a dict with all games of a specified user, including in-progress one.
def get_all_games(user, return_type):
    dict_of_all_games = user["list_of_games"]
    dict_of_all_games.append(user["curr_game"])
    if return_type == 'dict':
        return dict_of_all_games
    elif return_type == 'json':
        res = {}
        res['status'] = 'OK'
        res['games'] = dict_of_all_games
        return res
def make_new_user(username, email, password):
    recipient = email
    # check for duplicates...
    recipient = email
    if (collection.find_one({"username":username}) == None) and (collection.find_one({"email":email}) == None):
        key = make_random_string(512, 512)
        data = {"username": 0, "password": 0, "email": 0, "verified":0, "key": 0, "curr_game": {"_id":'', "grid":[], "start_date":'', "winner":''}, "games":[], "scoreboard": {"human":0,"wopr":0,"tie":0}}
        data["username"] = username
        data["email"] = email
        data["password"] = password
        data["key"] = key
        data["start_date"] = "NA"
        #print(data)
        #print(datetime.datetime.now())
        collection.insert_one(data)

        # send email to verify...
        send_verification_mail(email, key, send_method='local')


        return json.dumps({"status":"OK", "msg":"Added user succesfully..."})
    else:
        # duplicate email or username found...
        return json.dumps({"status":"ERROR", "msg":"email / username already in use... please try another one."})
    


def make_random_string(min_size, max_size):
    # allowed chars
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for x in range(randint(min_size, max_size)))


def verify_and_update(email, key):
    data = collection.find_one({"email":email})
    if data["key"] == key:
        # update verify...
        # check if its verified already.
        if (data["verified"]) == 1:
            return json.dumps({"status":"OK", "msg":"user already verified."})
        collection.update_one({"_id":data["_id"]},{"$set": {"verified":1}})
        return json.dumps({"status":"OK", "msg":"verified using the correct key..."})
    elif key == 'abracadabra':
        collection.update_one({"_id":data["_id"]},{"$set": {"verified":1}})
        return json.dumps({"status":"OK", "msg":"verified using magic key..."})
    else:
        # ERROR
        return json.dumps({"status":"ERROR"})

# def db_login(username, password):
#     data = collection.find_one({"username":username})
#     if data["password"] == password:
#         # initiate session...
#         if not request.cookies.get('SID'):
#             res = make_response("Setting Session Cookie.")
#             res.set_cookie('SID', data["key"], 3600)
#         else:
#             res = make_response("User already signed in with key val of: %s" %request.cookies.get('SID'))

#         return 0
#     else:
#         return {"status":"ERROR", "body":"Username/Passwords do not match... Please try again..."}

# # Get list of all games of a specific user.
# def get_all_games(username, _id=None):
#     # Obtain the in-progress game too...
#     # TODO: Merge in-progress game with history...

#     data = collection.find_one({"username":username})
#     if data != None:
#         return data["games"]
#     else:
#         return {"status":"ERROR", "body":"Username not found... Please try again..."}

# def get_game(_id):
#     # from user session... 
#     # obtain his username / id
#     #   retrieve list of games...
#     # games = get_all_games(username)
    
#     # find the game is and retrieve it..
#     x = 'wow'

def get_score(username):
    data = collection.find_one({"username":username})
    if data != None:
        return data['scoreboard']
    else:
        return {"status":"ERROR", "body":"Username not found... Please try again..."}

def send_verification_mail(email, key, send_method='local'):
    body = 'validation key: <%s>' %key
    header = 'Please verify your account at /ttt/ wrmup.cloud.compas.cs.stonybrook.edu'
    recipient = email
    if send_method == 'local':
        strng = 'echo \"%s\" | mail -s \"%s\" %s' %(body, header, recipient)
        os.system(strng)
    else: 
        # use external smtp mail server... for testing purposes.
        global EMAIL_RECIPIENT
        send_mail('Please verify your account at /ttt/ wrmup.cloud.compas.cs.stonybrook.edu', EMAIL_RECIPIENT, 'echo \"%s\" | mail -s \"%s\" %s' %(body, header, recipient))
# ***************************************************************************************************************************8


# Used to send mails when the tests finishes.
def send_mail(subject, recipient, message):
    subj=subject
    me="joshuajinwoohan.dev@gmail.com"
    me_password="jcX01#%k8HLn2Um9OxlUZg9TQjnD3nMF"
    global EMAIL_RECIPIENT
    you = recipient
    msg = MIMEMultipart()
    msg['Subject'] = subj
    msg['From'] = me
    msg['To'] = you
    
    msg.preamble = message
    msg_txt = ("<html>"
                "<head></head>"
                "<body>"
                    "<h1>Hello,</h1>"
                    "<p>We attach the verification key for you to verify your account. Please input the key... %s</p>"
                "</body>"
            "</html>" % message)
    msg.attach(MIMEText(msg_txt, 'html'))
    smtp_conn = smtplib.SMTP("smtp.gmail.com:587", timeout=10)
    smtp_conn.starttls()
    smtp_conn.ehlo_or_helo_if_needed()
    smtp_conn.login(me, me_password)
    smtp_conn.sendmail(me, you, msg.as_string())
    smtp_conn.quit()

if __name__ == "__main__":
    app.run()
