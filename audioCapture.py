import pyaudio
import wave

# Konfiguration für die Audioaufnahme
FORMAT = pyaudio.paInt16  # Aufnahmeformat
CHANNELS = 1  # Anzahl der Kanäle (Stereo)
RATE = 48000  # Abtastrate (Hz)
CHUNK = 1024  # Anzahl der Frames pro Puffer
RECORD_SECONDS = 5  # Dauer der Aufnahme in Sekunden
OUTPUT_FILENAME = "recording.wav"


class ImageCapture:
    def __init__(self) -> None:
        self.audio = pyaudio.PyAudio()
        self.list_input_device()
        # Öffnen des Audio-Streams für die Aufnahme
        stream = self.audio.open(
            format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK
        )

        print("Aufnahme gestartet...")

        frames = []

        # Audio aufnehmen und in frames speichern
        for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
            data = stream.read(CHUNK)
            frames.append(data)

        print("Aufnahme beendet.")

        # Audio-Stream schließen
        stream.stop_stream()
        stream.close()
        self.audio.terminate()

        # Audio in eine WAV-Datei speichern
        with wave.open(OUTPUT_FILENAME, "wb") as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(self.audio.get_sample_size(FORMAT))
            wf.setframerate(RATE)
            wf.writeframes(b"".join(frames))

        print(f"Audio wurde in {OUTPUT_FILENAME} gespeichert.")

    def list_input_device(self):
        nDevices = self.audio.get_device_count()
        print("Found input devices:")
        for i in range(nDevices):
            deviceInfo = self.audio.get_device_info_by_index(i)
            devName = deviceInfo["name"]
            print(f"Device ID {i}: {devName}")
