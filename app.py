from flask import Flask
from flask import render_template, request, make_response, redirect, url_for
import requests
import random
import json

app = Flask(__name__)

@app.route("/")
def hello_world():
    #retun 'hello' + home
    return "<p>Hello, App!</p>"

@app.route('/home', methods=['GET'])
def getTicTacToe():
    #return render_template('tictactoe.html', input_value = [])
    empty_board = ["" for i in range(10)]
    resp = make_response(render_template('tictactoe.html', input_value = empty_board, game_status = ""))
    for i in range(10):
        resp.set_cookie(str(i), "")
    return resp


@app.route('/home', methods=['POST'])
def postTicTacToe():
    responseJSON = callGetTTTApi()
    jsonData = json.dumps(responseJSON)

    # initialize an empty list of length 10
    input_value = ["" for i in range(10)]
    game_status = ""

    # pull out cookies values in input_value and update json accordingly
    # We use cookies to maintain board state.
    pyObj = json.loads(str(jsonData))
    for i in range(10):
        if (i == 0):
            continue
        value = request.cookies.get(str(i))
        input_value[i] = value
        player = None
        if (value == "X"):
            player = "Human"
        elif (value == "O"):
            player = "Bot"
        else:
            player = None
        pyObj["GameBoardState"]["Box " + str(i)] = player
    jsonData = json.dumps(pyObj)
    #print(jsonData)

    # Read user input and update board state
    if request.form['button']:
        valueOfClickedButton = request.form['button'] 
        indexOfClickedButton = int(valueOfClickedButton)
        input_value[indexOfClickedButton] = "X"
        player = "Human"
        choiceIndex = indexOfClickedButton
        newJsonData = updateJSON(jsonData, player, choiceIndex)
        # Let Bot play next move
        botResponseJson = callPostTTTApi(newJsonData)
        #print(botResponseJson)
        # To check which move bot played do following
        # Find all available moves bot had
        # Then check corresponding key in json obtained from recent POST call
        # key value will be "Bot" for the most recent bot's move
        choices = []
        for i in range(10):
            if (i == 0):
                continue
            value = request.cookies.get(str(i))
            if (value == ""):
                choices.append(i)
        
        gameBoardState = botResponseJson["GameBoardState"]
        for c in choices:
            boxIndexKey = "Box " + str(c)
            if (gameBoardState[boxIndexKey] == "Bot"):
                input_value[c] = "O" # update bot's move in frontend
                break
        
        if(botResponseJson["Status"] == "Game Over"):
            winner = botResponseJson["Winner"]
            if (winner == "Human"):
                game_status = "Congratulations!!! You won."
            elif (winner == "Bot"):
                game_status = "Oops!!! You lost. Better Luck next time"
            elif (winner == "None"):
                game_status = "Game Draw!!! Better Luck next time"
            
            # Since game over, so disable all available game buttons
            for i in range(10):
                if (input_value[i] == ""):
                    input_value[i] = " "
            resp = make_response(render_template('tictactoe.html', input_value = input_value, game_status = game_status))
            return resp

    # Reset game
    elif request.form['reset']:
        return redirect(url_for('home'))
    
    resp = make_response(render_template('tictactoe.html', input_value = input_value, game_status = game_status))
    for i in range(10):
        resp.set_cookie(str(i), input_value[i])
    return resp

def callGetTTTApi():
    url = "http://127.0.0.1:5001/"
    resp = requests.get(url)
    #print(responseJson.json())
    return resp.json()

def callPostTTTApi(jsonString):
    url = "http://127.0.0.1:5001/"
    j = json.loads(jsonString)
    # using requests.post(url, data=j) will not add the Content-Type header (so in particular it will NOT set it to application/json).
    # See https://docs.python-requests.org/en/latest/user/quickstart/#more-complicated-post-requests 
    resp = requests.post(url, json=j)
    return resp.json()

def updateJSON(jsonData, player, choiceIndex):
    pyObj = json.loads(str(jsonData))
    boxIndexKey = "Box " + str(choiceIndex)
    gameBoardState = pyObj["GameBoardState"]
    gameBoardState[boxIndexKey] = player
    return json.dumps(pyObj)

