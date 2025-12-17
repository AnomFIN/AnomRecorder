"""Audio input utilities: device listing, level meter, recording.

Optional dependency: `sounddevice`.
If not available, these helpers raise `AudioUnavailableError` and the UI will
provide a friendly message to install it.
"""

from __future__ import annotations

import threading
import queue
import wave
from dataclasses import dataclass
from typing import List, Optional

import numpy as np


class AudioUnavailableError(RuntimeError):
    pass


def _require_sd():
    try:
        import sounddevice as sd  # type: ignore
        return sd
    except Exception as exc:  # pragma: no cover - optional dependency
        raise AudioUnavailableError(
            "sounddevice ei ole asennettu. Asenna: pip install sounddevice"
        ) from exc


@dataclass
class AudioDevice:
    id: int
    name: str


def list_input_devices() -> List[AudioDevice]:
    sd = _require_sd()
    devices = []
    for idx, info in enumerate(sd.query_devices()):  # type: ignore
        if int(info.get("max_input_channels", 0)) > 0:
            devices.append(AudioDevice(id=idx, name=str(info.get("name", f"Device {idx}"))))
    return devices


class AudioLevelMeter:
    """Simple audio level meter using RMS amplitude from microphone."""

    def __init__(self, device: Optional[int | str] = None, samplerate: int = 16000, blocksize: int = 1024):
        self.device = device
        self.samplerate = samplerate
        self.blocksize = blocksize
        self._level = 0.0
        self._stream = None
        self._lock = threading.Lock()

    def start(self) -> None:
        sd = _require_sd()

        def callback(indata, frames, time, status):  # pragma: no cover - realtime callback
            if status:
                # ignore for meter
                pass
            # Compute RMS level
            data = np.asarray(indata, dtype=np.float32)
            if data.size:
                rms = float(np.sqrt(np.mean(np.square(data))))
                with self._lock:
                    self._level = rms

        self._stream = sd.InputStream(
            device=self.device,
            channels=1,
            samplerate=self.samplerate,
            blocksize=self.blocksize,
            callback=callback,
        )
        self._stream.start()

    def stop(self) -> None:
        if self._stream is not None:
            try:
                self._stream.stop()
                self._stream.close()
            finally:
                self._stream = None

    def get_level(self) -> float:
        with self._lock:
            return self._level


class AudioRecorder:
    """Background WAV recorder using sounddevice InputStream."""

    def __init__(self, device: Optional[int | str] = None, samplerate: int = 16000):
        self.device = device
        self.samplerate = samplerate
        self.channels = 1
        self._stream = None
        self._thread: Optional[threading.Thread] = None
        self._queue: "queue.Queue[np.ndarray]" = queue.Queue()
        self._running = False

    def start(self, out_path: str) -> None:
        sd = _require_sd()
        self._running = True
        wf = wave.open(out_path, "wb")
        wf.setnchannels(self.channels)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(self.samplerate)

        def callback(indata, frames, time, status):  # pragma: no cover - realtime callback
            if status:
                pass
            # Convert float32 [-1,1] to int16
            data = np.clip(np.asarray(indata)[:, 0], -1.0, 1.0)
            pcm16 = (data * 32767.0).astype(np.int16)
            self._queue.put(pcm16)

        self._stream = sd.InputStream(
            device=self.device,
            samplerate=self.samplerate,
            channels=self.channels,
            callback=callback,
        )

        def writer():  # pragma: no cover - realtime thread
            try:
                while self._running or not self._queue.empty():
                    try:
                        chunk = self._queue.get(timeout=0.1)
                    except queue.Empty:
                        continue
                    wf.writeframes(chunk.tobytes())
            finally:
                try:
                    wf.close()
                except Exception:
                    # Ignore errors closing the wave file; file may already be closed or corrupted
                    pass

        self._thread = threading.Thread(target=writer, daemon=True)
        self._thread.start()
        self._stream.start()

    def stop(self) -> None:
        self._running = False
        if self._stream is not None:
            try:
                self._stream.stop()
                self._stream.close()
            finally:
                self._stream = None
        if self._thread is not None:
            self._thread.join(timeout=1.0)
            self._thread = None

