import { useCallback, useEffect, useRef, useState } from "react";
import type { ManifestEntry, Prediction } from "../types/Book";

type Props = {
  prediction: Prediction | null;
  manifest: ManifestEntry[];
  musicBase: string;
};

export default function MusicPlayer(props: Props) {
  const { emotion, track, playing, volume, toggle, setVolume, next } =
    useMusicEngine(props);
 
  return (
    <div className="music-player">
      <div className="music-info">
        <div className="music-mood">Mood: {emotion ?? "—"}</div>
        <div className="music-track">
          {track ? `Track ${track.id}` : `No track for "${emotion}"`}
        </div>
      </div>
 
      <div className="music-controls">
        <button className="btn btn-primary btn-sm" onClick={toggle}>
          {playing ? "Pause" : "Play"}
        </button>
        <button className="btn btn-ghost btn-sm" onClick={next}>
          Next
        </button>
        <input
          type="range"
          min={0}
          max={1}
          step={0.01}
          value={volume}
          onChange={(e) => setVolume(Number(e.target.value))}
          aria-label="Volume"
        />
      </div>
    </div>
  );
}

function useMusicEngine({ prediction, manifest, musicBase }: Props) {
  const [emotion, setEmotion] = useState<string | null>(null);
  const [track, setTrack] = useState<ManifestEntry | null>(null);
  const [playing, setPlaying] = useState(false);
  const [volume, setVolume] = useState(0.7);

  const audioRef = useRef<HTMLAudioElement | null>(null);
  const outgoingRef = useRef<HTMLAudioElement | null>(null);
  const fadeRef = useRef<number | null>(null);
  const timerRef = useRef<number | null>(null);
  const emotionRef = useRef<string | null>(null)
  const targetRef = useRef<string | null>(null);
  const lastSwitchRef = useRef(0);
  const indexRef = useRef<Record<string, number>>({});

  const manifestRef = useRef(manifest);
  manifestRef.current = manifest;
  const volumeRef = useRef(volume);
  volumeRef.current = volume;
  const crossfadeRef = useRef<(e: string, ms?: number, mood?: boolean) => void>(() => {});

  const pickTrack = (label: string): ManifestEntry | null => {
    const list = manifestRef.current.filter((t) => t.category === label);
    if (!list.length) return null;
    const i = indexRef.current[label] ?? Math.floor(Math.random() * list.length);
    indexRef.current[label] = (i + 1) % list.length;
    return list[i % list.length];
  };

  const predictionRef = useRef(prediction);
  predictionRef.current = prediction;

  const startLabel = () => {
    const label = predictionRef.current?.label ?? "neutral";
    const exists = manifestRef.current.some((t) => t.category === label);
    return exists ? label : "neutral";
  };

  const crossfadeTo = useCallback((label: string, ms = 3000, moodChange = true) => {
    const t = pickTrack(label);
    if (!t) return;

    const prev = audioRef.current;
    outgoingRef.current?.pause();
    if (fadeRef.current) clearInterval(fadeRef.current);

    const el = new Audio(`${musicBase}/music/${t.category}/${encodeURIComponent(t.filename)}`);
    el.volume = 0;
    el.play().catch(() => {});
    outgoingRef.current = prev;

    const steps = 30;
    let i = 0;
    fadeRef.current = window.setInterval(() => {
      i++;
      const x = i / steps;
      el.volume = Math.sin((x * Math.PI) / 2) * volumeRef.current;
      if (prev) prev.volume = Math.cos((x * Math.PI) / 2) * volumeRef.current;
      if (i >= steps) {
        clearInterval(fadeRef.current!);
        fadeRef.current = null;
        prev?.pause();
        outgoingRef.current = null;
      }
    }, ms / steps);

    // Next song from the same label 
    let chained = false;
    el.addEventListener("timeupdate", () => {
      if (chained || !el.duration) return;
      if (el.duration - el.currentTime <= 4) {
        chained = true;
        if (audioRef.current === el) crossfadeRef.current(label, 4000, false);
      }
    });

    audioRef.current = el;
    emotionRef.current = label;
    if (moodChange) lastSwitchRef.current = Date.now();
    setEmotion(label);
    setTrack(t);
  }, [musicBase]);

  crossfadeRef.current = crossfadeTo;

  // Prediction reaction
  useEffect(() => {
    if (!prediction?.label) return;
    const { label, certainty, margin = 1 } = prediction;
    targetRef.current = label;
    console.log("pred:", { label, certainty, margin, playing, current: emotionRef.current });

    if (!playing) {
      if (!audioRef.current) setEmotion(label);
      return;
    }
    if (emotionRef.current === null) return crossfadeTo(startLabel(), 2000, false);

    if (label === emotionRef.current) {
      if (timerRef.current) clearTimeout(timerRef.current);
      return;
    }
    if (!(certainty >= 0.4 && margin >= 0.1)) return;

    const wait = 20000 - (Date.now() - lastSwitchRef.current);
    const ms = 8000 - Math.min(1, (certainty - 0.4) / 0.6) * 6000;
    if (timerRef.current) clearTimeout(timerRef.current);

    if (wait <= 0) crossfadeTo(label, ms);
    else timerRef.current = window.setTimeout(() => {
      if (emotionRef.current !== label) crossfadeTo(label, ms);
    }, wait);
  }, [prediction]);

  const toggle = useCallback(() => {
    if (playing) {
      audioRef.current?.pause();
      outgoingRef.current?.pause();
      if (timerRef.current) clearTimeout(timerRef.current);
      setPlaying(false);
      return;
    }
    setPlaying(true);
    if (audioRef.current) audioRef.current.play().catch(() => {});
    else crossfadeTo(startLabel(), 2000, false);
  }, [playing, crossfadeTo]);

  const next = useCallback(() => {
    if (emotionRef.current) {
      setPlaying(true);
      crossfadeTo(emotionRef.current, 1500, false);
    }
  }, [crossfadeTo]);

  useEffect(() => {
    if (audioRef.current && !fadeRef.current) audioRef.current.volume = volume;
  }, [volume]);

  useEffect(() => () => {
    if (fadeRef.current) clearInterval(fadeRef.current);
    if (timerRef.current) clearTimeout(timerRef.current);
    audioRef.current?.pause();
    outgoingRef.current?.pause();
  }, []);

  return { emotion, track, playing, volume, toggle, setVolume, next };
}