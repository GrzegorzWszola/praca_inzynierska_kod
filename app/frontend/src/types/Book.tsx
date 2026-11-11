export type JobStatus = "sent" | "parsing" | "predicting" | "done" | "error";
export type Book = {
  jobId: string
  filename: string
  filepath: string | null
  status: JobStatus
}

export type Sentence = { id: number; text: string }
export type Paragraph = { paragraph_id: number; sentences: Sentence[] }
export type Chapter = { chapter_id: number; title: string; paragraphs: Paragraph[] }
export type BookContent = {
  metadata: { title: string; author: string; num_chapters: number; num_sentences: number }
  chapters: Chapter[]
}

export type Prediction = { label: string | null; certainty: number; margin?: number };

export type Track = {
  id: string;
  file: string;
  title?: string;
};

export type Manifest = Record<string, Track[]>;

export type ManifestEntry = {
  filename: string;
  id: string;
  category: string;
  path?: string;
};