import React, { useEffect, useMemo, useRef, useState } from "react";

/**
 * BabPicker — autocomplete/dropdown for chapters.
 * chapters = [{number, title, title_translation, book}]
 * value = selected number (string) or empty
 * onSelect(number|null, chapter?) — pick or clear
 */
export default function BabPicker({ chapters, value, onSelect, placeholder = "Pilih atau ketik nomor bab" }) {
  const [text, setText] = useState(value ? String(value) : "");
  const [open, setOpen] = useState(false);
  const [highlight, setHighlight] = useState(0);
  const boxRef = useRef(null);

  useEffect(() => {
    const onDoc = (e) => { if (!boxRef.current?.contains(e.target)) setOpen(false); };
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, []);

  useEffect(() => {
    // If parent clears value, sync text
    if (!value) setText("");
  }, [value]);

  const query = text.trim().toLowerCase();
  const matches = useMemo(() => {
    if (!query) return chapters.slice(0, 12);
    return chapters.filter((c) =>
      String(c.number).includes(query) ||
      (c.title || "").toLowerCase().includes(query) ||
      (c.title_translation || "").toLowerCase().includes(query)
    ).slice(0, 12);
  }, [chapters, query]);

  // Auto-switch when typed number exactly matches a chapter
  useEffect(() => {
    const n = Number(query);
    if (Number.isInteger(n) && n > 0) {
      const hit = chapters.find((c) => c.number === n);
      if (hit && String(hit.number) !== String(value)) onSelect(hit.number, hit);
    } else if (!query && value) {
      onSelect(null, null);
    }
    // eslint-disable-next-line
  }, [query, chapters]);

  const pick = (c) => { onSelect(c.number, c); setText(String(c.number)); setOpen(false); };

  const onKey = (e) => {
    if (!open) return;
    if (e.key === "ArrowDown") { setHighlight((h) => Math.min(matches.length - 1, h + 1)); e.preventDefault(); }
    else if (e.key === "ArrowUp") { setHighlight((h) => Math.max(0, h - 1)); e.preventDefault(); }
    else if (e.key === "Enter" && matches[highlight]) { pick(matches[highlight]); e.preventDefault(); }
    else if (e.key === "Escape") { setOpen(false); }
  };

  return (
    <div className="bab-picker" ref={boxRef} data-testid="bab-picker">
      <input
        className="ef-input"
        value={text}
        placeholder={placeholder}
        onFocus={() => setOpen(true)}
        onChange={(e) => { setText(e.target.value); setOpen(true); setHighlight(0); }}
        onKeyDown={onKey}
        data-testid="bab-picker-input"
      />
      {value && (
        <button className="bp-clear" onClick={() => { setText(""); onSelect(null, null); }} aria-label="Hapus pilihan" data-testid="bab-picker-clear">×</button>
      )}
      {open && matches.length > 0 && (
        <ul className="bp-list" data-testid="bab-picker-list">
          {matches.map((c, i) => (
            <li key={c.number} className={i === highlight ? "hi" : ""} onMouseEnter={() => setHighlight(i)} onMouseDown={() => pick(c)} data-testid={`bab-picker-option-${c.number}`}>
              <b>Bab {c.number}</b>
              <span>{c.title}</span>
              <small>{c.title_translation}</small>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
