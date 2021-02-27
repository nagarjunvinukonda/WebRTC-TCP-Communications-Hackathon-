#!/usr/bin/env python3

import numpy as np
import cv2
import aiortc
import multiprocessing
import argparse
import asyncio
import logging
import time
import json

from aiortc import RTCPeerConnection, RTCIceCandidate, RTCSessionDescription, VideoStreamTrack
from aiortc.contrib.signaling import add_signaling_arguments, create_signaling, BYE


def channel_log(channel, t, message):
    logging.info("channel(%s) %s %s" % (channel.label, t, message))


def channel_send(channel, message):
    channel_log(channel, ">", message)
    channel.send(message)


def get_args():
    parser = argparse.ArgumentParser()

    parser.add_argument('--verbose', type=bool, default=True)
    add_signaling_arguments(parser)

    args = parser.parse_args()
    args.signaling = 'tcp-socket'
    return args


async def make_answer(peer_connection, signaling, queue, x, y):

    """
    Description:
    Makes an answer to the offer received from server.
    When the message is received it is put into queue.
    Client showing received messages through opencv. 

    """

    channel = peer_connection.createDataChannel("chat")
    channel_log(channel, "-", "created by local party")

    # async def send_pings():
    #     while True:
    #         channel_send(channel, "ping %d" % current_stamp())
    #         await asyncio.sleep(1)

    # @channel.on("open")
    # def on_open():
    #     asyncio.ensure_future(send_pings())


    @peer_connection.on("track")
    async def on_track(track):
        logging.info("Track %s received" % track.kind)
        frame = await track.recv()
        image = frame.to_ndarray(format="bgr24")
        cv2.imshow('image', image)  
        queue.put([image, frame.pts])
        logging.info('Image put to queue!!!!')
        cv2.waitKey(1)
        
    while True:
        message = None
        try:
            message = await signaling.receive()
        except asyncio.streams.LimitOverrunError as e:
            logging.error('Limit Overrun error handled', e)
            

        if isinstance(message, RTCSessionDescription):
            await peer_connection.setRemoteDescription(message)

            if message.type == "offer":
                logging.info("Received message from server!!!")
                await peer_connection.setLocalDescription(await peer_connection.createAnswer())
                await signaling.send(peer_connection.localDescription)
                x_val = None
                y_val = None
                with x.get_lock():
                    x_val = x.value
                with y.get_lock():
                    y_val = y.value

                channel._setReadyState("open")

                values = {'x': x_val, 'y': y_val}
                data = json.dumps(values)
                channel_send(channel, data)
                


        elif message is BYE:
            print("Exiting")
            break
        await signaling._writer.drain()
    channel.close()
            
class ProcessA(multiprocessing.Process):

    """
    Description:
    Clients new multiprocessing thread.
    It computes x,y coordinates of multiprocessing value. And try to send it to the server.

    Raises:
    Unable to send message to server. 
    The compute x,y is unable to detect the center of circle. 

    return
    x,y coordinates
    """    
    def __init__(self, task_queue, x, y):
        multiprocessing.Process.__init__(self)
        self.task_queue = task_queue
        self.x = x
        self.y = y

    def run(self):
        proc_name = self.name
        logging.info(proc_name + 'starting')
        while True:
            next_frame, time = self.task_queue.get()
            logging.info('Image received from queue at ' + str(time))
            if next_frame is None:
                logging.info('%s: Exiting' % proc_name)
                break
            logging.debug('%s: %s' % (proc_name, next_frame))
            x, y = self.compute_xy(next_frame)

            with self.x.get_lock():
                self.x.value = x
            with self.y.get_lock():
                self.y.value = y
        return

    def compute_xy(self, frame):
        x = 0
        y = 0

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        gray_blurred = cv2.blur(gray, (3, 3)) 
        # circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, 1.2, 100)

        detected_circles = cv2.HoughCircles(gray_blurred,  
                   cv2.HOUGH_GRADIENT, 1, 5, param1 = 50, 
               param2 = 30, minRadius = 1, maxRadius = 40) 

        if detected_circles is not None: 
            detected_circles = np.uint16(np.around(detected_circles)) 

            for pt in detected_circles[0, :]: 
                x, y = pt[0], pt[1] 
                # logging.info(x, y)
            ## To be corrected
                return x, y



if __name__ == '__main__':

    tasks = multiprocessing.Queue()
    x = multiprocessing.Value("i", 0)
    y = multiprocessing.Value("i", 0)



    process_a = ProcessA(tasks, x, y) 

    args = get_args()

    if args.verbose:
        logging.basicConfig(level=logging.INFO)

    signaling = create_signaling(args)
    peer_connection = RTCPeerConnection()

    process_a.start()
    offer = make_answer(peer_connection, signaling, tasks, x, y)


    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(offer)
    except KeyboardInterrupt:
        pass
    finally:
        loop.run_until_complete(peer_connection.close())
        loop.run_until_complete(signaling.close())






