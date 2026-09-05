import io
import time
import wave

import torch
from transformers import AutoModel


MODEL_NAME = "ai4bharat/indic-conformer-600m-multilingual"


def create_test_wav(duration_seconds: float = 5.0) -> bytes:
    """
    Create a valid 16 kHz mono 16-bit WAV containing silence.

    This is only a pipeline/latency test.
    It is NOT a meaningful ASR accuracy test.
    """
    sample_rate = 16_000
    num_samples = int(sample_rate * duration_seconds)

    audio = b"\x00\x00" * num_samples

    buffer = io.BytesIO()

    with wave.open(buffer, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(audio)

    return buffer.getvalue()


def load_wav_tensor(wav_bytes: bytes) -> torch.Tensor:
    """Convert WAV bytes into a float32 tensor."""
    buffer = io.BytesIO(wav_bytes)

    with wave.open(buffer, "rb") as wav:
        frames = wav.readframes(wav.getnframes())

    audio = torch.frombuffer(
        bytearray(frames),
        dtype=torch.int16,
    ).to(torch.float32)

    audio = audio / 32768.0

    # Shape expected by the model: [channels, samples]
    return audio.unsqueeze(0)


def main() -> None:
    print("=" * 60)
    print("AAROH ASR LATENCY BENCHMARK")
    print("=" * 60)

    print("\nCreating test audio...")
    wav_bytes = create_test_wav(duration_seconds=5.0)

    print("Loading audio tensor...")
    wav = load_wav_tensor(wav_bytes)

    print(f"Tensor shape: {tuple(wav.shape)}")
    print(f"Duration: {wav.shape[-1] / 16000:.2f}s")

    print("\nLoading IndicConformer model...")

    load_start = time.perf_counter()

    model = AutoModel.from_pretrained(
        MODEL_NAME,
        trust_remote_code=True,
    )

    load_time = time.perf_counter() - load_start

    print(f"Model load time: {load_time:.2f}s")

    print("\nRunning warm-up inference...")

    with torch.inference_mode():
        _ = model(wav, "hi", "ctc")

    print("Warm-up complete.")

    print("\nRunning benchmark...")

    timings = []

    for i in range(3):
        start = time.perf_counter()

        with torch.inference_mode():
            result = model(wav, "hi", "ctc")

        elapsed = time.perf_counter() - start
        timings.append(elapsed)

        print(
            f"Run {i + 1}: "
            f"{elapsed:.3f}s | "
            f"Result: {result!r}"
        )

    average = sum(timings) / len(timings)

    print("\n" + "=" * 60)
    print("RESULT")
    print("=" * 60)

    print(f"Audio duration:       5.000s")
    print(f"Model load time:      {load_time:.3f}s")
    print(f"Average inference:    {average:.3f}s")
    print(f"Real-time factor:     {average / 5.0:.3f}")

    if average > 5.0:
        print("Status: SLOWER THAN REAL TIME")
    else:
        print("Status: FASTER THAN REAL TIME")


if __name__ == "__main__":
    main()