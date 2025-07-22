import os
import numpy as np
import torch
from faster_whisper import WhisperModel
import torchaudio

MODEL_NAME = "medium"
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"[디버그] fast whisper 모델 로드 (device: {device})")
model = WhisperModel(MODEL_NAME, device=device, compute_type="float16" if device=="cuda" else "float32")

def extract_lyrics(audio_path: str) -> list[str]:
    try:
        print(f"[디버그] 오디오 파일 로드 시작: {audio_path}")
        waveform, sr = torchaudio.load(audio_path)
        print(f"[디버그] torchaudio로 로드: shape={waveform.shape}, sr={sr}")
        # mono 변환
        if waveform.shape[0] > 1:
            waveform = waveform.mean(dim=0, keepdim=True)
            print(f"[디버그] mono 변환 후 shape: {waveform.shape}")
        # 리샘플링
        target_sr = 16000
        if sr != target_sr:
            resampler = torchaudio.transforms.Resample(orig_freq=sr, new_freq=target_sr)
            waveform = resampler(waveform)
            sr = target_sr
            print(f"[디버그] 리샘플링 후 shape: {waveform.shape}, sr: {sr}")
        audio = waveform.squeeze().numpy().astype(np.float32)
        print(f"[디버그] float32 변환 후 audio shape: {audio.shape}, dtype: {audio.dtype}, sr: {sr}")
        # 임시 wav 파일로 저장 (faster-whisper는 파일 경로 입력이 더 간편)
        import soundfile as sf
        tmp_wav = f"{os.path.splitext(audio_path)[0]}_tmp.wav"
        sf.write(tmp_wav, audio, 16000)
        print(f"[디버그] 임시 wav 파일 저장: {tmp_wav}")
        print(f"[디버그] fast whisper 추론 시작 (device: {device})")
        segments, info = model.transcribe(tmp_wav, language='ko', beam_size=5, best_of=5, temperature=0.0, vad_filter=True)
        output_lines = []
        for seg in segments:
            start = getattr(seg, 'start', 0)
            end = getattr(seg, 'end', 0)
            text = getattr(seg, 'text', '').strip()
            output_lines.append(f"[{start:.2f} ~ {end:.2f}] {text}")
        # 파일 저장
        base, _ = os.path.splitext(os.path.basename(audio_path))
        txt_path = f"{base}.txt"
        with open(txt_path, "w", encoding="utf-8") as f:
            for line in output_lines:
                f.write(line + "\n")
        print(f"[디버그] 가사+타임스탬프가 {txt_path} 파일로 저장되었습니다.")
        print(output_lines)
        # 임시 파일 삭제
        if os.path.exists(tmp_wav):
            os.remove(tmp_wav)
        return output_lines
    except Exception as e:
        print(f"[에러] {e}")
        return [] 