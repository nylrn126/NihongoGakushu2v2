import React from "react";

/**
 * Ruby (furigana) renderer.
 * Segments look like: [{ text: "私", reading: "わたし" }, { text: "は", reading: null }]
 */
export function Ruby({ segments = [], size = "base", className = "" }) {
  const sizeCls = size === "lg" ? "text-2xl md:text-3xl" : size === "sm" ? "text-base" : "text-xl";
  return (
    <span className={`ja-ruby ${sizeCls} ${className}`}>
      {segments.map((seg, i) =>
        seg.reading ? (
          <ruby key={i}>
            {seg.text}
            <rt>{seg.reading}</rt>
          </ruby>
        ) : (
          <span key={i}>{seg.text}</span>
        )
      )}
    </span>
  );
}

export function plainText(segments = []) {
  return segments.map((s) => s.text).join("");
}
