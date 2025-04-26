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
    event: z.object({
      address: z.string(),
      description: z.string(),
      estimated_cost: z.string(),
      justification: z.string(),
      name: z.string(),
      url: z.string(),
      url_to_book_tickets: z.string(),
    }),
    storyboard: z.object({
      narration: z.string().array(),
      images: z.string().array(),
    }),
    story: z.string(),
    story_images: z.object({
      image_paths: z.string().array(),
    }),
    story_audio: z.string().array(),
    story_videos: z.string().array().optional(),
    lesson: z.string(),
    reasoning: z.string(),
    plan_for_evening: z.string(),
  }),
});

export type AudioPrompt = z.infer<typeof AudioPromptSchema>;
export type FinalOutput = z.infer<typeof FinalOutputSchema>;
