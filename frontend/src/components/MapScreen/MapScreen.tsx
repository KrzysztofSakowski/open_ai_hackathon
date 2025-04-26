import { useCallback } from "react";
import styles from "./mapScreen.module.css";
import { IconArrowRight } from "@tabler/icons-react";
import { FinalOutput } from "../schemas";

export interface MapScreenProps {
  event: FinalOutput["text"]["event"];
  onNext: () => void;
}

export function MapScreen({ event, onNext }: MapScreenProps) {
  const handleNext = useCallback(() => {
    onNext();
  }, [onNext]);

  return (
    <div className={styles.grid}>
      <div className={styles.mapContainer}>
        <iframe
          title="map"
          width="100%"
          height="100%"
          frameBorder="0"
          src={`https://maps.google.com/maps?q=${encodeURIComponent(
            event.address
          )}&z=14&output=embed`}
          allowFullScreen
        />
      </div>
      <div className={styles.description}>
        <div>
          <h2>{event.name}</h2>
          <p>{event.description}</p>
          <p>{event.justification}</p>
          <p>{event.estimated_cost}</p>
        </div>
        <a
          href={event.url}
          target="_blank"
          rel="noopener noreferrer"
          className={styles.visitButton}
        >
          Visit Website
        </a>
      </div>
      <button className={styles.nextButton} onClick={handleNext}>
        <IconArrowRight />
      </button>
    </div>
  );
}
