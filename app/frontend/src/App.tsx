import './App.css'
import FileUpload from "./components/file_upload"
import BookReader from "./components/book_reader"
import { useCallback, useState } from "react"
import useJobPolling from './components/use_job_polling';
import type { Book, BookContent } from './types/Book';

const API = import.meta.env.VITE_API_URL;

function App() {
  const [books, setBooks] = useState<Book[]>([])
  const [openBook, setOpenBook] = useState<{ jobId: string; content: BookContent } | null>(null)

  const handleUploaded = ({ jobId, filename }: { jobId: string; filename: string }) =>
    setBooks((prev) => [{ jobId, filename, status: "sent", filepath: "" }, ...prev])

  const removeBook = (jobId: string) =>
    setBooks((prev) => prev.filter((b) => b.jobId !== jobId))

  const updateBook = useCallback(
    (jobId: string, patch: Partial<Book>) =>
      setBooks((prev) => prev.map((b) => (b.jobId === jobId ? { ...b, ...patch } : b))),
    []
  );

  const loadContent = async (jobId: string) => {
    const res = await fetch(`${API}/books/${jobId}/content`)
    if (!res.ok) throw new Error(`Error ${res.status}`)
    const content: BookContent = await res.json()
    setOpenBook({ jobId, content })
  }

  const handleVisibleSentences = useCallback((ids: number[]) => {
    if (!openBook) return
    const { jobId } = openBook
    // ids = current page + 2 pages ahead
    console.log("[BookReader] jobId:", jobId, "sentence IDs:", ids)
    // e.g. fetch(`${API}/books/${jobId}/predictions/prefetch`, { method: "POST", body: JSON.stringify({ sentence_ids: ids }) })
  }, [openBook])

  useJobPolling(books, updateBook)

  return (
    <>
      {openBook && (
        <BookReader
          content={openBook.content}
          onClose={() => setOpenBook(null)}
          onVisibleSentences={handleVisibleSentences}
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
