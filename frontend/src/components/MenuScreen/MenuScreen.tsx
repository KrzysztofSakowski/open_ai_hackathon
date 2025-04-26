import React from "react";
import styles from "./menuScreen.module.css";
import { IconThumbDown, IconCheck } from "@tabler/icons-react";

interface MenuScreenProps {
  onStory: () => void;
  onActivities: () => void;
  onLesson: () => void;
  onArtProject: () => void;
  onRegenerate: () => void;
  onComplete: () => void;
}

export function MenuScreen({ onStory, onActivities, onLesson, onArtProject, onRegenerate, onComplete }: MenuScreenProps) {
  return (
    <div className={styles.container}>
      <div className={styles.imageSlot}>
        <img
          src="https://picsum.photos/seed/menu/800/400"
          alt="Placeholder"
          className={styles.image}
        />
        <button className={`${styles.iconButton} ${styles.left}`} onClick={onRegenerate}>
          <IconThumbDown />
        </button>
        <button className={`${styles.iconButton} ${styles.right}`} onClick={onComplete}>
          <IconCheck />
        </button>
      </div>
      <div className={styles.buttonGrid}>
        <button className={`${styles.button} ${styles.story}`} onClick={onStory}>Story</button>
        <button className={`${styles.button} ${styles.activities}`} onClick={onActivities}>Activities</button>
        <button className={`${styles.button} ${styles.lesson}`} onClick={onLesson}>Lesson</button>
        <button className={`${styles.button} ${styles.artProject}`} onClick={onArtProject}>Art project</button>
      </div>
    </div>
  );
}
