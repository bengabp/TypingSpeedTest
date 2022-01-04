import sqlite3
import time
from random import choice
from threading import Thread

from kivy.animation import Animation
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.properties import StringProperty, BooleanProperty
from kivymd.app import MDApp
from kivymd.uix.list import OneLineIconListItem, IconLeftWidget
from plyer import notification


class SpeedTest(MDApp):
    # set properties which are referenced in the kv file
    time_format = StringProperty("01:00")
    words_label = StringProperty('')
    anim_completed = BooleanProperty(True)
    checked_words = StringProperty("")

    def __init__(self, **kwargs):
        super(SpeedTest, self).__init__(**kwargs)
        # register a function to be called for a window event
        Window.bind(on_keyboard=self.key_pressed)

        self.create_database()  # call  our create database function
        self.is_running = False  # set the game state
        self.counter = 0  # set the counter to zero . This counter is used to get the current word the user is typing from the list of words displayed for him on the screen
        self.correct_letters = []  # this will hold the letters typed correctly

    def build(self):
        Clock.schedule_once(self.animate_window)
        return Builder.load_file("speed.kv")

    # initialize the game by setting some important variables and attributes for the game and other methods
    # this function is being called from the kv file when the user hits the start button, passing in the player, level and screen parameters
    def game_init(self, player, level, sn):
        if player and level:
            levels = ['Easy', 'Medium', 'Hard']
            if level in levels:  # check if the level is valid
                self.player = player.lower()
                conn = sqlite3.connect("leaderboard.db")
                cursor = conn.cursor()
                users = []
                g = cursor.execute("SELECT user FROM leaderboard")
                for i in g:
                    users.append(i[0].lower())
                # check if the player's profile is in our datebase. if he does not exists, we add him
                if self.player.lower() not in users:
                    self.create_new_user(player.lower())
                cursor.close()
                conn.close()
                sn.current = "typing-layout-eng"
                # load all the words in the words file for processing
                with open("english_71657005.txt") as f:
                    self.all = f.read().split("\n")

                mn, mx = self.check_level(level)

                self.list_of_words = self.get_list_of_words(self.all, mn, mx)

                self.words = []
                self.get_words()
                self.words_label = " ".join(self.words)
                self.total_letters = 0
                self.is_running = True
                self.time = 60
                Clock.schedule_interval(self.tick,
                                        1)  # schedule our tick function which updates the seconds counter display
                Clock.schedule_once(
                    self.clear_login_text_box)  # schedule a function to clear the text input . You will notice that i am scheduling the function and not calling it directly because if i do so it will set the textfield text to an empty string but scheduling it will solve this problem thereby clearing all text in the textfield
            else:
                notification.notify("Invalid level")

        else:
            pass

    # this function is called every second to update the seconds counter display
    def tick(self, dt):
        if self.time >= 0:
            minute, sec = divmod(self.time, 60)
            self.time_format = "{:02d}:{:02d}".format(minute, sec)
            self.time -= 1
        else:
            Clock.unschedule(self.tick)
            self.stop_game()

    # this function checks the level entered by the player/user
    def check_level(self, level):
        self.words_range = 0, 0
        if level == "Easy":
            self.words_range = (1, 6)
        elif level == "Medium":
            self.words_range = (7, 9)
        elif level == "Hard":
            self.words_range = (9, 20)
        return self.words_range

    # get random list of words to use for the whole test section
    def get_list_of_words(self, list_of_all_words, min_value, max_value):
        list_of_words = []
        for i in list_of_all_words:
            if max_value > len(i) > min_value:
                list_of_words.append(i)
        return list_of_words

    # set the list of words to display
    def get_words(self):
        if len(self.list_of_words) > 10:
            for i in range(10):
                word = choice(self.list_of_words)
                self.words.append(word)
                self.list_of_words.remove(word)
        else:
            self.words = self.list_of_words

    # this function gets called when a keyboard event occurs
    def key_pressed(self, window, key, *args):
        # space bar keycode
        if key == 32:
            if self.is_running:
                self.space_bar_pressed()
            else:
                self.clear_text_field(0)

    # this function is called when the user presses the space bar key and the game is running (is_running is True)
    def space_bar_pressed(self):
        # get the word from the textfield and the list of words displayed for the player to type in
        word = self.root.ids.word.text.strip()
        words = self.words_label.split(' ')
        Clock.schedule_once(self.clear_text_field)

        if self.counter <= len(words) - 1:
            current_word = words[self.counter]
            if current_word == words[-1]:
                self.check_accuracy(current_word, word)
                self.counter += 1
                self.counter = 0
                self.checked_words = ""
                self.words = []
                self.get_words()
                self.words_label = " ".join(self.words)
            else:
                self.check_accuracy(current_word, word)
                self.counter += 1

        else:
            self.counter = 0
            self.checked_words = ""
            self.words = []
            self.get_words()
            self.words_label = " ".join(self.words)

    def clear_text_field(self, dt):
        self.root.ids.word.text = ''

    def clear_login_text_box(self, dt):
        self.root.ids.user_name.text = ''
        self.root.ids.level.text = ''

    # this founction checks if the user typed in the word correctly, filtering out the correct letters in the word and storing it in the correct_words list
    def check_accuracy(self, current_word, word):
        self.total_letters += len(word)
        if len(current_word) > len(word):
            word_length = len(word)
        else:
            word_length = len(current_word)

        for i in range(0, word_length):
            if word[i] == current_word[i]:
                self.correct_letters.append(word[i])

                if len(word) < len(current_word):
                    self.checked_words += f"[color=#EB2224]{current_word[i]}[/color]"

                else:
                    self.checked_words += f"[color=#15A72D]{current_word[i]}[/color]"

            else:
                self.checked_words += f"[color=#EB2224]{current_word[i]}[/color]"
        self.checked_words += " "

    # this function is called when the counter display zeros out
    def stop_game(self):
        self.is_running = False
        self.checked_words = ""
        if len(self.correct_letters) <= 0:
            accuracy = 0
        else:
            accuracy = int((len(self.correct_letters) / self.total_letters) * 100)
        wpm = int(len(self.correct_letters) / 5)

        self.root.ids.eng_win.current = "score_board"

        self.update_score(accuracy, wpm, self.player)  # update the user's score to our database
        self.counter = 0
        self.correct_letters = []
        Clock.schedule_once(self.clear_text_field)

    def create_database(self):
        conn = sqlite3.connect("leaderboard.db")
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS leaderboard(
             id integer PRIMARY KEY AUTOINCREMENT UNIQUE,
             user text NOT NULL,
            accuracy INTEGER NOT NULL,
            wpm INTEGER NOT NULL);
        """)
        cursor.close()
        conn.close()

    # this function creates a new user in our database
    def create_new_user(self, name):
        conn = sqlite3.connect("leaderboard.db")
        cursor = conn.cursor()
        if name:
            if name not in cursor.execute("SELECT user FROM leaderboard"):
                cursor.execute("INSERT INTO leaderboard (user, accuracy, wpm) VALUES (?,?,?)", (name, 0, 0))
                conn.commit()
                cursor.close()
                conn.close()

    def update_score(self, accuracy, wpm, player):
        global info
        conn = sqlite3.connect("leaderboard.db")
        cursor = conn.cursor()
        _sql = f"SELECT * FROM leaderboard"
        usr = cursor.execute(_sql)
        # get the information for the current player
        for i in usr:
            print(i)
            if i[1] == player:
                info = i

        # update the player's accuracy and wpm if their corresponding values are bigger than the one stored in the database
        if accuracy > info[2]:
            _sql = f"UPDATE leaderboard SET accuracy={accuracy} WHERE id={info[0]}"
            cursor.execute(_sql)
        if wpm > info[3]:
            _sql = f"UPDATE leaderboard SET wpm={wpm} WHERE id={info[0]}"
            cursor.execute(_sql)

        conn.commit()
        cursor.close()
        conn.close()

        self.root.ids.wpm_label.text = f"Speed: {wpm} wpm"
        self.root.ids.accuracy_label.text = f"Accuracy: {accuracy}%"

    # this function is called when the user clicks the show leaderboard button
    def show_leaderboard(self):
        conn = sqlite3.connect("leaderboard.db")
        cursor = conn.cursor()
        # order the database according to the wpm in descending order
        _sql = f"SELECT * FROM leaderboard ORDER BY wpm DESC"
        profile = cursor.execute(_sql)
        self.root.ids.row.clear_widgets()
        for i in profile:
            space = " " * 30
            ic = IconLeftWidget(icon="account", theme_text_color='Custom', text_color=self.theme_cls.primary_color)
            list_item = OneLineIconListItem(text=f"{i[1].capitalize()}{space}{i[3]} wpm", font_style="Body1",
                                            theme_text_color='Custom', text_color=self.theme_cls.primary_color)
            list_item.add_widget(ic)
            self.root.ids.row.add_widget(list_item)
        cursor.close()
        conn.close()

    def animate_window(self, dt):
        anim = Animation(opacity=1)
        anim.start(self.root.ids.eng_win_id)
        write = Thread(target=self.write, daemon=True)
        write.start()

    def write(self):
        text = "Welcome to SpeedType \n Fill in the text field to get started and take your typing skills to the next level"
        text = ''.join(text)
        self.root.ids.welcome_label.text = ""
        self.anim_completed = False
        for letter in text:
            self.root.ids.welcome_label.text += letter
            time.sleep(0.05)
        self.anim_completed = True


if __name__ == "__main__":
    SpeedTest().run()
