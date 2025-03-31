#!/usr/bin/env python3
import socket
import struct
import time
import argparse
from flask import Flask 

# defining ip and port numbers as arguments 
parser = argparse.ArgumentParser(description="Write JSON data to a file.") 
parser.add_argument("--ip", type=str, required=True, help="server's ip address.")

# parsing arguments defined above 
args = parser.parse_args()

app = Flask(__name__)

# Create a UDP socket and send the request
def send_udp_request(server_ip, server_port, request_time, command, team_num):
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    if team_num is None: 
        # Build request packet (time, command)
        request_packet = struct.pack("!II",request_time,int(command)) # two unsigned ints each 4 bytes long packed in big-endian format
    else:
        request_packet = struct.pack("!IIf",request_time,command,float(team_num)) # two unsigned int and a 4 byte floating-point number 

    # Send UDP request
    udp_socket.sendto(request_packet, (server_ip, server_port))
    
    return udp_socket

# Receive and process the response from the server
def receive_raw_response(udp_socket):
    response, server_address = udp_socket.recvfrom(1024)  # Buffer size 1024 bytes 

    # Extract response data
    server_time, command = struct.unpack("II", response[:8])

    # Decode data (you can customize this as needed)
    output_data = response[8:]

    return server_time, command, output_data, server_address

# Main function to drive the script
@app.route('/get_data/<int:team_num>',methods=['GET'])
def get_data(team_num):
    float_outputs = set(range(17, 23)) | set(range(27, 37)) | set(range(38, 48)) | set(range(58,103)) | {106,109,112,115,118}

    results = {} 

    for command in range(1,119): # iterates from 1-118 to send to server 
        request_time = int(time.time())
        if command >= 58: 
            # Send UDP request
            udp_socket = send_udp_request(args.ip, 14141, request_time, command,team_num)
            # Receive and process the server's response
            server_time, command_received, output_data, server_address = receive_raw_response(udp_socket) 
            if command in float_outputs: 
                decoded_data = struct.unpack(">f", output_data)  # Big-endian float
                decoded_data = decoded_data[0] 
            else: 
                # decoded_data = struct.unpack(">I", output_data)  # Big-endian float
                decoded_data = struct.unpack(">I", output_data)[0] & 0xFF
            # decoded_data is a tuple so just extract first entry 
        else: 
            udp_socket = send_udp_request(args.ip, 14141, request_time, command,None) 
            # Receive and process the server's response
            server_time, command_received, output_data, server_address = receive_raw_response(udp_socket) 
            if command in float_outputs:
                decoded_data = struct.unpack(">f", output_data) # Unsigned int 
                decoded_data = decoded_data[0] 
            else: 
                # decoded_data = struct.unpack(">I", output_data) # Unsigned int
                decoded_data = struct.unpack(">I", output_data)[0] & 0xFF

        # write to json file/ write to persistent database / write to data variable in script 
        results[command] = decoded_data 

    # Close the socket
    udp_socket.close()
    return results 

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0') 
