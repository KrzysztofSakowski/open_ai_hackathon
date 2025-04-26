import React from "react";
import styles from "./menuScreen.module.css";
import { IconThumbDown, IconCheck } from "@tabler/icons-react";
import { ROOT } from "../constants";

interface MenuScreenProps {
  onStory: () => void;
  onActivities: () => void;
  onLesson: () => void;
  onArtProject: () => void;
  onRegenerate: () => void;
  onComplete: () => void;
  imageUrl: string | null;
}

export function MenuScreen({
  onStory,
  onActivities,
  onLesson,
  onArtProject,
  onRegenerate,
  onComplete,
  imageUrl,
}: MenuScreenProps) {
  return (
    <div className={styles.container}>
      <div className={styles.imageSlot}>
        <img
          src={ROOT + "/" + imageUrl}
          alt="Placeholder"
          className={styles.image}
        />
        <button
          className={`${styles.iconButton} ${styles.left}`}
          onClick={onRegenerate}
        >
          <IconThumbDown />
        </button>
        <button
          className={`${styles.iconButton} ${styles.right}`}
          onClick={onComplete}
        >
          <IconCheck />
        </button>
      </div>
      <div className={styles.buttonGrid}>
        <button
          className={`${styles.button} ${styles.story}`}
          onClick={onStory}
        >
          Story
        </button>
        <button
          className={`${styles.button} ${styles.activities}`}
          onClick={onActivities}
        >
          Activities
        </button>
        <button
          className={`${styles.button} ${styles.lesson}`}
          onClick={onLesson}
        >
          Lesson
        </button>
        <button
          className={`${styles.button} ${styles.artProject}`}
          onClick={onArtProject}
        >
          Plan for evening
        </button>
      </div>
    </div>
  );
}
