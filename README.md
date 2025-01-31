# ChatBotRoulette
## A program that allows you to create and naturally converse with different DeepSeek AI personalities with their own voices and even long term memories! 

#### It works using a group of different API's in order to simulate natural conversation as well as possible. 

- DeepSeek: For the main thought process of the bots.
  
- ElevenLabs: To transform the text responses into voice mp3s.
  
- OpenAI: Specifically Whisper, which translates the recordings into text.
  
- PineCone: A vector embedding database in order to simulate long-term memory.

### How does it work?

Simplifying things a bit, the program runs a loop in which it waits for the user to press and hold spacebar to record, or press '0'. In the case of pressing 0 it just changes to another personality from the _personalidades.py_ header, but if you decide to record yourself, things get interesting. The program first sends said recording to OpenAI's Whisper to transform it into text form, it then trasnforms it into an embedding vector in order to look into Pinecone for instances of similar conversation and retreives them. Then we give the AI three things as a prompt: its personality which dictates how it should respond, the results from its "memory" that pass a certain similarity parameter and lastly the last n interactions in order to serve as short-term memory. After receiving the response from DeepSeek, we then use ElevenLabs in order to create the mp3 files of the response. Each personality has its own voice, which is again stored in the _personalidades.py_ header. Finally after playing said file the program loops and awaits for the user to press space or '0'.

### Installation and Usage
- First of all, there are a bunch of libraries that have to be installed in order to run this program. Mainly all the API's and ffmpeg which is the piece of software that we use to record and play audio. So just go ahead and download them using pip, in the case of ffmpeg it is a bit trickier than that, but there are a lot of tutorials such as: https://phoenixnap.com/kb/ffmpeg-windows
  
- Second, you have to create accounts for all the API we are using and get your developer keys, it is pretty straightforward, but each one has a _Getting Started_ guide within its documentation if necessary. Sadly, some of them do need you to put credits into them, mainly OpenAI, but since we only use it for whisper it consumes a small amount. As for the rest, I only put in 2 dollars into my DeepSeek account and from all the testing I had to do to create this, it has only lowered to 1.96. PineCone offers an amazing free package so no money is needed there. Lastly ElevenLabs does offer a free package, but it has almost no credits and they do run out quickly specially when using the eleven_multilingual_v2 model, I'd recommend to use their flash model but it won't allow custom voices.
  
- After that,  I'd recommend the user to create new chatbots since mine are in spanish and made to be humorous. They are located in the _personalidades.py_ file, so go ahead and delete them or alter them however you want! The voices will not work off the bat since they are custom made by my account, but there are a lot of voices offered by ElevenLabs and making your own is incredibly easy. While you are here, you may notice another cycle list named colorRGB, I used that to differentiate between the personalities since I ported the project to a rasperry pi, but you can go ahead and delete that.

### Conclution
I started this project in order to help me learn more about AI implementation into software and robotics. I even implemented it into its own standalone device using a raspberry pi zero 2w. I hope more people realize just how easier and cheaper working with AI has become, specially thanks to DeepSeek. Hopefully this repository proves useful and makes working with APIs a bit more bearable for beginners, I do want to apologize for the excesive spanglish if it makes things a bit confusing :P
