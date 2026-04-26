import os
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from dotenv import load_dotenv
import random
import time
import numpy
import cv2 as cv
import edge_tts
import asyncio
from moviepy import VideoFileClip, vfx, AudioFileClip
import re
import threading

load_dotenv()
app = App(token=os.environ.get("SLACK_BOT_TOKEN"))


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
	frame = colourmap[((frame[:] * (len(colourmap) - 1)) // 255).astype(numpy.uint8)]
	# Maps entire row to corresponding ascii character and adds that row to the string as 1 long string.
	# frame is stiill in raw bytes so we need to decode it
	return frame.tobytes().decode()


def create_video_obj(video_file: str):
	vr = cv.VideoCapture(video_file)
	vr.set(cv.CAP_PROP_FPS, 2)
	return vr


def handle_mention(event, client, say):
	print("Recieved: " + event["text"])
	channel_id = event.get("channel")
	thread_ts = event.get("thread_ts")
	user_id = event.get("user")

	if "slopify" not in event["text"].split():
		print("No slopify")
		return
	if not thread_ts:
		client.chat_postEphemeral(
			channel=channel_id,
			user=user_id,  # ID of the user who should see the message
			thread_ts=thread_ts,  # Keeps the ephemeral message inside the thread
			text="Mention me inside of the thread you want to slopify"
		)
		return

	result = client.conversations_replies(channel=event["channel"], ts=thread_ts)
	messages = result.get("messages", [])
	return messages, thread_ts, user_id


async def speak(text, name="output"):
	communicate = edge_tts.Communicate(text)
	await communicate.save(f"{name}.mp3")


def upload_video(client, user_id, file_path, thread_ts):
	dm = client.conversations_open(users=user_id)
	try:
		dm_channel_id = dm["channel"]["id"]
		client.files_upload_v2(
			channel=dm_channel_id,  # DMs to the user directly
			file=file_path,
			title=f"Slopified video {thread_ts}"
		)
	except Exception as e:
		client.chat_postMessage(channel=user_id,
								text=f"I'm to lazy to create actual error messages so here is what slack said went wrong.\n"
									 f"{e}")
		return
	os.remove(file_path)


@app.event("app_mention")
def handle_slop_mention(event, client, say):
	messages, thread_ts, user_id = handle_mention(event, client, say)
	client.chat_postMessage(channel=user_id,
							text="generating your video be patient as it can take a while")
	text = ""
	for message in messages:
		p = r'https?://\S+|www\.\S+'
		n_url = str(re.sub(p, "", message["text"]))
		parts = re.split(r"<@(U[A-Z0-9]+)>", n_url)
		for i in range(0, len(parts)):
			if re.match(r"U[A-Z0-9]+", parts[i]):
				parts[i] = client.users_info(user=parts[i])["user"]["profile"]["display_name"]
		msg = "".join(parts)
		text += msg + ". "

	print("turning to audio")
	name = f"{thread_ts}{random.randint(1000, 9999)}"
	asyncio.run(speak(text, name))

	print("turing to video")
	audio_clip = AudioFileClip(f"{name}.mp3")

	mypath = "slop_videos"
	onlyfiles = [f for f in os.listdir(mypath) if os.path.isfile(os.path.join(mypath, f))]
	file_i = random.randint(0, len(onlyfiles) - 1)

	video_clip = (
		VideoFileClip(f"{mypath}/{onlyfiles[file_i]}")
		.with_volume_scaled(0)
	).with_effects([vfx.Loop(duration=audio_clip.duration)])

	video_clip.audio = audio_clip.subclipped(0, video_clip.duration)
	video_clip.write_videofile(f"{name}.mp4")
	os.remove(f"{name}.mp3")

	threading.Thread(target=upload_video, args=(client, user_id, f"{name}.mp4", thread_ts)).start()


@app.command("/slopify")
def handle_slop_command(ack, say, command):
	print("Triggered")
	ack()

	client = app.client

	user_id = command["user_id"]
	url = command.get("text", "")
	client.chat_postMessage(channel=user_id,
							text="generating your video be patient as it can take a while")
	channel_match = re.search(r'/archives/(\w+)/', url)
	channel_id = channel_match.group(1) if channel_match else None

	# Extract Message TS
	ts_match = re.search(r'/p(\d{16})', url)
	if ts_match:
		raw_ts = ts_match.group(1)
		# Format: 1621234567.000123
		thread_ts = f"{raw_ts[:-6]}.{raw_ts[-6:]}"

	try:
		result = client.conversations_replies(channel=channel_id, ts=thread_ts)
		messages = result.get("messages", [])
	except Exception as e:
		client.chat_postMessage(channel=user_id,
								text=f"I'm to lazy to create actual error messages so here is what slack said went wrong.\n"
									 f"{e}")
		return

	text = ""
	for message in messages:
		p = r'https?://\S+|www\.\S+'
		n_url = str(re.sub(p, "", message["text"]))
		parts = re.split(r"<@(U[A-Z0-9]+)>", n_url)
		for i in range(0, len(parts)):
			if re.match(r"U[A-Z0-9]+", parts[i]):
				parts[i] = client.users_info(user=parts[i])["user"]["profile"]["display_name"]
		msg = "".join(parts)
		text += msg + ". "

	print("turning to audio")
	name = f"{thread_ts}{random.randint(1000, 9999)}"
	asyncio.run(speak(text, name))

	print("turing to video")
	audio_clip = AudioFileClip(f"{name}.mp3")

	mypath = "slop_videos"
	onlyfiles = [f for f in os.listdir(mypath) if os.path.isfile(os.path.join(mypath, f))]
	file_i = random.randint(0, len(onlyfiles) - 1)

	video_clip = (
		VideoFileClip(f"{mypath}/{onlyfiles[file_i]}")
		.with_volume_scaled(0)
	).with_effects([vfx.Loop(duration=audio_clip.duration)])

	video_clip.audio = audio_clip.subclipped(0, video_clip.duration)
	video_clip.write_videofile(f"{name}.mp4")
	os.remove(f"{name}.mp3")

	threading.Thread(target=upload_video, args=(client, user_id, f"{name}.mp4", thread_ts)).start()


@app.event("message")
def handle_message_events(ack):
	# Simply acknowledge to stop the "unhandled request" warning
	pass


@app.command("/generatecat")
def handle_cat_gen_command(ack, say, command):
	# Acknowledge the command within 3 seconds
	t1 = time.time()
	ack()

	print("recieved!")
	client = app.client

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

	mypath = "cat"
	onlyfiles = [f for f in os.listdir(mypath) if os.path.isfile(os.path.join(mypath, f))]
	file_i = random.randint(0, len(onlyfiles) - 1)
	img = cv.imread(f"cat/{onlyfiles[file_i]}")
	img = cv.resize(img, (width, height))

	ASCII_COLOURMAP = r"@%#*+=-:. "[::-1]
	lut = numpy.frombuffer(ASCII_COLOURMAP.encode(), dtype=numpy.uint8)
	img_vals = frame_to_gs(img)
	img = frame_to_ascii(img_vals, lut)
	img = [(img[i:i + width]) for i in range(0, len(img), width)]
	i = 0
	length = 0
	msg = ""
	try:
		while i < len(img):
			length += width
			if length > 3000:
				say(text=f"```{msg}```")
				msg = ""
				length = 0
			msg += "\n" + img[i]
			i += 1
		say(text=f"```{msg}```")

	except Exception as e:
		say(text=f"```{e}```")
	print(time.time() - t1)


@app.command("/badapple")
def handle_badapple_command(ack, say, command):
	# Acknowledge the command within 3 seconds
	ack()

	client = app.client

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

	print_frame = say(text="```Loading Frame```")

	message_ts = print_frame["ts"]
	channel_id = print_frame["channel"]

	ASCII_COLOURMAP = r"%@#*+=-:."[::-1]
	lut = numpy.frombuffer(ASCII_COLOURMAP.encode(), dtype=numpy.uint8)

	video_obj = create_video_obj("BadApple_1fps.mp4")
	frame_count = int(video_obj.get(cv.CAP_PROP_FRAME_COUNT))
	while True:
		ret, frame = video_obj.read()

		if not ret:
			break

		frame = cv.resize(frame, (width, height))
		frame = cv.cvtColor(frame, cv.COLOR_BGR2RGB)

		frame_vals = frame_to_gs(frame)
		frame = frame_to_ascii(frame_vals, lut)
		frame = '\n'.join(frame[i:i + width] for i in range(0, len(frame), width))

		client.chat_update(
			channel=channel_id,
			ts=message_ts,
			text=f"```{frame}```"
		)
		time.sleep(1)


# Start your app
if __name__ == "__main__":
	SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()
