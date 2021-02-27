# Hackathon Programming Challenge

* This hackathon challenge is exciting and interesting and there are a lot many things to learn. It is to send a video stream between server and client using aiortc library of TCPsocketSignalling.


* In this repo I have created communication between server and client while multiprocessing with a queue. Generate 2D image frames of ball bouncing. Create a separate multi-processsing process_a.
  

# Dependencies:
* Linux or Ubuntu(18.0.4)
* Python 3.4+
* Numpy
* [Opencv](https://pypi.org/project/opencv-python/)
* [aiortc](https://github.com/aiortc/aiortc)
* [multiprocessing](https://docs.python.org/3.7/library/multiprocessing.html)

# To launch files:
1) Open Terminal with two tabs

2) Run:
python3 server.py

3) In another terminal Run:
python3 client.py

# Challenge:
* Make a server python program that runs from the command line (**python3 server.py**)
* Make a server client program that runs from the command line (**python3 client.py**)
* Using aiortc built-in [TcpSocketSignalling](https://github.com/aiortc/aiortc/blob/f85f7133435b54ce9de5f2f391c0c0ef0014e820/aiortc/contrib/signaling.py#L147):
  * The server should create an **aiortc** *offer* and send to client.
  * The client should recive the *offer* and create an **aiortc** answer.
* The server should generate a continuous 2D image of ball bouncing across the screen.
* The server should transmit these images to client via **aiortc** using frame trasport(extend **aiortc.MediaStreamTrack**).
* The cleint should display received images using Opencv.
* The client should start new **multiprocessing.Process(process_a)**.
* The client should send received frame to this **process_a** using **multiprocessing.Queue**.
* The client **process_a** should parse the image and determine the current location of the ball as x,y coordinates.
* The client **process_a** should store the computed x,y coordinate as **multiprocessing.Value**.
* The client should open an **aiortc** data channel to the server and send each x,y coordinates to the server. These coordinates are from **process_a** but sent to server from client main thread.
* The server program should display recievd coordinates and compute error to actual location of the ball.
* Write **unit tests** for all functions which will be executed by pytest(pytest test_Your_SCRIPT.py)
* **Docker** and **Kubernets**:
  * Make a Docker Container for server.
  * Make a Docker Container for client.
  * Use **minikube** to create deployment of server and client.



