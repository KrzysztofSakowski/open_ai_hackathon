import { useCallback } from "react";
import styles from "./mapScreen.module.css";
import { IconArrowRight } from "@tabler/icons-react";

export interface MapScreenProps {
  lat: number;
  lng: number;
  onNext: () => void;
  description?: string;
}

export function MapScreen({ lat, lng, onNext, description = "Description goes here." }: MapScreenProps) {
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
          src={`https://maps.google.com/maps?q=${lat},${lng}&z=14&output=embed`}
          allowFullScreen
        />
      </div>
      <div className={styles.description}>{description}</div>
      <button className={styles.nextButton} onClick={handleNext}>
        <IconArrowRight />
      </button>
    </div>
  );
}
