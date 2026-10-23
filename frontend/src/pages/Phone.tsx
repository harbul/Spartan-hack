/**
 * Resident phone simulator (/phone): phone frame, resident picker, SMS thread,
 * text box, photo attach (resized under 1 MB), and quick replies from
 * data/test_replies.json. Posts to the same /inbound webhook real SMS would use.
 *
 * MOCK (H1-H4): sending adds the reply to this page only.
 * TODO(P1, H4-H6): POST /inbound {phone, text, image_b64}; thread from GET /residents/{id}/messages.
 *
 * Data: GET /residents/{id}/messages, POST /inbound.
 * Implements: PLAN.md §9.2, §6 (SMS channel). Owner: P1 (Frontend and UX).
 */
import { useState } from 'react';
import { mockMessages } from '../api/mock';
import { residents, testReplies } from '../api/seed';
import type { Message } from '../api/types';
import { LANGUAGE_LABEL, clockTime } from '../components/status';

const MAX_PHOTO_BYTES = 1_000_000; // Lambda payload limit (§16)

/** Downscale to 1280 px and re-encode as JPEG until the base64 payload is under 1 MB. */
async function resizePhoto(file: File): Promise<string> {
  const bitmap = await createImageBitmap(file);
  const scale = Math.min(1, 1280 / Math.max(bitmap.width, bitmap.height));
  const canvas = document.createElement('canvas');
  canvas.width = Math.round(bitmap.width * scale);
  canvas.height = Math.round(bitmap.height * scale);
  canvas.getContext('2d')!.drawImage(bitmap, 0, 0, canvas.width, canvas.height);
  for (let quality = 0.85; quality > 0.2; quality -= 0.15) {
    const dataUrl = canvas.toDataURL('image/jpeg', quality);
    if (dataUrl.length * 0.75 < MAX_PHOTO_BYTES) return dataUrl;
  }
  throw new Error('Photo is too large even after resizing');
}

export default function Phone() {
  const [residentId, setResidentId] = useState(residents[0].resident_id);
  const [sent, setSent] = useState<Record<string, Message[]>>({});
  const [text, setText] = useState('');
  const [photo, setPhoto] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const resident = residents.find((r) => r.resident_id === residentId)!;
  const thread = [...mockMessages(residentId, 5), ...(sent[residentId] ?? [])];
  const quickReplies = [...testReplies].sort(
    (a, b) => Number(b.resident_id === residentId) - Number(a.resident_id === residentId),
  );

  const send = () => {
    if (!text.trim() && !photo) return;
    const message: Message = {
      resident_id: residentId,
      ts: new Date().toISOString(),
      direction: 'in',
      channel: 'sms',
      text: text.trim(),
      translation_en: null,
      image_key: photo,
      trace_id: null,
    };
    setSent((s) => ({ ...s, [residentId]: [...(s[residentId] ?? []), message] }));
    setText('');
    setPhoto(null);
  };

  const attach = async (file: File | undefined) => {
    setError(null);
    if (!file) return;
    try {
      setPhoto(await resizePhoto(file));
    } catch (err) {
      setError((err as Error).message);
    }
  };

  return (
    <main className="flex min-h-screen items-start justify-center gap-8 bg-[#f7f4ee] p-6 text-stone-800">
      <div className="flex h-[740px] w-[360px] flex-col overflow-hidden rounded-[2.5rem] border-[10px] border-stone-800 bg-white shadow-xl">
        <header className="border-b border-stone-200 bg-stone-50 px-4 pb-2 pt-4 text-center">
          <select
            value={residentId}
            onChange={(e) => setResidentId(e.target.value)}
            className="w-full rounded border border-stone-300 bg-white px-2 py-1 text-sm"
            aria-label="Resident"
          >
            {residents.map((r) => (
              <option key={r.resident_id} value={r.resident_id}>
                {r.name} ({LANGUAGE_LABEL[r.language]})
              </option>
            ))}
          </select>
          <p className="mt-1 text-xs text-stone-500">{resident.phone} · Santa Clara County</p>
        </header>

        <ol className="flex-1 space-y-2 overflow-y-auto p-3 text-sm">
          {thread.map((m) => (
            <li key={m.ts + m.direction} className={`flex ${m.direction === 'in' ? 'justify-end' : ''}`}>
              <div
                className={`max-w-[80%] rounded-2xl px-3 py-2 ${
                  m.direction === 'in' ? 'bg-blue-500 text-white' : 'bg-stone-200'
                }`}
              >
                {m.image_key?.startsWith('data:') && <img src={m.image_key} alt="" className="mb-1 rounded-lg" />}
                {m.text}
                <div className={`mt-0.5 text-[10px] ${m.direction === 'in' ? 'text-blue-100' : 'text-stone-500'}`}>
                  {clockTime(m.ts)}
                </div>
              </div>
            </li>
          ))}
        </ol>

        <footer className="border-t border-stone-200 p-2">
          {photo && (
            <div className="mb-1 flex items-center gap-2 text-xs">
              <img src={photo} alt="" className="h-10 w-10 rounded object-cover" />
              <button onClick={() => setPhoto(null)} className="text-stone-500 underline">
                remove
              </button>
            </div>
          )}
          {error && <p className="mb-1 text-xs text-red-600">{error}</p>}
          <div className="flex items-center gap-2">
            <label className="cursor-pointer rounded-full bg-stone-100 px-2 py-1 text-lg" title="Attach a photo">
              📷
              <input type="file" accept="image/*" className="hidden" onChange={(e) => attach(e.target.files?.[0])} />
            </label>
            <input
              value={text}
              onChange={(e) => setText(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && send()}
              placeholder="Text message"
              className="min-w-0 flex-1 rounded-full border border-stone-300 px-3 py-1.5 text-sm"
            />
            <button onClick={send} className="rounded-full bg-blue-500 px-3 py-1.5 text-sm text-white">
              Send
            </button>
          </div>
        </footer>
      </div>

      <aside className="w-80">
        <h2 className="mb-1 font-semibold">Quick replies</h2>
        <p className="mb-2 text-xs text-stone-500">
          From data/test_replies.json. This resident's replies come first. Mock: replies stay on this page until
          /inbound is wired (H4-H6).
        </p>
        <ul className="max-h-[680px] space-y-1 overflow-y-auto text-sm">
          {quickReplies.map((r) => (
            <li key={r.reply_id}>
              <button
                onClick={() => {
                  setResidentId(r.resident_id);
                  setText(r.text);
                }}
                className={`w-full rounded border px-2 py-1 text-left hover:bg-white ${
                  r.resident_id === residentId ? 'border-blue-300 bg-blue-50' : 'border-stone-200'
                }`}
              >
                <span className="mr-1 rounded bg-stone-200 px-1 text-[10px] font-semibold">{LANGUAGE_LABEL[r.language]}</span>
                {r.text}
                {r.image && <span className="ml-1 text-xs text-stone-500">+ photo</span>}
                <span className="block text-[11px] text-stone-500">
                  {residents.find((x) => x.resident_id === r.resident_id)?.name} · {r.note}
                </span>
              </button>
            </li>
          ))}
        </ul>
      </aside>
    </main>
  );
}
