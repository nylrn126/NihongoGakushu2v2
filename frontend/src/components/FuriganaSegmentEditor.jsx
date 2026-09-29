import React from "react";
import { Ruby } from "@/components/Ruby";

/**
 * FuriganaSegmentEditor — edit segments = [{text, reading}]
 * text = plain kanji/kana chunk; reading = furigana on top (nullable for kana-only chunks)
 */
export default function FuriganaSegmentEditor({ value = [], onChange, testid = "furi" }) {
  const rows = value.length ? value : [{ text: "", reading: null }];

  const update = (i, patch) => {
    const next = rows.map((r, idx) => idx === i ? { ...r, ...patch } : r);
    onChange(next);
  };
  const addRow = () => onChange([...rows, { text: "", reading: null }]);
  const removeRow = (i) => onChange(rows.filter((_, idx) => idx !== i).length ? rows.filter((_, idx) => idx !== i) : [{ text: "", reading: null }]);

  return (
    <div className="furi-editor" data-testid={testid}>
      <div className="furi-preview">
        <Ruby segments={rows.filter((r) => r.text)} />
      </div>
      {rows.map((r, i) => (
        <div className="furi-row" key={i}>
          <input
            className="ef-input" placeholder="Teks (kanji / kana)" value={r.text}
            onChange={(e) => update(i, { text: e.target.value })}
            data-testid={`${testid}-text-${i}`}
          />
          <input
            className="ef-input" placeholder="Bacaan (furigana; kosong utk kana)"
            value={r.reading || ""}
            onChange={(e) => update(i, { reading: e.target.value || null })}
            data-testid={`${testid}-reading-${i}`}
          />
          <button className="del-btn" onClick={() => removeRow(i)} type="button" aria-label="Hapus" data-testid={`${testid}-remove-${i}`}>×</button>
        </div>
      ))}
      <button className="furi-add" onClick={addRow} type="button" data-testid={`${testid}-add`}>+ Tambah potongan furigana</button>
    </div>
  );
}
