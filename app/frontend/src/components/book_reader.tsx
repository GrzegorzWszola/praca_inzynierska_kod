import { useState, useRef, useLayoutEffect, useEffect, useCallback } from "react";
import type { BookContent, Chapter, Paragraph } from "../types/Book";

type Props = {
  content: BookContent;
  onClose: () => void;
  /** Called whenever the visible + lookahead sentence IDs change */
  onVisibleSentences?: (ids: number[]) => void;
};

// ─── helpers ────────────────────────────────────────────────────────────────

function sentenceIds(paras: Paragraph[]): number[] {
  return paras.flatMap((p) => p.sentences.map((s) => s.id));
}

/** Pack paragraphs into pages that each fit within `maxHeight` px */
function buildPages(paragraphs: Paragraph[], heights: number[], maxHeight: number): Paragraph[][] {
  const PARA_GAP = 20; // matches marginBottom in styles
  const pages: Paragraph[][] = [];
  let current: Paragraph[] = [];
  let used = 0;

  for (let i = 0; i < paragraphs.length; i++) {
    const h = heights[i] + PARA_GAP;
    if (used + h > maxHeight && current.length > 0) {
      pages.push(current);
      current = [paragraphs[i]];
      used = h;
    } else {
      current.push(paragraphs[i]);
      used += h;
    }
  }
  if (current.length > 0) pages.push(current);
  return pages;
}

// ─── component ──────────────────────────────────────────────────────────────

export default function BookReader({ content, onClose, onVisibleSentences }: Props) {
  const { metadata, chapters } = content;
  const [chapterIdx, setChapterIdx] = useState(0);
  const [pageIdx, setPageIdx] = useState(0);
  const [pages, setPages] = useState<Paragraph[][]>([]);
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const mainRef = useRef<HTMLDivElement>(null);
  const measureRef = useRef<HTMLDivElement>(null);

  const chapter: Chapter = chapters[chapterIdx];

  // ── measure + paginate whenever chapter or pane size changes ──────────────
  const paginate = useCallback(() => {
    const main = mainRef.current;
    const measure = measureRef.current;
    if (!main || !measure) return;

    const availableHeight =
      main.clientHeight
      - (measure.querySelector<HTMLElement>("[data-title]")?.offsetHeight ?? 0)
      - 80; // nav row reserve

    const paraEls = Array.from(
      measure.querySelectorAll<HTMLElement>("[data-para-id]")
    );
    const heights = paraEls.map((el) => el.offsetHeight);

    const built = buildPages(chapter.paragraphs, heights, availableHeight);
    setPages(built);
    setPageIdx(0);
  }, [chapter]);

  // run after every render that might change heights
  useLayoutEffect(() => {
    paginate();
  }, [paginate]);

  // ResizeObserver so repagination happens on window resize too
  useEffect(() => {
    const el = mainRef.current;
    if (!el) return;
    const ro = new ResizeObserver(paginate);
    ro.observe(el);
    return () => ro.disconnect();
  }, [paginate]);

  // ── notify parent about sentence IDs ─────────────────────────────────────
  useEffect(() => {
    if (!pages.length || !onVisibleSentences) return;
    // current page + 2 lookahead
    const lookahead = pages.slice(pageIdx, pageIdx + 2).flat();
    onVisibleSentences(sentenceIds(lookahead));
  }, [pages, pageIdx, onVisibleSentences]);

  // ── chapter navigation helpers ────────────────────────────────────────────
  const goToChapter = (idx: number) => {
    setChapterIdx(idx);
    setPageIdx(0);
  };

  const prevPage = () => setPageIdx((i) => Math.max(0, i - 1));
  const nextPage = () => setPageIdx((i) => Math.min(pages.length - 1, i + 1));

  const currentParas = pages[pageIdx] ?? [];

  return (
    <div style={styles.overlay}>
      {/* ── Header ── */}
      <div style={styles.header}>
        <button style={styles.iconBtn} onClick={() => setSidebarOpen((v) => !v)} title="Toggle chapters">
          ☰
        </button>
        <div style={styles.headerTitle}>
          <span style={styles.bookTitle}>{metadata.title}</span>
          <span style={styles.bookAuthor}>by {metadata.author}</span>
        </div>
        <div style={styles.headerMeta}>
          {metadata.num_chapters} chapters · {metadata.num_sentences} sentences
        </div>
        <button style={{ ...styles.iconBtn, marginLeft: "auto" }} onClick={onClose} title="Close reader">
          ✕
        </button>
      </div>

      <div style={styles.body}>
        {/* ── Sidebar ── */}
        {sidebarOpen && (
          <nav style={styles.sidebar}>
            <p style={styles.sidebarHeading}>Chapters</p>
            {chapters.map((ch, i) => (
              <button
                key={ch.chapter_id}
                style={{ ...styles.chapterBtn, ...(i === chapterIdx ? styles.chapterBtnActive : {}) }}
                onClick={() => goToChapter(i)}
              >
                {ch.chapter_id}. {ch.title}
              </button>
            ))}
          </nav>
        )}

        {/* ── Main reading pane ── */}
        <main ref={mainRef} style={styles.main}>

          {/* Invisible measuring container — same width, same typography */}
          <div ref={measureRef} style={styles.measureContainer} aria-hidden="true">
            <h2 data-title style={styles.chapterTitle}>{chapter.title}</h2>
            {chapter.paragraphs.map((para) => (
              <p key={para.paragraph_id} data-para-id={para.paragraph_id} style={styles.paragraph}>
                {para.sentences.map((s) => <span key={s.id}>{s.text} </span>)}
              </p>
            ))}
          </div>

          {/* Visible content */}
          <h2 style={styles.chapterTitle}>{chapter.title}</h2>

          <div style={styles.pageContent}>
            {currentParas.map((para) => (
              <p key={para.paragraph_id} style={styles.paragraph}>
                {para.sentences.map((s) => (
                  <span key={s.id} data-sentence-id={s.id}>
                    {s.text}{" "}
                  </span>
                ))}
              </p>
            ))}
          </div>

          {/* ── Page navigation ── */}
          <div style={styles.navRow}>
            <button style={styles.navBtn} onClick={prevPage} disabled={pageIdx === 0}>
              ← Prev
            </button>
            <span style={styles.navLabel}>
              Ch. {chapterIdx + 1}/{chapters.length} · Page {pageIdx + 1}/{pages.length || 1}
            </span>
            <button style={styles.navBtn} onClick={nextPage} disabled={pageIdx >= pages.length - 1}>
              Next →
            </button>
          </div>
        </main>
      </div>
    </div>
  );
}

