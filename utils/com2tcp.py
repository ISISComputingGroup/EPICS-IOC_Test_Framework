import argparse
import socket
import sys
import threading
import time

import serial


def listen_to_tcp(tcp_conn: socket.socket, serial_conn: serial.Serial) -> None:
    while True:
        tcp_data = tcp_conn.recv(1024)
        if len(data) > 0:
            serial_conn.writelines([tcp_data])
            print("Data on tcp: " + str(tcp_data))
        time.sleep(0.001)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Transfers data between a COM port and a TCP port."
    )
    parser.add_argument("tcp_port", help="The port to send TCP messages to. (e.g. 57677)", type=int)
    parser.add_argument("com_port", help="The COM port to send serial messages to. (e.g. COM2)")
    parser.add_argument(
        "-b", "--baud", help="The baud rate to communicate on the COM port.", default=9600
    )

    args = parser.parse_args()

    try:
        tcp_conn = socket.create_connection(("localhost", args.tcp_port))
    except Exception as e:
        print("Failed to connect to tcp port: " + str(e))
        sys.exit()

    try:
        serial_conn = serial.Serial(args.com_port, args.baud)
    except Exception as e:
        print("Failed to connect to serial port: " + str(e))
        sys.exit()

    listen_thread = threading.Thread(target=listen_to_tcp, args=(tcp_conn, serial_conn))
    listen_thread.daemon = True
    listen_thread.start()

    print("Listening on " + str(args.com_port) + " and localhost:" + str(args.tcp_port))
    print("Press Ctrl+C to stop")

    try:
        while True:
            if serial_conn.in_waiting:
                data = serial_conn.read()
                print("Data on serial: " + str(data))
                tcp_conn.sendall(data)

            time.sleep(0.001)
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        tcp_conn.close()
        serial_conn.close()
