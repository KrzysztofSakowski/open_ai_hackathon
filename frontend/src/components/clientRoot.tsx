"use client";

import {
  QueryClient,
  QueryClientProvider,
  useMutation,
  useQuery,
} from "@tanstack/react-query";
import styles from "./promptScreen.module.css";
import { useRef, useState } from "react";
import { IconMicrophone, IconMicrophoneFilled } from "@tabler/icons-react";

const queryClient = new QueryClient();

export function ClientRoot() {
  return (
    <QueryClientProvider client={queryClient}>
      <InnerComponent />
    </QueryClientProvider>
  );
}

export function InnerComponent() {
  const q = useQuery({
    queryKey: ["story"],
    queryFn: async () => {
      const res = await fetch("https://jsonplaceholder.typicode.com/todos/1");
      const json = res.json();
      return json;
    },
  });

  return (
    <PromptScreen question="How are you today? Could you tell me something about yourself?" />
  );
}

export interface PromptScreenProps {
  question?: string;
}

const useRecorder = () => {
  let mediaRecorderRef = useRef<MediaRecorder | null>(null);

  let recordedChunks: Blob[] = [];

  const [isRecording, setIsRecording] = useState(false);

  const mutation = useMutation({
    mutationFn: async (audioBlob: Blob) => {
      console.log(audioBlob);

      const playback = false;
      if (playback) {
        const audioUrl = URL.createObjectURL(audioBlob);
        const audio = new Audio(audioUrl);
        audio.play(); // or save the blob
      }

      const formData = new FormData();
      formData.append("audio", audioBlob, "recording.webm");
      try {
        const response = await fetch("/upload-endpoint", {
          method: "POST",
          body: formData,
        });
        if (!response.ok) throw new Error("Upload failed");
        console.log("Upload successful");
      } catch {
        console.error("Upload failed");
      }
    },
  });

  async function startRecording() {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

    setIsRecording(true);

    recordedChunks = [];

    mediaRecorderRef.current = new MediaRecorder(stream);
    const mediaRecorder = mediaRecorderRef.current;

    mediaRecorder.ondataavailable = (event) => {
      if (event.data.size > 0) recordedChunks.push(event.data);
    };

    mediaRecorder.onstop = () => {
      setIsRecording(false);
      const audioBlob = new Blob(recordedChunks, { type: "audio/webm" });
      mutation.mutateAsync(audioBlob);
    };

    mediaRecorder.start();
  }

  function stopRecording() {
    mediaRecorderRef.current?.stop();
  }

  return { isRecording, startRecording, stopRecording };
};

export function PromptScreen(props: PromptScreenProps) {
  const recorder = useRecorder();
  return (
    <div>
      <div className={styles.message}>{props.question}</div>
      <div className={styles.recordContainer}>
        {recorder.isRecording ? (
          <button
            className={`${styles.roundButton} ${styles.active}`}
            onClick={recorder.stopRecording}
          >
            <IconMicrophoneFilled />
          </button>
        ) : (
          <button
            className={`${styles.roundButton}`}
            onClick={recorder.startRecording}
          >
            <IconMicrophone />
          </button>
        )}
      </div>
    </div>
  );
}
