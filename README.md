# Sentra 🎨🤖

> Scan a painting, and it comes alive. Ask Mona Lisa why she isn't smiling — and she answers herself.

Built at **HackGT 12: Midnight at the Museum**

🔗 [Devpost](https://devpost.com/software/lumi-h9yu1w)

---

## What it does

Sentra turns static paintings into living conversations. Point your phone at any artwork, ask it a question, and the painting responds — in its own voice, with lip-synced animation.

---

## Pipeline
Image Input
↓
Gemini (artwork identification + character dialogue)
↓
ElevenLabs (text → realistic speech audio)
↓
Wav2Lip (audio → lip-synced video)
↓
React Frontend / FastAPI Backend

Orchestrated via **Cedar OS** for smooth, modular sequencing across all components.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Vision + LLM | Gemini API |
| Text to Speech | ElevenLabs |
| Lip Sync | Wav2Lip |
| Backend | FastAPI (Python) |
| Frontend | React + Next.js |
| Orchestration | Cedar OS |

---

## Built By

- Anika Reddy Gaddam
- Vaidehi Gupta
- Tuhina Parida
- Nidhi Krishna
