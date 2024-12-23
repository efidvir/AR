from flask import Flask, render_template, redirect, url_for, session
from flask_socketio import SocketIO, emit
from collections import Counter

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Needed to use sessions
socketio = SocketIO(app)

# Store the players as a list of dictionaries
players = []

# Store the riddles with options
riddles = [
    {
        "id": 1,
        "text": "What has to be broken before you can use it?",
        "options": ["An Egg", "A Lock", "A Mirror", "A Glass"]
    }
]

# Store votes as a Counter
votes = Counter()

@app.route('/')
def home():
    session['access_team_gathering'] = True
    return render_template('index.html')

@app.route('/team-gathering')
def team_gathering():
    if session.get('access_team_gathering'):
        session.pop('access_team_gathering')
        return render_template('team-gathering.html')
    else:
        return redirect(url_for('home'))

@app.route('/game')
def game():
    return render_template('game.html', riddles=riddles)

@socketio.on('join')
def handle_join(data):
    name = data['name']
    if not any(player['name'] == name for player in players):
        players.append({'name': name, 'ready': False})
        emit('update_players', players, broadcast=True)

@socketio.on('edit')
def handle_edit(data):
    old_name = data['oldName']
    new_name = data['newName']
    for player in players:
        if player['name'] == old_name:
            player['name'] = new_name
            break
    emit('update_players', players, broadcast=True)

@socketio.on('toggle_ready')
def handle_toggle_ready(data):
    name = data['name']
    ready = data['ready']
    for player in players:
        if player['name'] == name:
            player['ready'] = ready
            break
    emit('update_players', players, broadcast=True)

@socketio.on('vote')
def handle_vote(data):
    option = data['option']
    votes[option] += 1
    emit('update_votes', dict(votes), broadcast=True)
    check_votes()

def check_votes():
    # Check if all players have voted
    total_votes = sum(votes.values())
    if total_votes >= len(players):
        # Find the option with the most votes
        winning_option = votes.most_common(1)[0][0]
        emit('winning_option', winning_option, broadcast=True)
        votes.clear()  # Reset votes for the next round


@socketio.on('all_ready')
def handle_all_ready():
    emit('game_ready', broadcast=True)



if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5001, debug=True)
