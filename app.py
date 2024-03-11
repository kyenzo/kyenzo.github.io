from flask import Flask, render_template, request, session, redirect, url_for
import random

app = Flask(__name__)
app.secret_key = 'GuessTheNumber123'

class GuessTheNumberGame:
    def __init__(self):
        self.reset_game()

    def start_new_game(self, rounds, top_of_range):
        self.rounds = rounds
        self.top_of_range = top_of_range
        self.random_number = random.randint(1, self.top_of_range)
        self.current_round = 1
        self.total_guesses_player_1 = 0
        self.total_guesses_player_2 = 0
        self.current_player = "Player 1"
        self.guesses_player_1 = 0
        self.guesses_player_2 = 0

    def make_a_guess(self, guess):
        guess = int(guess)
        correct_guess = guess == self.random_number
        if self.current_player == "Player 1":
            self.total_guesses_player_1 += 1
            self.guesses_player_1 += 1
        else:
            self.total_guesses_player_2 += 1
            self.guesses_player_2 += 1
        
        if correct_guess:
            winner = self.current_player
            self.current_round += 1
            if self.current_round <= self.rounds:
                self.random_number = random.randint(1, self.top_of_range)
                self.guesses_player_1 = 0
                self.guesses_player_2 = 0
                self.current_player = "Player 1"
            return True, winner
        else:
            self.switch_player()
            return False, None

    def switch_player(self):
        self.current_player = "Player 2" if self.current_player == "Player 1" else "Player 1"

    def game_over(self):
        return self.current_round > self.rounds

    def get_winner(self):
        if self.total_guesses_player_1 < self.total_guesses_player_2:
            return "Player 1"
        elif self.total_guesses_player_2 < self.total_guesses_player_1:
            return "Player 2"
        else:
            return "Draw"

    def reset_game(self):
        self.total_guesses_player_1 = 0
        self.total_guesses_player_2 = 0
        self.current_player = "Player 1"
        self.random_number = 0
        self.top_of_range = 100  # Default value, can be adjusted when starting a new game
        self.rounds = 1  # Default value
        self.current_round = 1
        self.guesses_player_1 = 0
        self.guesses_player_2 = 0

# Create a global instance of the game
game_instance = GuessTheNumberGame()

@app.route('/', methods=['GET', 'POST'])
def home():
    message = ""
    if request.method == 'POST':
        if 'start_game' in request.form:
            rounds = int(request.form.get('rounds', 1))
            top_of_range = int(request.form.get('top_of_range', 100))
            game_instance.start_new_game(rounds, top_of_range)
            return redirect(url_for('home'))
        elif 'guess' in request.form:
            guess = request.form['guess']
            correct, winner = game_instance.make_a_guess(guess)
            if correct:
                message = f"{winner} wins! Starting next round..."
                if game_instance.game_over():
                    winner = game_instance.get_winner()
                    game_instance.reset_game()
                    message = f"Game Over. {winner} wins the game!"
                    return render_template('game_over.html', winner=winner)
            else:
                message = f"Wrong guess! {game_instance.current_player}'s turn."

    return render_template('index.html', game=game_instance, message=message)

@app.route('/reset', methods=['GET'])
def reset():
    game_instance.reset_game()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
