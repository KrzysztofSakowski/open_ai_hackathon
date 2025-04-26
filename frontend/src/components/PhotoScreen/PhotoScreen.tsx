"use client";

import React, { useEffect, useRef, useState } from "react";
import styles from "./photoScreen.module.css";

interface PhotoScreenProps {
  onCapture: (dataUrl: string) => void;
  onSkip: () => void;
}

export function PhotoScreen({ onCapture, onSkip }: PhotoScreenProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [stream, setStream] = useState<MediaStream | null>(null);

  useEffect(() => {
    async function enableCamera() {
      try {
        const mediaStream = await navigator.mediaDevices.getUserMedia({
          video: true,
        });
        if (videoRef.current) {
          videoRef.current.srcObject = mediaStream;
          videoRef.current.play();
        }
        setStream(mediaStream);
      } catch (err) {
        console.error("Error accessing camera", err);
      }
    }
    enableCamera();
    return () => {
      stream?.getTracks().forEach((track) => track.stop());
    };
  }, []);

  function handleCapture() {
    if (!canvasRef.current || !videoRef.current) return;
    const context = canvasRef.current.getContext("2d");
    const video = videoRef.current;
    if (context) {
      canvasRef.current.width = video.videoWidth;
      canvasRef.current.height = video.videoHeight;
      context.drawImage(video, 0, 0);
      const dataUrl = canvasRef.current.toDataURL("image/png");
      onCapture(dataUrl);
    }
  }

  return (
    <div className={styles.container}>
      <video ref={videoRef} className={styles.video} />
      <canvas ref={canvasRef} style={{ display: "none" }} />
      <div className={styles.buttonGroup}>
        <button onClick={onSkip} className={styles.skipButton}>
          Skip
        </button>
        <button onClick={handleCapture} className={styles.captureButton}>
          Capture Selfie
        </button>
      </div>
    </div>
  );
}
