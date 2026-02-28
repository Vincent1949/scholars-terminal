import pyttsx3

# Test if pyttsx3 works
engine = pyttsx3.init()
voices = engine.getProperty('voices')

print(f"Found {len(voices)} voices:")
for i, voice in enumerate(voices):
    print(f"{i+1}. {voice.name}")

# Test speaking
engine.say("Hello! This is a voice test. Can you hear me?")
engine.runAndWait()
print("Voice test complete!")