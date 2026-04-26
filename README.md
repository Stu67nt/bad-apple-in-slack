## Stunty

It does as it says on the tin. You can watch Bad Apple be played on any Slack channel stunty is in!

I decided to make this because I wanted to challenge myself to make a project within the span of 1 show and tell. 
I succeeded!

### Usage
Visit #stunty on the Hack Club Slack to test the commands!

#### Bad Apple
Run the command /badapple for it to run in 80x24 resolution.  
To customise the resolution, add the extra arguments [width] [height] to the end. (This will fail for resolutions with more than 3000 characters, for example, 110x30 will fail, but 90x70 won't)

#### Cat Photos
To generate a cat image, run /generatecat for it to run in 80x24 resolution.  
To customise the resolution, add the extra arguments [width] [height] to the end. This command works for any resolution, but to be able to properly see larger resolution images, you may need to 
zoom out (on Slack web) or have a big monitor.

#### Generate slop
To generate slop videos of a thread, either ping @stunty and say slopify like "@stunty pls slopify this thread" WITHIN THE THREAD or in a main channel run the command /slopify [url]. If the bot is not in the channel where the thread you want to slopify is, it will not work and return an error message. Make sure to add it to the channel where the thread you want to slopify is first.

### AI
I used gemini and claude to help me with regex for filtering some inputs and to help with getting and sending messages with the slack api. 
