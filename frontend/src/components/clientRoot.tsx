"use client";

import {
  QueryClient,
  QueryClientProvider,
  useMutation,
  useQuery,
} from "@tanstack/react-query";
import styles from "./promptScreen.module.css";
import React, { use, useEffect, useRef, useState } from "react";
import { IconMicrophone, IconMicrophoneFilled } from "@tabler/icons-react";
import { StoryScreen } from "./StoryScreen/StoryScreen";
import { WelcomeScreen } from "./WelcomeScreen/WelcomeScreen";
import { MenuScreen } from "./MenuScreen/MenuScreen";
import { SimpleScreen } from "./SimpleScreen/SimpleScreen";
import { MapScreen } from "./MapScreen/MapScreen";
import { v4 as uuid } from "uuid";

const ROOT = "http://localhost:8000";
const queryClient = new QueryClient();

export function ClientRoot() {
  return (
    <QueryClientProvider client={queryClient}>
      <InnerComponent />
    </QueryClientProvider>
  );
}

type AppState =
  | { state: "welcome" }
  | { state: "prompt" }
  | { state: "story"; step: number }
  | { state: "activities" }
  | { state: "lesson" }
  | { state: "artProject" }
  | { state: "menu" };

export function InnerComponent() {
  const [state, setAppState] = useState<AppState>({ state: "welcome" });
  const [convoId, setConvoId] = useState<string | null>(null);

  if (state.state === "welcome") {
    return (
      <WelcomeScreen
        onStart={() => {
          async function fetchConvoId() {
            try {
              const storedId = localStorage.getItem("convoId");
              let convoIdToSend: string;
              if (storedId) {
                convoIdToSend = storedId;
              } else {
                convoIdToSend = uuid();
                localStorage.setItem("convoId", convoIdToSend);
              }

              const response = await fetch(ROOT + "/start", {
                method: "POST",
                headers: {
                  "Content-Type": "application/json",
                },
                body: JSON.stringify({ conversation_id: convoIdToSend }),
              });

              if (!response.ok) throw new Error("Convo failed");
              const data = await response.json();
              console.log(data);
              setConvoId(data.conversation_id);
              console.log("Convo started successfully");
            } catch (error) {
              console.error("Convo failed", error);
            }
          }
          fetchConvoId().then(() => {
            setAppState({ state: "prompt" });
          });
        }}
      />
    );
  }

  if (state.state === "prompt") {
    return <PromptScreen convoId={convoId!} />;
  }

  if (state.state === "story") {
    return (
      <StoryScreen
        imageUrl="http://picsum.photos/300/300"
        story="hello"
        onNext={() => setAppState({ state: "menu" })}
      />
    );
  }

  if (state.state === "activities") {
    return (
      <MapScreen
        lat={37.7749}
        lng={-122.4194}
        onNext={() => setAppState({ state: "menu" })}
      />
    );
  }

  if (state.state === "lesson") {
    return (
      <SimpleScreen
        text="This is a demo lesson screen."
        onNext={() => setAppState({ state: "menu" })}
      />
    );
  }

  if (state.state === "artProject") {
    return (
      <SimpleScreen
        text="This is a demo art project screen."
        onNext={() => setAppState({ state: "menu" })}
      />
    );
  }

  if (state.state === "menu") {
    return (
      <MenuScreen
        onStory={() => setAppState({ state: "story", step: 0 })}
        onActivities={() => setAppState({ state: "activities" })}
        onLesson={() => setAppState({ state: "lesson" })}
        onArtProject={() => setAppState({ state: "artProject" })}
        onRegenerate={() => {
          console.log("Regenerate clicked");
        }}
        onComplete={() => {
          console.log("Complete clicked");
        }}
      />
    );
  }

  return null;
}

export interface PromptScreenProps {
  convoId: string;
}

const useRecorder = (options: { convoId: string }) => {
  let mediaRecorderRef = useRef<MediaRecorder | null>(null);

  let recordedChunks: Blob[] = [];

  const [isRecording, setIsRecording] = useState(false);

  const mutation = useMutation({
    mutationFn: async (audioBlob: Blob) => {
      console.log(audioBlob);
      console.log(options.convoId);

      const playback = false;
      if (playback) {
        const audioUrl = URL.createObjectURL(audioBlob);
        const audio = new Audio(audioUrl);
        audio.play(); // or save the blob
      }

      const formData = new FormData();
      formData.append("audio", audioBlob, "recording.webm");
      try {
        const response = await fetch(
          ROOT + "/message/audio/" + options.convoId,
          {
            method: "POST",
            body: formData,
          }
        );
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
  const { convoId } = props;

  const [prompt, setPrompt] = useState<string | null>(null);
  const recorder = useRecorder({ convoId });

  useEffect(() => {
    if (!convoId) return;
    async function fetchAudio() {
      try {
        const response = await fetch(ROOT + "/state/" + convoId, {
          method: "GET",
        });
        if (!response.ok) throw new Error("Audio failed");
        const data = await response.json();
        if (!data) return;
        const audio = data.audio_base64;
        setPrompt(data.text);
        const audioUrl = "data:audio/webm;base64," + audio;
        const audioElement = new Audio(audioUrl);

        audioElement.play();
        console.log("Audio played successfully");
      } catch (error) {
        console.error("Audio failed", error);
      }
    }
    const interval = setInterval(() => {
      fetchAudio();
    }, 1000);
    return () => {
      clearInterval(interval);
    };
  }, [convoId]);

  return (
    <div className={styles.container}>
      {prompt === null ? (
        <div className={styles.loaderContainer}>
          <div className={styles.loader} />
        </div>
      ) : (
        <>
          <div className={styles.message}>{prompt}</div>
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
        </>
      )}
    </div>
  );
}
