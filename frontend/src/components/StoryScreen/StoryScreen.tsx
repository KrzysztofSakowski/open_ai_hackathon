"use client";

import { useCallback, useState } from "react";
import styles from "./storyScreen.module.css";
import { IconArrowRight } from "@tabler/icons-react";

export interface StoryScreenProps {
  story: string;
  imageUrl: string | null;
  onNext: () => void;
}

export function StoryScreen({ story, imageUrl, onNext }: StoryScreenProps) {
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

  const handleNext = useCallback(() => {
    onNext();
  }, [onNext]);

  return (
    <div className={styles.grid}>
      {elements}
      <button className={styles.nextButton} onClick={handleNext}>
        <IconArrowRight />
      </button>
    </div>
  );
}
