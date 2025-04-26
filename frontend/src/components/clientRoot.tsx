"use client";

import {
  QueryClient,
  QueryClientProvider,
  useMutation,
  useQuery,
} from "@tanstack/react-query";
import styles from "./promptScreen.module.css";
import React, { useEffect, useRef, useState } from "react";
import { IconMicrophone, IconMicrophoneFilled } from "@tabler/icons-react";

const ROOT = "http://localhost:8000";
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

const useRecorder = (options: {convoId: string | undefined; setConvoId: React.Dispatch<React.SetStateAction<string | undefined>>}) => {
  let mediaRecorderRef = useRef<MediaRecorder | null>(null);

  let recordedChunks: Blob[] = [];

  const [isRecording, setIsRecording] = useState(false);

  useEffect(() => {
    async function fetchConvoId() {
      try {
        const response = await fetch(ROOT + "/start", {
          method: "POST",
        });
        if (!response.ok) throw new Error("Convo failed");
        const data = await response.json();
        console.log(data);
        options.setConvoId(data.conversation_id);
        console.log("Convo started successfully");
      } catch (error) {
        console.error("Convo failed", error);
      }
    }
    fetchConvoId();
  }, []);

  const mutation = useMutation({
    mutationFn: async (audioBlob: Blob) => {
      console.log(audioBlob);
      console.log(options.convoId)

      const playback = false;
      if (playback) {
        const audioUrl = URL.createObjectURL(audioBlob);
        const audio = new Audio(audioUrl);
        audio.play(); // or save the blob
      }

      const formData = new FormData();
      formData.append("audio", audioBlob, "recording.webm");
      try {
        const response = await fetch(ROOT + "/message/audio/" + options.convoId, {
          method: "POST",
          body: formData,
        });
        if (!response.ok) throw new Error("Upload failed");
        console.log("Upload successful");
      } catch (error) {
        console.error("Upload failed", error);
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

  const [convoId, setConvoId] = useState<string | undefined>(undefined);
  const recorder = useRecorder({convoId, setConvoId});
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
