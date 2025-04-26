"use client";

import { useCallback, useState, useEffect } from "react";
import styles from "./storyScreen.module.css";
import { IconArrowRight, IconVolume2 } from "@tabler/icons-react";

export interface StoryScreenProps {
  story: string;
  audioUrl: string | null;
  imageUrl: string | null;
  onNext: () => void;
}

export function StoryScreen({
  story,
  audioUrl,
  imageUrl,
  onNext,
}: StoryScreenProps) {
  const elements = [
    <div key="image" className={styles.centeredCell}>
      {imageUrl && <img className={styles.image} src={imageUrl} />}
    </div>,
    <div key="story" className={`${styles.centeredCell} ${styles.storyText}`}>
      {story}
    </div>,
  ];

  if (story.length % 2 === 0) {
    elements.reverse();
  }

  const [audioEl, setAudioEl] = useState<HTMLAudioElement | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);

  useEffect(() => {
    if (!audioUrl) {
      setAudioEl(null);
      setIsPlaying(false);
      return;
    }
    const a = new Audio(audioUrl);
    a.onended = () => setIsPlaying(false);
    setAudioEl(a);
    return () => {
      a.pause();
      setIsPlaying(false);
    };
  }, [audioUrl]);

  const handleNext = useCallback(() => {
    onNext();
  }, [onNext]);

  const handlePlayAudio = useCallback(() => {
    if (!audioEl) return;
    if (isPlaying) {
      audioEl.pause();
      setIsPlaying(false);
    } else {
      audioEl.play();
      setIsPlaying(true);
    }
  }, [audioEl, isPlaying]);

  return (
    <div className={styles.grid}>
      {audioUrl && (
        <button
          onClick={handlePlayAudio}
          className={`${styles.audioButton} ${
            isPlaying ? styles.audioPlaying : ""
          }`}
        >
          {isPlaying ? <IconVolume2 /> : <IconVolume2 />}
        </button>
      )}
      {elements}
      <button className={styles.nextButton} onClick={handleNext}>
        <IconArrowRight />
      </button>
    </div>
  );
}
