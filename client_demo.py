import socket
import threading
import sys
import os
from time import sleep


def get_message_from_output(message: str):
    """ helper function for autosending messages """
    split_word = message.split("#")
    after_asterix = split_word[1]
    after_colon = after_asterix.split(":")
    user_message = after_colon[1]
    return user_message


def get_channel_from_output(message: str):
    """ helper function for autosending messages """
    split_word = message.split("#")
    after_asterix = split_word[1]
    split_again = after_asterix.split(" ")
    channel_name = split_again[0]
    return channel_name


def print_recv_message():
    """helper function for use with threading"""

    output_message = str
    channel_name = str

    while True:
        data = client.recv_message()

        if "PING :tmi.twitch.tv" in data:
            client.send_pong()

        if "PRIVMSG #" in data:
            output_message = get_message_from_output(data).strip()

            if output_message in client.channel_commands:
                channel_name = get_channel_from_output(data).strip()
                sleep(1)
                client.autosend_message(channel_name, client.channel_commands.get(output_message))

        print(data)


class IRCClient:

    def __init__(self, username, port=6667, address="irc.chat.twitch.tv"):
        self.username = username
        self.password = None
        self.address = address
        self.port = port
        self.__sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        self.channel_commands = {}

    def connect(self):
        self.__sock.connect((self.address, self.port))
        self.__sock.send(f"{self.password}\r\n".encode())
        self.__sock.send(f"NICK {self.username}\r\n".encode())

    def set_password(self):
        with open(os.path.join(sys.path[0], "auth_pass.txt"), "r+") as pass_text:
            if "PASS" not in pass_text.read():
                text_password = input(
                    "Enter your authorized password token.\nGo to https://twitchapps.com/tmi/ to obtain it "
                    "and copy-paste the token here:\n")
                pass_text.write(f"PASS {text_password}")

            pass_text.seek(os.SEEK_SET) # return file back to start
            self.password = pass_text.read()
            pass_text.close()

    def join_channel(self, message):
        self.__sock.send(f"{message}\r\n".encode())

    def part_channel(self, message):
        self.__sock.send(f"{message}\r\n".encode())

    def autosend_message(self, channel, message):
        self.__sock.send(f"PRIVMSG #{channel} :{message}\r\n".encode())

    def send_channel_message(self, message):
        cmd_and_message = message.split("#")

        while True:
            user_input = input()
            if user_input.upper() in ["QUIT", "EXIT"]:
                exit(1)
            elif user_input.startswith("PART #"):
                self.__sock.send(f"{user_input}\r\n".encode())
                break
            else:
                self.__sock.send(f"PRIVMSG #{cmd_and_message[1]} :{user_input}\r\n".encode())

    def send_pong(self):
        self.__sock.send("PONG :tmi.twitch.tv\r\n".encode())

    def recv_message(self):
        return self.__sock.recv(512).decode()

    def get_list_of_commands(self, command_file_name):
        cmd_dict = {}
        with open(os.path.join(sys.path[0], command_file_name), "r") as cmd_text:
            for line in cmd_text:
                split_line = line.split("    ")
                if split_line:
                    key = split_line[0]
                    value = split_line[1]
                    cmd_dict[key] = value
                else:
                    print("ERROR")

        cmd_text.close()
        self.channel_commands = cmd_dict  # point our class dictionary to our newly created dictionary

    def close_connection(self):
        self.__sock.close()


if __name__ == "__main__":

    client = None

    if len(sys.argv) not in range(2, 4):
        print("Enter a username, OPTIONAL port, OPTIONAL server\n")
        print("As so: \"John123, 6667, irc.chat.twitch.tv\"")
        exit(1)

    if len(sys.argv) == 2:
        client = IRCClient(sys.argv[1])
    elif len(sys.argv) == 3:
        client = IRCClient(sys.argv[1], sys.argv[2])
    elif len(sys.argv) == 4:
        client = IRCClient(sys.argv[1], sys.argv[2], sys.argv[3])

    client.set_password()
    print(client.password)
    client.connect()
    recieve_thread = threading.Thread(target=print_recv_message)
    recieve_thread.daemon = True  # kills thread automatically once main is exited
    recieve_thread.start()

    while True:

        message = input()

        if message.startswith("JOIN #"):
            client.join_channel(message)
            client.send_channel_message(message)

        elif message.upper() == "BOT":
            print("Enter name of game you want to use a default bot for\n"
                  "Current games:\nLeague of Legends - type \"league\"\n")

            game = input()
            try:
                client.get_list_of_commands(game + "_commands.txt")
                print(f"{game} commands initialized\n")
            except FileNotFoundError:
                continue

        elif message.upper() in ["QUIT", "EXIT"]:
            break
        else:
            print("\nCommand not recognized\nJOIN #<channel> to join a channel"
                  "\nPART #<channel> to leave a channel"
                  "\nPRIVMSG #<channel> :<message> to send a message on a channel\n")

    client.close_connection()
