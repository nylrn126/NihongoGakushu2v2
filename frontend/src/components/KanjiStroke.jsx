import React, { useEffect, useRef, useState } from "react";

/**
 * KanjiStroke — fetches KanjiVG SVG for a character and animates strokes.
 * KanjiVG data hosted on jsdelivr from github repo KanjiVG/kanjivg@master.
 */
const CDN = "https://cdn.jsdelivr.net/gh/KanjiVG/kanjivg@master/kanji";

function codepointFile(ch) {
  const cp = ch.codePointAt(0).toString(16).padStart(5, "0");
  return `${CDN}/${cp}.svg`;
}

export default function KanjiStroke({ character, size = 220, autoplay = true }) {
  const [status, setStatus] = useState("loading"); // loading|ok|fallback|error
  const [svgHtml, setSvgHtml] = useState("");
  const [playKey, setPlayKey] = useState(0);
  const containerRef = useRef(null);

  useEffect(() => {
    if (!character) return;
    setStatus("loading");
    let cancelled = false;
    fetch(codepointFile(character))
      .then((r) => (r.ok ? r.text() : Promise.reject(new Error("no svg"))))
      .then((txt) => {
        if (cancelled) return;
        // KanjiVG returns XML with DOCTYPE + entity refs. Extract only <svg>…</svg>.
        const start = txt.indexOf("<svg");
        const end = txt.lastIndexOf("</svg>");
        if (start < 0 || end < 0) throw new Error("bad svg");
        let cleaned = txt.slice(start, end + 6)
          .replace(/kvg:[a-zA-Z-]+="[^"]*"/g, "")
          .replace(/<text[^>]*>[^<]*<\/text>/g, "")
          .replace(/xmlns:kvg="[^"]*"/g, "");
        // Ensure viewBox exists and remove fixed width/height so we can scale via CSS
        cleaned = cleaned.replace(/(<svg[^>]*?)\swidth="[^"]*"/i, "$1")
                         .replace(/(<svg[^>]*?)\sheight="[^"]*"/i, "$1");
        setSvgHtml(cleaned);
        setStatus("ok");
      })
      .catch(() => {
        if (!cancelled) setStatus("fallback");
      });
    return () => { cancelled = true; };
  }, [character]);

  useEffect(() => {
    if (status !== "ok" || !containerRef.current || !autoplay) return;
    const paths = containerRef.current.querySelectorAll("path");
    let delay = 0;
    paths.forEach((p) => {
      const len = p.getTotalLength ? p.getTotalLength() : 0;
      p.style.transition = "none";
      p.style.strokeDasharray = `${len}`;
      p.style.strokeDashoffset = `${len}`;
      p.style.stroke = "#17252b";
      p.style.strokeWidth = "3";
      p.style.fill = "none";
      p.style.strokeLinecap = "round";
      p.style.strokeLinejoin = "round";
      requestAnimationFrame(() => {
        p.style.transition = `stroke-dashoffset 900ms ease ${delay}ms`;
        p.style.strokeDashoffset = "0";
      });
      delay += 700;
    });
  }, [status, playKey, svgHtml, autoplay]);

  if (status === "loading") {
    return <div className="kanji-stroke loading" style={{ width: size, height: size }}>…</div>;
  }
  if (status === "fallback" || status === "error") {
    return <div className="kanji-stroke fallback" style={{ width: size, height: size }}>{character}</div>;
  }
  return (
    <div className="kanji-stroke ok" style={{ width: size, height: size }} data-testid={`kanji-stroke-${character}`}>
      <div ref={containerRef} className="kanji-stroke-svg" dangerouslySetInnerHTML={{ __html: svgHtml }} />
      <button className="stroke-replay" onClick={() => setPlayKey(playKey + 1)} data-testid="stroke-replay" aria-label="Putar ulang goresan">↻</button>
    </div>
  );
}
