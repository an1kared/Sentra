# Sentra 🎨🤖

> Scan a painting, and it comes alive. Ask Mona Lisa why she isn't smiling — and she answers herself.

Built at **HackGT 12: Midnight at the Museum**

🔗 [Devpost](https://devpost.com/software/lumi-h9yu1w)

---

## What it does

Sentra turns static paintings into living conversations. Point your phone at any artwork, ask it a question, and the painting responds — in its own voice, with lip-synced animation.

---

## Pipeline

**Image Input → Gemini → ElevenLabs → Wav2Lip → Frontend**

1. **Gemini** identifies the artwork and generates character-driven dialogue
2. **ElevenLabs** converts the text response into realistic speech audio
3. **Wav2Lip** animates the painting's lips to sync with the audio
4. **React + FastAPI** handles the frontend and backend routing

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