// ─── styles ─────────────────────────────────────────────────────────────────

const styles: Record<string, React.CSSProperties> = {
  overlay: {
    position: "fixed",
    inset: 0,
    display: "flex",
    flexDirection: "column",
    background: "#faf8f4",
    color: "#1a1a1a",
    fontFamily: "Georgia, 'Times New Roman', serif",
    zIndex: 1000,
  },
  header: {
    display: "flex",
    alignItems: "center",
    gap: 12,
    padding: "10px 18px",
    background: "#2c2c2c",
    color: "#eee",
    flexShrink: 0,
  },
  headerTitle: {
    display: "flex",
    flexDirection: "column",
    lineHeight: 1.2,
  },
  bookTitle: { fontWeight: "bold", fontSize: 15 },
  bookAuthor: { fontSize: 12, opacity: 0.7 },
  headerMeta: { marginLeft: 24, fontSize: 12, opacity: 0.6, whiteSpace: "nowrap" },
  iconBtn: {
    background: "none",
    border: "none",
    color: "#eee",
    fontSize: 18,
    cursor: "pointer",
    padding: "4px 8px",
    borderRadius: 4,
  },
  body: { display: "flex", flex: 1, overflow: "hidden" },
  sidebar: {
    width: 230,
    flexShrink: 0,
    overflowY: "auto",
    background: "#f0ede8",
    borderRight: "1px solid #ddd",
    padding: "12px 0",
  },
  sidebarHeading: {
    fontSize: 11,
    fontFamily: "sans-serif",
    textTransform: "uppercase",
    letterSpacing: 1,
    color: "#888",
    padding: "0 14px 8px",
    margin: 0,
  },
  chapterBtn: {
    display: "block",
    width: "100%",
    textAlign: "left",
    background: "none",
    border: "none",
    padding: "7px 14px",
    fontSize: 13,
    fontFamily: "Georgia, serif",
    cursor: "pointer",
    color: "#333",
    lineHeight: 1.4,
  },
  chapterBtnActive: {
    background: "#e0d9ce",
    fontWeight: "bold",
    borderLeft: "3px solid #7a5c3a",
    paddingLeft: 11,
  },
  main: {
    flex: 1,
    // no overflow: hidden/auto — we clip via pageContent
    display: "flex",
    flexDirection: "column",
    padding: "32px 60px 0",
    maxWidth: 780,
    margin: "0 auto",
    width: "100%",
    position: "relative", // needed for measureContainer positioning
    boxSizing: "border-box",
  },
  measureContainer: {
    // renders all paragraphs invisibly at real width to measure heights
    position: "absolute",
    top: 0,
    left: 60,
    right: 60,
    visibility: "hidden",
    pointerEvents: "none",
    zIndex: -1,
  },
  chapterTitle: {
    fontSize: 24,
    fontWeight: "bold",
    marginBottom: 20,
    marginTop: 0,
    borderBottom: "1px solid #ccc",
    paddingBottom: 10,
    color: "#3a2a1a",
    flexShrink: 0,
  },
  pageContent: {
    flex: 1,
    overflow: "hidden", // clips the content — no scrollbar, true page feel
  },
  paragraph: {
    marginBottom: 20,
    lineHeight: 1.85,
    fontSize: 17,
    textAlign: "justify",
  },
  navRow: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    padding: "14px 0 20px",
    borderTop: "1px solid #ddd",
    flexShrink: 0,
  },
  navBtn: {
    fontFamily: "Georgia, serif",
    fontSize: 14,
    padding: "8px 18px",
    cursor: "pointer",
    border: "1px solid #bbb",
    borderRadius: 4,
    background: "#fff",
  },
  navLabel: { fontSize: 13, color: "#888" },
};
