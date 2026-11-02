import { useState } from "react"
import type { JobStatus } from "../types/Book";

const API = import.meta.env.VITE_API_URL;
type Props = {
  onUploaded: (result: { jobId: string, filename: string, filepath: string, status: JobStatus }) => void;
};

export default function FileUpload({ onUploaded }: Props) {
    const [file, setFile] = useState<File | null>(null)
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState("")

    const formatFileName = (filename: string): string => {
        if (!filename) return '';
        const nameWithoutExt = filename.substring(0, filename.lastIndexOf('.')) || filename;
        const withSpaces = nameWithoutExt.replace(/[-_]/g, ' ');
        const formatted = withSpaces
            .split(' ')
            .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
            .join(' ');

        return formatted;
    };

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setFile(e.target.files?.[0] ?? null)
        setError("")
    };

    const handleUpload = async () => {
        if (!file) return

        const formData = new FormData()
        formData.append("file", file)

        try{
            setLoading(true)
            setError("")
            
            const res = await fetch(`${API}/books/upload_epub`, {
                method: "POST",
                body: formData,
            })
            if (!res.ok) throw new Error(`Error: ${res.status}`)
            const data: { job_id: string } = await res.json();
            onUploaded({ jobId: data.job_id, filename: formatFileName(file.name), filepath: "", status: "sent" });
            setFile(null);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Unknown error");
        } finally {
            setLoading(false);
        }
    }

    return (
        <div className="upload-card">
            <div className="upload-row">
                <label className="upload-label">
                    <span>Choose EPUB file</span>
                    <input type="file" accept=".epub" onChange={handleChange} />
                </label>
                {file && (
                    <span className="upload-filename">
                        {file.name} ({(file.size / 1024).toFixed(1)} KB)
                    </span>
                )}
                <button
                    className="btn btn-primary"
                    onClick={handleUpload}
                    disabled={!file || loading}
                >
                    {loading ? "Uploading..." : "Upload"}
                </button>
            </div>
            {error && <p className="upload-error">{error}</p>}
        </div>
    )
}