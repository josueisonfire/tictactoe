
from flask import Flask
from flask import request
from flask import render_template
from flask import jsonify
import json
import random
import datetime
import os
import sys

app = Flask(__name__)

@app.route("/")
def hello():
    return "Hello, Flask!"


@app.route('/ttt', methods=['POST'])
def return_game_form():
    print('POST REQUEST: %s' %str(os.getcwd()), file=sys.stderr)
    if request.form.get('name') != None:
        name = request.form.get('name')
        date = datetime.datetime.today()
        return render_template('sample.html', name=name, date=date)
    else:
        return "Erroneous Request."

@app.route('/ttt', methods=['GET'])
def init_form():
    return '''
        <h1>Enter Your name:</h1>

        <form action="/ttt" method="POST">
            <label for="name">name: </label>
            <input name="name" placeholder="enter your name">
            <button type="submit">submit</button>
        </form>
        '''
req_count = 0

@app.route('/ttt/play', methods=['POST'])
def play():
    received_data = request.get_data()

    obj = json.loads(received_data)
    #print('Received: %s' %received_data, file=sys.stderr)
    obj = obj["grid"]
    #print ('Received: %s' %obj, file=sys.stderr)

    
    rgrid = obj
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

def play_ttt(grid=[' ',' ',' ',' ',' ',' ',' ',' ',' ']):
    filled = False
    while(filled == False):
        ran = random.randint(0,8)
        if grid[ran] == ' ':
            grid[ran] = 'O'
            filled = True
    return grid

def check_victory(grid):

    if (grid[0] == grid[1]) and (grid[0] == grid[2]):
        #print('Player: %s has won in series 0-1-2' %grid[0], file=sys.stderr)
        return grid[0]

    elif (grid[3] == grid[4]) and (grid[3] == grid[5]):
        #print('Player: %s has won in series 0-1-2' %grid[3], file=sys.stderr)
        return grid[3]
    
    elif (grid[6] == grid[7]) and (grid[6] == grid[8]):
        #print('Player: %s has won in series 0-1-2' %grid[6], file=sys.stderr)
        return grid[6]
   
    elif (grid[0] == grid[3]) and (grid[0] == grid[6]):
        #print('Player: %s has won in series 0-1-2' %grid[3], file=sys.stderr)
        return grid[0]
    
    elif (grid[1] == grid[4]) and (grid[1] == grid[7]):
        #print('Player: %s has won in series 0-1-2' %grid[1], file=sys.stderr)
        return grid[1]
    
    elif (grid[2] == grid[5]) and (grid[2] == grid[8]):
        #print('Player: %s has won in series 0-1-2' %grid[2], file=sys.stderr)
        return grid[2]
    
    elif (grid[0] == grid[4]) and (grid[0] == grid[8]):
        #print('Player: %s has won in series 0-1-2' %grid[0], file=sys.stderr)
        return grid[4]
    
    elif (grid[2] == grid[4]) and (grid[2] == grid[6]):
        #print('Player: %s has won in series 0-1-2' %grid[2], file=sys.stderr)
        return grid[2]
    else:
        full = True
        for cell in grid:
            if cell == ' ':
                full = False
        if full:
            return 'TIE'
        return ' '
    
if __name__ == "__main__":
    app.run()