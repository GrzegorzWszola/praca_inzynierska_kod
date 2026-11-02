import { useEffect, useRef } from "react"
import type { Book } from "../types/Book"

const API = import.meta.env.VITE_API_URL
const isActive = (b: Book) => b.status === "sent" || b.status === "parsing" || b.status === "predicting"

export default function useJobPolling(books: Book[], update: (jobId: string, patch: Partial<Book>) => void) {
    const booksRef = useRef(books)
    booksRef.current = books

    const hasActive = books.some(isActive)
    useEffect(() => {
        if (!hasActive) return

        const controller = new AbortController()
        let timer: number
        let delay = 1000

        const tick = async () => {
        const active = booksRef.current.filter(isActive)

            await Promise.all(
                active.map(async (b) => {
                    try {
                        const res = await fetch(`${API}/books/${b.jobId}/status`, {
                            signal: controller.signal,
                        })
                        if (res.status === 404) {
                            update(b.jobId, { status: "error" })
                            return
                        }
                        if (!res.ok) return
                        update(b.jobId, await res.json())
                    } catch {}
                })
            )

            if (!controller.signal.aborted) {
                delay = Math.min(delay * 1.5, 5000)
                timer = window.setTimeout(tick, delay)
            }
        }

        timer = window.setTimeout(tick, delay)
        return () => {
            controller.abort()
            clearTimeout(timer)
        }
    }, [hasActive, update])
}
