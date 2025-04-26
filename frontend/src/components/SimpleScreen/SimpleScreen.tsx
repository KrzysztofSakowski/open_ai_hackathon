import React from "react";
import styles from "./simpleScreen.module.css";
import { IconArrowRight } from "@tabler/icons-react";

export interface SimpleScreenProps {
  text: string;
  onNext: () => void;
}

export function SimpleScreen({ text, onNext }: SimpleScreenProps) {
  return (
    <div className={styles.grid}>
      <div className={styles.text}>{text}</div>
      <button className={styles.nextButton} onClick={onNext}>
        <IconArrowRight />
      </button>
    </div>
  );
}
