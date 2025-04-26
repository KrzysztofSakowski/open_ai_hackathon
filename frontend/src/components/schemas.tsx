import { z } from "zod";

export const AudioPromptSchema = z.object({
  type: z.literal("audio"),
  text: z.string(),
  audio_base64: z.string(),
  format: z.literal("mp3"),
});

export const FinalOutputSchema = z.object({
  type: z.literal("output"),
  format: z.literal("text"),
  text: z.object({
    storyboard: z.object({
      narration: z.string().array(),
      images: z.string().array(),
    }),
    story: z.string(),
    story_image_paths: z.string().array(),
    lesson: z.string(),
    reasoning: z.string(),
    plan_for_evening: z.string(),
    // event
  }),
});

export type AudioPrompt = z.infer<typeof AudioPromptSchema>;
export type FinalOutput = z.infer<typeof FinalOutputSchema>;
