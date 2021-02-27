#!/usr/bin/env python3

import numpy as np
import cv2
import aiortc
import multiprocessing
import argparse
import asyncio
import logging
import time
import fractions
import json

from av import VideoFrame
from typing import Tuple

from aiortc import RTCPeerConnection, RTCIceCandidate, RTCSessionDescription, MediaStreamTrack
from aiortc.contrib.signaling import add_signaling_arguments, create_signaling, BYE


AUDIO_PTIME = 0.020  # 20ms audio packetization
VIDEO_CLOCK_RATE = 90000
VIDEO_PTIME = 1 / 30  # 30fps
VIDEO_TIME_BASE = fractions.Fraction(1, VIDEO_CLOCK_RATE)



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



class VideoTransformTrack(MediaStreamTrack):
    '''
    Description:
    This class has functions.

    init: to initialize the coordinates of ball.

    next_timestamp: Sending next timestamp of video frame through tuples.
    return: timestamp, video_time_base.
    Raises: It raises MediaStreamError if the video is not alive.

    recv: recieving coordinates from client.
    return: It returns frame.'''

    kind = "video"

    def __init__(self, y, timestep):
        super().__init__()  
        self.frame_num = timestep
        self.image = np.zeros(shape=[512, 512, 3], dtype=np.uint8)

        self.center_coordinates = (32, y)
        self.radius = 20
        self.color = (255, 0, 0)
        self.thickness = -1

    _start: float
    _timestamp: int

    async def next_timestamp(self) -> Tuple[int, fractions.Fraction]:
        if self.readyState != "live":
            raise MediaStreamError

        if hasattr(self, "_timestamp"):
            self._timestamp += int(VIDEO_PTIME * VIDEO_CLOCK_RATE)
            wait = self._start + (self._timestamp / VIDEO_CLOCK_RATE) - time.time()
            await asyncio.sleep(wait)
        else:
            self._start = time.time()
            self._timestamp = 0
        return self._timestamp, VIDEO_TIME_BASE



    async def recv(self):
        pts, time_base = await self.next_timestamp()

        image = cv2.circle(self.image, self.center_coordinates, self.radius, self.color, self.thickness)

        frame = VideoFrame.from_ndarray(image, format="bgr24")
        frame.pts = pts
        frame.time_base = time_base

        return frame


async def make_offer(peer_connection, signaling):

    """
    Description: 

    It makes an offer creating WebRTC connection sending message to client and receiving back again through peer connection through channel
    _log

    """
    y = 32
    timestep = 0
    peer_connection.addTrack(VideoTransformTrack(y, timestep))
    await peer_connection.setLocalDescription(await peer_connection.createOffer())
    await signaling.send(peer_connection.localDescription)
    logging.info("Sent message from server!!!")


    @peer_connection.on("datachannel")
    def on_datachannel(channel):
        channel_log(channel, "-", "created by remote party")

        @channel.on("message")
        def on_message(message):
            channel_log(channel, "<", message)

            if not message.startswith("ping"):
                data = json.loads(message)
                logging.info(data)


    while True:
        y += 10
        y = y % 512
        timestep += 1
        message = await signaling.receive()


        if isinstance(message, RTCSessionDescription):
            if message.type == "answer":
                logging.info("Received answer from client!!!!!")
                await peer_connection.setRemoteDescription(message)


        elif message is BYE:
            print("Exiting")
            break
        
        time.sleep(0.5)
        peer_connection.addTrack(VideoTransformTrack(y, timestep))
        await peer_connection.setLocalDescription(await peer_connection.createOffer())
        await signaling.send(peer_connection.localDescription)

        await signaling._writer.drain()



if __name__ == '__main__':
    args = get_args()

    if args.verbose:
        logging.basicConfig(level=logging.INFO)

    signaling = create_signaling(args)
    logging.debug(signaling)
    peer_connection = RTCPeerConnection()

    offer = make_offer(peer_connection, signaling)

    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(offer)
    except KeyboardInterrupt:
        pass
    finally:
        loop.run_until_complete(peer_connection.close())
        loop.run_until_complete(signaling.close())






