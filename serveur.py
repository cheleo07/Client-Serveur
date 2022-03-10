import json
import random
import time
from socket import socket, AF_INET, SOCK_STREAM
import string
from struct import pack, unpack
from threading import Thread, Event
from typing import Any
from random import choice

from unidecode import unidecode

PORT = 0x2BAD
NB_LETTERS_WIN = 30
players = []
list_of_words = []
first_letter = ""

def word():
    f = open('mot.txt', 'r', encoding='utf8')
    contenu = f.readlines()
    return unidecode(choice(contenu)).upper().replace('\n', '')

lettres_deja_proposees = []
mot_a_deviner = word()
#affichage = underscore(mot_a_deviner)
nb_erreurs = 0


class Player(Thread):
    def __init__(self, num, sock):
        Thread.__init__(self)
        self._id = num
        self._sock = sock
        self._ready = False
        self._nbletters = 0

    def is_ready(self):
        return self._ready is not None

    def run(self):
        global ready_event
        self._sock.send(create_json("idjoueur", self._id))
        isReady = self._sock.recv(4096)
        self._choice = read_json(isReady)
        if all_players_ready():
            starter_time = time.time()  #########
            while True:
                mot = mot_a_deviner  # random mot
                self._sock.send(mot.encode())  # envoi mot au client
                letterIsCorrect = False
                while (not letterIsCorrect):
                    letter = self._sock.recv(4096).decode()  # recu lettre client
                    if letter not in lettres_deja_proposees:
                        lettres_deja_proposees += [letter]
                    if not (letter[0] == mot):  # si première lettre mot client == random letter
                        # Si 1, mauvaise premiere lettre
                        self._sock.send(pack('!i', 1))  # Envoie code associé au mot
                    elif letter in list_of_words:
                        # Si 0, mot conforme
                        self._nbletters += len(letter)
                        if self._nbletters > NB_LETTERS_WIN:
                            end_time = time.time()
                            self._sock.send(pack('!i', 3))
                            self._sock.send(pack('!i', self._nbletters))
                            x = (end_time - starter_time)
                            self._sock.send(pack('!f', x))
                            print(f"- Player {self._id} left")
                            return
                        else:
                            self._sock.send(pack('!i', 0))
                            wordIsCorrect = True
                    else:
                        # Si 2 mot qui n'existe pas
                        self._sock.send(pack('!i', 2))
                    self._sock.send(pack('!i', self._nbletters))

def load_list_of_words():
    a_file = open("mot.txt", "r", encoding="utf8")
    for line in a_file:
        word = line.rstrip()
        list_of_words.append(word)
    a_file.close()


def all_players_ready():
    global players
    for player in players:
        if player is not None and not player.is_ready():
            return False
    return True


def find_player_id():
    global players
    for i in range(len(players)):
        if players[i] is None:
            return i + 1
    players.append(None)
    return len(players)


def create_json(method: str, params: Any):
    data = {"jsonrpc": "2.0", "method": method, "params": params}
    return json.dumps(data).encode()


def read_json(data: bytes):
    dict = json.loads(data.decode())
    value = dict["params"]
    return value


if __name__ == '__main__':
    with socket(AF_INET, SOCK_STREAM) as sock_listen:
        sock_listen.bind(('', PORT))
        sock_listen.listen(5)
        print(f"Listening on port {PORT}")
        load_list_of_words()
        while True:
            sock_service, client_addr = sock_listen.accept()
            index = find_player_id()
            print(f"- Player {index} arrived")
            players[index - 1] = Player(index, sock_service)
            players[index - 1].start()