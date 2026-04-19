import os
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from dotenv import load_dotenv
import random
import time
import numpy
from decord import VideoReader, AudioReader
from decord import cpu

def frame_to_gs(frame):
	"""
	Greyscales a single frame and returns the frame
	:param frame: singlular RGB numpy frame
	:return: singuar Greyscaled numoy frame
	"""
	# Vector Calc to convert whole frame in 1 go. Storing frame as unsigned 16 bit int
	return ((frame[:, :, 0] * 0.299) + (frame[:, :, 1] * 0.587) + (frame[:, :, 2] * 0.114)).astype(numpy.uint16)

def frame_to_ascii(frame, colourmap):
	"""
	Converts a greyscaled numoy frame into an ASCII frame
	:param frame: Greyscaled numpy frame
	:param colourmap: numpy array of each ascii character allowed
	:return: ASCIIfied frame as a 1D list of strings
	"""
	# Formula for calcing ascii value stolen from stackoverflow
	# colourmap length subtracted from 1 due to potential index errors.
	# Once frame is converted the colourmap is applied to whole frame
	frame = colourmap[((frame[:] * (len(colourmap)-1)) // 255).astype(numpy.uint8)]
	# Maps entire row to corresponding ascii character and adds that row to the string as 1 long string.
	# frame is stiill in raw bytes so we need to decode it
	return frame.tobytes().decode()

def create_video_obj(video_file: str, w, h):
	"""
	Converts a video file in a processable video object
	:param video_file: File path for video file either relevative or exact.
	:return: decord VideoReader Object
	"""
	with open(video_file, 'rb') as f:
		vr = VideoReader(f, width=w, height=h)
		f.close()
	return vr

# Initializes your app with your bot token and socket mode handler
# Load variables from .env
load_dotenv()

# Now os.environ.get will find your token
app = App(token=os.environ.get("SLACK_BOT_TOKEN"))

@app.message("generate bad apple")
def edit_msg(message, say):
	client = app.client
	width = 80
	height = 24
	client.chat_postMessage(
		channel="stunty",
		text="Starting up"
	)

	print_frame = client.chat_postMessage(
		channel="stunty",
		text="Loading Frame"
	)

	message_ts = print_frame["ts"]
	channel_id = print_frame["channel"]

	ASCII_COLOURMAP = r"%@#*+=-:. "[::-1]
	lut = numpy.frombuffer(ASCII_COLOURMAP.encode(), dtype=numpy.uint8)

	video_obj = create_video_obj("BadApple.mp4", w=width, h=height)
	for i in range(0, len(video_obj), 15):
		frame = video_obj[i].asnumpy()
		frame_vals = frame_to_gs(frame)
		frame = frame_to_ascii(frame_vals, lut)
		frame = '\n'.join(frame[i:i + width] for i in range(0, len(frame), width))


		client.chat_update(
			channel=channel_id,
			ts=message_ts,
			text=f"```{frame}```"
		)
		time.sleep(0.5)


@app.command("/badapple")
def handle_badapple_command(ack, say, command):
	# Acknowledge the command within 3 seconds
	ack()

	# Extract info from the command payload
	user_id = command["user_id"]
	nums = command.get("text", "")

	try:
		width, height = nums.split()
		width = int(width)
		height = int(height)
	except Exception:
		width = 80
		height = 24

	client = app.client
	client.chat_postMessage(
		channel="stunty",
		text="Starting up"
	)

	print_frame = client.chat_postMessage(
		channel="stunty",
		text="Loading Frame"
	)

	message_ts = print_frame["ts"]
	channel_id = print_frame["channel"]

	ASCII_COLOURMAP = r"%@#*+=-:. "[::-1]
	lut = numpy.frombuffer(ASCII_COLOURMAP.encode(), dtype=numpy.uint8)

	video_obj = create_video_obj("BadApple.mp4", w=width, h=height)
	for i in range(0, len(video_obj), 15):
		frame = video_obj[i].asnumpy()
		frame_vals = frame_to_gs(frame)
		frame = frame_to_ascii(frame_vals, lut)
		frame = '\n'.join(frame[i:i + width] for i in range(0, len(frame), width))


		client.chat_update(
			channel=channel_id,
			ts=message_ts,
			text=f"```{frame}```"
		)
		time.sleep(0.5)

# Start your app
if __name__ == "__main__":
	SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()
