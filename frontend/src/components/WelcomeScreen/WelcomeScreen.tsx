export interface WelcomeScreenProps {
  onStart: () => void;
}

import styles from "./welcomeScreen.module.css";

export function WelcomeScreen(props: WelcomeScreenProps) {
  return (
    <div className={styles.container}>
      <button className={styles.startButton} onClick={props.onStart}>
        Welcome
      </button>
    </div>
  );
}
