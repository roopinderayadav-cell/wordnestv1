"""Wordnest Jobs - video interview recorder.

Runs in the candidate's browser:
  - speaks the question aloud with the browser's built-in voice (free, no server needed)
  - shows the camera, records the answer (camera + microphone) up to a time limit
  - lets the candidate watch it back, record once more, then submit
Works on https sites (Streamlit Cloud) and on http://localhost. The browser asks for camera permission.
"""
import base64

import streamlit as st

CSS = """
.vi { font-family: inherit; border:1px solid #DDE2DC; border-radius:16px; background:#fff; padding:18px; color:#1C2321; }
.vi .who { display:flex; align-items:center; gap:10px; font-size:13px; color:#4A5551; margin-bottom:8px; }
.vi .dot { width:34px; height:34px; border-radius:50%; background:#1F6F5C; color:#fff; display:flex; align-items:center;
  justify-content:center; font-weight:700; }
.vi .q { font-size:22px; line-height:1.35; font-family: 'Source Serif 4', Georgia, serif; margin:4px 0 14px; }
.vi video { width:100%; max-width:560px; aspect-ratio:16/9; background:#1C2321; border-radius:12px; display:block; object-fit:cover; }
.vi .row { display:flex; flex-wrap:wrap; gap:8px; margin-top:12px; align-items:center; }
.vi button { font: inherit; font-size:14px; font-weight:600; border-radius:999px; padding:10px 16px; min-height:44px;
  border:1px solid #C9D0C8; background:#fff; color:#1C2321; cursor:pointer; }
.vi button.primary { background:#1F6F5C; border-color:#1F6F5C; color:#fff; }
.vi button.rec { background:#8B1E2B; border-color:#8B1E2B; color:#fff; }
.vi button:disabled { opacity:.45; cursor:not-allowed; }
.vi [hidden] { display:none !important; }
.vi .status { font-size:13.5px; color:#4A5551; margin-top:8px; min-height:20px; }
.vi .timer { font-variant-numeric: tabular-nums; font-weight:700; color:#8B1E2B; }
"""

