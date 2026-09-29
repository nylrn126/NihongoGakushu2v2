import React, { useEffect, useRef, useState } from "react";
import { Ruby } from "@/components/Ruby";

/**
 * Duolingo-style word-order picker.
 * tokens = [{text, reading}]. value = list of picked token indices (into original shuffled tokens).
 * onChange(nextIndices). Renders furigana on all tiles.
 */
export default function SusunPicker({ tokens, value, onChange, qid, correctLength, disabled = false }) {
  const [animKey, setAnimKey] = useState(0);
  const used = new Set(value);
  const bank = tokens.map((t, i) => ({ t, i })).filter((x) => !used.has(x.i));

  const add = (i) => { if (disabled) return; onChange([...value, i]); setAnimKey(animKey + 1); };
  const removeAt = (pos) => { if (disabled) return; onChange(value.filter((_, idx) => idx !== pos)); };

  const targetSlots = correctLength || tokens.length;
  const slotsArr = Array.from({ length: targetSlots });

  return (
    <div className="susun-duo" data-testid={`susun-picker-${qid}`}>
      <div className="susun-answer">
        {slotsArr.map((_, idx) => {
          const pickedIdx = value[idx];
          const tok = pickedIdx != null ? tokens[pickedIdx] : null;
          return (
            <button
              key={idx}
              className={`susun-slot ${tok ? "filled" : "empty"}`}
              onClick={() => tok && removeAt(idx)}
              disabled={disabled || !tok}
              data-testid={`susun-slot-${qid}-${idx}`}
              aria-label={tok ? `Hapus ${tok.text}` : "Slot kosong"}
            >
              {tok ? <Ruby segments={[tok]} size="sm" /> : <span className="dash">＿</span>}
            </button>
          );
        })}
      </div>
      <div className="susun-divider" />
      <div className="susun-bank" data-testid={`susun-bank-${qid}`}>
        {bank.map(({ t, i }) => (
          <button
            key={i}
            className="susun-tile"
            onClick={() => add(i)}
            disabled={disabled}
            data-testid={`susun-tile-${qid}-${i}`}
          >
            <Ruby segments={[t]} size="sm" />
          </button>
        ))}
        {bank.length === 0 && <span className="muted small">Semua kata sudah dipakai</span>}
      </div>
    </div>
  );
}
