"use client";

import { useCallback, useState } from "react";
import styles from "./storyScreen.module.css";
import { IconArrowRight } from "@tabler/icons-react";

export interface StoryScreenProps {
  story: string;
  imageUrl: string;
}

export function StoryScreen(props: StoryScreenProps) {
  const [flip] = useState(props.story.length % 2 === 0);

  const elements = [
    <div key="image" className={styles.centeredCell}>
      <img className={styles.image} src={props.imageUrl} />
    </div>,
    <div key="story" className={`${styles.centeredCell} ${styles.storyText}`}>
      {props.story}
    </div>,
  ];

  if (flip) {
    elements.reverse();
  }

  const onNext = useCallback(() => {
    console.log("onNext");
  }, []);

  return (
    <div className={styles.grid}>
      {elements}
      <button className={styles.nextButton} onClick={onNext}>
        <IconArrowRight />
      </button>
    </div>
  );
}
