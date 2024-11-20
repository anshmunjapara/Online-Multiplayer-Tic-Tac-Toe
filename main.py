import json
import socket
import time
from _thread import *

host = '127.0.0.1'  # server address
port = 65431

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    s.bind((host, port))
except socket.error as e:
    str(e)

s.listen()
print("waiting for connection")

games = {}
id_count = 0


def threaded_client(connection: socket.socket, player, room):
    global id_count

    reply = {"player": player}

    connection.send(str.encode(json.dumps(reply)))
    reply = ""
    time.sleep(1)
    while True:

        try:

            if games[room]["ready"]:
                reply = json.dumps({"type": "ready"})

                games[room]["players"][0].send(reply.encode())
                games[room]["players"][1].send(reply.encode())
                games[room]["ready"] = False

            data = connection.recv(2048)
            reply = data.decode("utf-8")

            if not data:
                print(f"player {player} Disconnected")
                break
            else:
                print("Received: ", reply)
                decoded_message = json.loads(reply)

                other_player = 1 if player == 0 else 0
                if "move" in decoded_message:
                    if len(games[room]["players"]) == 2:
                        print(f"Relaying move to Player {other_player} in room {room}")
                        games[room]["players"][other_player].send(data)
                if "playerName" in decoded_message:
                    if len(games[room]["players"]) == 2:
                        games[room]["players"][other_player].send("\n".encode())
                        print(f"Relaying Player name to  {other_player} in room {room}")
                        games[room]["players"][other_player].send(data)

        except Exception as e:
            print(f"Error with Player {player} in room {room}: {e}")
            break

    connection.close()
    if room in games:
        if connection in games[room]["players"]:
            games[room]["players"].remove(connection)
            print(f"Player: {player} got removed.")

            # If no players are left in the room, delete the room

            if len(games[room]["players"]) == 0:
                del games[room]
                print(f"Room {room} deleted due to disconnection.")

            else:
                # Notify the remaining player of the disconnect
                print(f"notifying another player.")
                remaining_player = games[room]["players"][0]
                remaining_player.send(str.encode("\n"))
                disconnect_msg = json.dumps({"type": "disconnect"})
                remaining_player.send(disconnect_msg.encode())

        # Decrement the global player ID count
        id_count -= 1


while True:
    conn, addr = s.accept()
    print("Connected to: ", addr)

    id_count += 1
    p = 0
    game_id = (id_count - 1) // 2

    if id_count % 2 == 1:
        games[game_id] = {"players": [conn], "ready": False}
        print("Creating a new game.")
    else:
        games[game_id]["players"].append(conn)
        games[game_id]["ready"] = True
        p = 1
    start_new_thread(threaded_client, (conn, p, game_id))