JS = """
export default function(component) {
  const { data, setTriggerValue, parentElement } = component;
  const root = document.createElement('div');
  root.className = 'vi';
  root.innerHTML = `
    <div class="who"><div class="dot">W</div><div><b>Wordnest interviewer</b><br><span class="qn"></span></div></div>
    <div class="q"></div>
    <video class="cam" autoplay muted playsinline></video>
    <video class="review" controls playsinline hidden></video>
    <div class="row">
      <button class="play">Hear the question</button>
      <button class="start primary" disabled>Start recording</button>
      <button class="stop rec" hidden>Stop</button>
      <button class="redo" hidden>Record again</button>
      <button class="use primary" hidden>Use this answer</button>
      <span class="timer"></span>
    </div>
    <div class="status">Starting your camera...</div>`;
  parentElement.appendChild(root);
  const $ = (s) => root.querySelector(s);
  $('.q').textContent = data.question;
  $('.qn').textContent = `Video question ${data.index + 1} of ${data.total} · up to ${Math.round(data.max_seconds / 60)} min`;
  const cam = $('.cam'), review = $('.review'), status = $('.status'), timer = $('.timer');
  let stream = null, rec = null, chunks = [], blob = null, mime = '', started = 0, tick = null, retakes = data.retakes;

  function speak() {
    try {
      window.speechSynthesis.cancel();
      const u = new SpeechSynthesisUtterance(data.question);
      u.lang = data.lang || 'en-IN';
      u.rate = 0.95;
      const v = window.speechSynthesis.getVoices().find(v => v.lang === u.lang) ||
                window.speechSynthesis.getVoices().find(v => v.lang && v.lang.startsWith('en'));
      if (v) u.voice = v;
      window.speechSynthesis.speak(u);
    } catch (e) { /* no speech available: the question is on screen */ }
  }
  function pickMime() {
    const opts = ['video/webm;codecs=vp8,opus', 'video/webm', 'video/mp4'];
    for (const o of opts) { if (window.MediaRecorder && MediaRecorder.isTypeSupported(o)) return o; }
    return '';
  }
  function stopTimer() { if (tick) { clearInterval(tick); tick = null; } }
  function stopRecording() {
    if (rec && rec.state !== 'inactive') rec.stop();
    stopTimer();
  }

  navigator.mediaDevices.getUserMedia({ video: { width: 640, height: 360 }, audio: true })
    .then(s => {
      stream = s; cam.srcObject = s;
      $('.start').disabled = false;
      status.textContent = 'Camera ready. Listen to the question, then press Start recording.';
      setTimeout(speak, 400);
    })
    .catch(err => {
      status.textContent = 'Camera or microphone is blocked. Allow access in your browser (lock icon next to the address) and reload.';
      setTriggerValue('error', String(err && err.name || err));
    });

  $('.play').onclick = speak;
  $('.start').onclick = () => {
    window.speechSynthesis.cancel();
    chunks = []; blob = null; mime = pickMime();
    try {
      rec = new MediaRecorder(stream, mime ? { mimeType: mime, videoBitsPerSecond: 350000, audioBitsPerSecond: 64000 } : {});
    } catch (e) { rec = new MediaRecorder(stream); }
    mime = rec.mimeType || mime || 'video/webm';
    rec.ondataavailable = (e) => { if (e.data && e.data.size) chunks.push(e.data); };
    rec.onstop = () => {
      blob = new Blob(chunks, { type: mime.split(';')[0] });
      review.src = URL.createObjectURL(blob);
      cam.hidden = true; review.hidden = false;
      $('.stop').hidden = true; $('.use').hidden = false;
      $('.redo').hidden = retakes <= 0;
      status.textContent = 'Watch your answer. When you are happy, press Use this answer.';
      timer.textContent = '';
    };
    rec.start(1000);
    started = Date.now();
    $('.start').hidden = true; $('.stop').hidden = false; $('.play').disabled = true;
    status.textContent = 'Recording... look at the camera and speak clearly.';
    tick = setInterval(() => {
      const left = data.max_seconds - Math.floor((Date.now() - started) / 1000);
      timer.textContent = `● ${Math.floor(left / 60)}:${String(left % 60).padStart(2, '0')} left`;
      if (left <= 0) stopRecording();
    }, 250);
  };
  $('.stop').onclick = stopRecording;
  $('.redo').onclick = () => {
    retakes -= 1;
    review.hidden = true; cam.hidden = false;
    $('.use').hidden = true; $('.redo').hidden = true; $('.start').hidden = false; $('.play').disabled = false;
    status.textContent = 'Ready to record again.';
  };
  $('.use').onclick = () => {
    if (!blob) return;
    $('.use').disabled = true; $('.redo').hidden = true;
    status.textContent = 'Saving your answer...';
    const seconds = Math.round((Date.now() - started) / 1000);
    const reader = new FileReader();
    reader.onload = () => {
      const b64 = String(reader.result).split(',')[1];
      setTriggerValue('recorded', { index: data.index, mime: mime.split(';')[0], b64: b64, seconds: seconds,
                                    retakes_used: data.retakes - retakes });
    };
    reader.readAsDataURL(blob);
  };

  return () => {
    stopTimer();
    try { window.speechSynthesis.cancel(); } catch (e) {}
    if (rec && rec.state !== 'inactive') { try { rec.stop(); } catch (e) {} }
    if (stream) stream.getTracks().forEach(t => t.stop());
  };
}
"""

_recorder = st.components.v2.component("wordnest_video_answer", css=CSS, js=JS)


def record_answer(question, index, total, key, max_seconds=120, retakes=1, lang="en-IN"):
    """Show the recorder. Returns (video_bytes, mime, seconds) once the candidate submits, ('error', msg) on camera
    failure, or None while they are still recording."""
    res = _recorder(data={"question": question, "index": index, "total": total, "max_seconds": max_seconds,
                          "retakes": retakes, "lang": lang},
                    key=key, on_recorded_change=lambda: None, on_error_change=lambda: None)
    rec = getattr(res, "recorded", None)
    if rec and rec.get("index") == index and rec.get("b64"):
        return base64.b64decode(rec["b64"]), rec.get("mime") or "video/webm", int(rec.get("seconds") or 0)
    err = getattr(res, "error", None)
    if err:
        return "error", str(err)
    return None
