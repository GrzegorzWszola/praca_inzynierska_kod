import './App.css'
import FileUpload, { formatFileName } from "./components/file_upload"
import BookReader from "./components/book_reader"
import { useCallback, useEffect, useRef, useState } from "react"
import useJobPolling from './components/use_job_polling';
import type { Book, BookContent, ManifestEntry, Prediction } from './types/Book';
import { api } from './api';
import MusicPlayer from './components/music_player';

const MUSIC_BASE = import.meta.env.VITE_MUSIC_ORIGIN ?? "/music";
const MANIFEST = import.meta.env.VITE_MANIFEST;

function App() {
  const [books, setBooks] = useState<Book[]>([])
  const [openBook, setOpenBook] = useState<{ jobId: string; content: BookContent } | null>(null)
  const debounceTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [prediction, setPrediction] = useState<Prediction | null>(null);
  const [manifest, setManifest] = useState<ManifestEntry[]>([]);

  useEffect(() => {
    let cancelled = false

    api("/books/mine")
      .then((r) => {
        if (!r.ok) throw new Error(`Error ${r.status}`)
        return r.json()
      })
      .then((list: { job_id: string; name: string; status: string }[]) => {
        if (cancelled) return
        setBooks(
          list.map((b) => ({
            jobId: b.job_id,
            filename: formatFileName(b.name),
            status: b.status as Book["status"],
            filepath: "",
          }))
        )
      })
      .catch(console.error)

    return () => { cancelled = true }
  }, [])

  // Download manifest
  useEffect(() => {
    let cancelled = false;

    fetch(MANIFEST)
      .then((r) => {
        if (!r.ok) throw new Error(`Manifest error ${r.status}`);
        return r.json();
      })
      .then((data: ManifestEntry[]) => {
        if (!cancelled) setManifest(data);
      })
      .catch(console.error);

    return () => { cancelled = true };
  }, []);

  const handleUploaded = ({ jobId, filename }: { jobId: string; filename: string }) =>
    setBooks((prev) => [{ jobId, filename, status: "sent", filepath: "" }, ...prev])

  const removeBook = async (jobId: string) => {
      try {
        const res = await api(`/books/${jobId}`, { method: "DELETE" })
        if (!res.ok && res.status !== 404) throw new Error(`Error ${res.status}`)
        setBooks((prev) => prev.filter((b) => b.jobId !== jobId))
      } catch (e) {
        console.error(e)
      }
    }

  const updateBook = useCallback(
    (jobId: string, patch: Partial<Book>) =>
      setBooks((prev) => prev.map((b) => (b.jobId === jobId ? { ...b, ...patch } : b))),
    []
  );

  const loadContent = async (jobId: string) => {
    const res = await api(`/books/${jobId}/content`)
    if (!res.ok) throw new Error(`Error ${res.status}`)
    const content: BookContent = await res.json()
    setOpenBook({ jobId, content })
  }

  const handleVisibleSentences = useCallback((ids: number[]) => {
    if (!openBook) return;
    const { jobId } = openBook;

    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }

    debounceTimerRef.current = setTimeout(async () => {
      try {
        const res = await api(`/predictions/${jobId}`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ sentence_ids: ids })
        });

        if (!res.ok) {
          if (res.status !== 404) throw new Error(`Error ${res.status}`);
          return;
        }
        setPrediction(await res.json());
      } catch (error) {
        console.error("Prefetch error:", error);
      }
    }, 2000);

  }, [openBook]);

  useJobPolling(books, updateBook)

  return (
    <>
      {openBook && (
        <BookReader
          content={openBook.content}
          onClose={() => {
            if (debounceTimerRef.current) clearTimeout(debounceTimerRef.current);
            setOpenBook(null);
            setPrediction(null);
          }}
          onVisibleSentences={handleVisibleSentences}
        />
      )}
      {openBook && (
        <MusicPlayer 
          prediction={prediction} 
          manifest={manifest} 
          musicBase={MUSIC_BASE}
        />
      )}

      <div className="page">
        <header className="header">
          <h1>Book Reader</h1>
          <p>Upload an EPUB file to parse and read.</p>
        </header>

        <FileUpload onUploaded={handleUploaded} />

        {books.length > 0 ? (
          <>
            <div className="section-heading">Books</div>
            <ul className="book-list">
              {books.map((b) => (
                <li key={b.jobId} className="book-card">
                  <div className="book-info">
                    <div className="book-name">{b.filename}</div>
                    <div className="book-meta">
                      <span className={`badge badge-${b.status}`}>{b.status}</span>
                      <span>Job: {b.jobId}</span>
                    </div>
                  </div>

                  <div className="book-actions">
                    <button
                      className="btn btn-primary btn-sm"
                      onClick={() => loadContent(b.jobId)}
                      disabled={b.status !== "done"}
                    >
                      Read
                    </button>
                    <button
                      className="btn btn-ghost btn-sm"
                      onClick={() => removeBook(b.jobId)}
                    >
                      Remove
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          </>
        ) : (
          <div className="empty-state">No books uploaded yet.</div>
        )}
      </div>
    </>
  )
}

export default App
