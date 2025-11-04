# 🎵 Remira - AI-Powered Family Photo Song Generator

**Transform your cherished family memories into personalized musical masterpieces**

Remira is an innovative AI-powered application that analyzes your family photos, understands their emotional context, and creates a complete original song with custom lyrics, melodious instrumental music, and expressive vocals—all generated using cutting-edge open-source AI models.

---

## 🎯 Project Overview

### What Remira Does
- **Analyzes family photos** using advanced vision AI to understand scenes, emotions, and moments
- **Generates narrative summaries** that capture the essence and story of your photos
- **Creates custom song lyrics** tailored to your photos, genre preference, and desired mood
- **Generates beautiful instrumental music** using Stable Audio Open for melodious background tracks
- **Synthesizes expressive vocals** using Bark TTS to sing/speak the lyrics naturally
- **Mixes everything together** into a professional-quality final audio track ready to download

### The Complete Pipeline
```
Family Photos → BLIP-2 Image Analysis → LLM Story Summary → Custom Lyrics Generation 
    → Stable Audio Music Generation → Bark TTS Vocal Synthesis → Audio Mixing → Final Song 🎶
```

---

## 🏗️ Architecture & Technology Stack

### Backend Infrastructure
- **Modal.com** - Serverless GPU compute platform for running ML models
  - Auto-scales GPU resources (A10G GPUs) based on demand
  - Handles model downloads, caching, and persistent storage
  - Provides FastAPI endpoints for seamless API integration

### AI Models Used (All Open-Source)
- **BLIP-2 (Salesforce/blip2-flan-t5-xl)** - State-of-the-art vision-language model for detailed image captioning
- **Qwen2.5-VL-7B** - Vision-language LLM for generating narrative summaries from captions
- **Stable Audio Open 1.0** - Professional-quality music generation model (up to 47 seconds)
- **Bark TTS (suno/bark)** - Expressive text-to-speech model that can generate singing and speech

### Core Technologies
- **Python 3.x** - Backend language
- **PyTorch 2.3.1** - Deep learning framework
- **Transformers 4.45.2** - Hugging Face model library
- **Diffusers 0.31.0** - Audio generation pipeline
- **FastAPI** - REST API framework
- **Pydub** - Audio processing and mixing library
- **SoundFile** - Audio file I/O operations

### Frontend Development
- **Lovable.dev** - AI-powered web application development platform
  - Used to rapidly build and iterate the user interface
  - Streamlined frontend-backend integration with Modal API endpoints
  - Enabled fast prototyping and deployment of the web application

---

## 📋 Key Features

### 1. Intelligent Photo Analysis
- **Multi-image support** - Process multiple photos in a single job
- **Detailed captioning** - BLIP-2 generates rich, contextual descriptions
- **Emotion detection** - Understands mood and sentiment from visual cues

### 2. Narrative Story Generation
- **Cohesive summaries** - Qwen LLM creates personalized stories from photo captions
- **Contextual understanding** - Connects multiple photos into a unified narrative
- **Emotional depth** - Captures the essence and feelings of family moments

### 3. Custom Lyrics Creation
- **Genre-aware** - Supports multiple genres (pop, rock, acoustic, EDM, lo-fi, etc.)
- **Mood customization** - Adapts to desired emotional tone (nostalgic, happy, epic, etc.)
- **Structured format** - Generates professional song structure with verses and choruses
- **Story-driven** - Lyrics directly reference events and moments from your photos

### 4. Professional Music Generation
- **Stable Audio Open** - Generates high-quality instrumental music (25-47 seconds)
- **Context-aware prompts** - Music themes extracted from lyrics for better cohesion
- **Genre and mood matching** - Music style matches user-selected preferences
- **High-quality settings** - 150 inference steps for optimal audio quality

### 5. Expressive Vocal Synthesis
- **Bark TTS** - Natural-sounding speech and singing synthesis
- **Voice presets** - Consistent, clear English voice generation
- **Lyrics optimization** - Text preprocessing for best audio output
- **Audio normalization** - Prevents clipping and ensures balanced output

### 6. Professional Audio Mixing
- **Hybrid approach** - Combines instrumental music + vocals seamlessly
- **Volume balancing** - Music at background level (-8dB), vocals prominent (+2dB)
- **Automatic normalization** - Prevents audio distortion
- **Fallback handling** - Graceful degradation if mixing fails

---

## 🚀 How It Works

### Step 1: Photo Upload
- Users upload family photos via the web interface (built with Lovable)
- Supports both URL-based uploads and direct file uploads
- Photos stored in Modal persistent volumes for processing

### Step 2: Job Submission
- User selects genre (pop, rock, acoustic, etc.) and mood (nostalgic, happy, epic, etc.)
- Backend creates a job with unique ID and queues it for processing

### Step 3: AI Processing Pipeline
1. **Image Analysis** - BLIP-2 generates detailed captions for each photo
2. **Story Generation** - Qwen LLM creates a cohesive narrative summary
3. **Lyrics Generation** - Qwen LLM writes structured song lyrics based on the story
4. **Music Generation** - Stable Audio creates instrumental track matching genre/mood
5. **Vocal Synthesis** - Bark TTS generates expressive vocals from lyrics
6. **Audio Mixing** - Pydub mixes music and vocals into final track
7. **Result Packaging** - Creates download URL and metadata

### Step 4: Result Retrieval
- Users poll job status endpoint
- Once complete, download the final audio file
- Can also retrieve captions, summary, and lyrics

---

## 🔧 Development Setup

### Prerequisites
- Python 3.8+
- Modal.com account (free tier available)
- LLMStudio or compatible LLM API endpoint (for Qwen models)
- ngrok or similar tunnel service (for local LLM testing)

### Installation Steps

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Remira
   ```

2. **Set up Python environment**
   ```bash
   conda create -n remira python=3.10
   conda activate remira
   pip install -r backend/requirements.txt
   ```

3. **Install Modal CLI**
   ```bash
   pip install modal
   modal setup
   ```

4. **Configure environment variables**
   - Set `LLMSTUDIO_API_URL` in `modal_app.py` (or use environment variable)
   - Set `LLMSTUDIO_MODEL_NAME` (default: `qwen/qwen2.5-vl-7b`)
   - Configure `BLIP_MODEL` and `BARK_MODEL_ID` if needed

5. **Deploy backend to Modal**
   ```bash
   cd backend
   modal deploy modal_app.py
   ```

6. **Frontend setup (Lovable)**
   - Connect frontend to Modal API endpoints
   - Configure API base URL to point to deployed Modal app
   - Set up file upload handling

---

## 📡 API Endpoints

### `POST /upload_photo`
Upload photos via URLs or direct file upload
- **Body**: `{ "image_urls": ["url1", "url2"] }` or multipart form data
- **Returns**: `{ "job_id": "...", "status": "created" }`

### `POST /submit_job`
Submit a job for processing with genre and mood
- **Body**: `{ "job_id": "...", "genre": "pop", "mood": "nostalgic" }`
- **Returns**: `{ "job_id": "...", "status": "queued" }`

### `GET /get_status?job_id=...`
Check the current status of a job
- **Returns**: Full job object with current status

### `GET /fetch_result?job_id=...`
Get the final result when job is complete
- **Returns**: `{ "captions": [...], "summary": "...", "lyrics": "...", "audio_url": "..." }`

### `GET /download_audio?job_id=...`
Download the generated audio file
- **Returns**: WAV audio file stream

---

## 🎨 Using Lovable.dev for Frontend Development

### Why Lovable?
- **Rapid prototyping** - Build web interfaces quickly with AI assistance
- **Seamless integration** - Easy connection to backend APIs
- **Modern UI components** - Pre-built components for file uploads, progress tracking, etc.
- **Real-time updates** - Live preview of changes during development

### Implementation Steps with Lovable
1. **Created project structure** - Set up React/Next.js application
2. **Designed UI components**:
   - Photo upload interface with drag-and-drop
   - Genre and mood selection dropdowns
   - Progress indicator for job status
   - Audio player for final result
3. **Integrated Modal API** - Connected frontend to deployed Modal endpoints
4. **Implemented polling** - Status checking mechanism for job completion
5. **Added error handling** - User-friendly error messages and retry logic
6. **Styled interface** - Modern, responsive design for web and mobile

### Key Frontend Features Built
- **Multi-photo upload** - Drag-and-drop or file picker
- **Real-time status updates** - Polling mechanism shows processing progress
- **Audio preview** - Built-in audio player for generated songs
- **Result display** - Shows captions, summary, and lyrics alongside audio
- **Download functionality** - One-click download of final audio file

---

## ⚙️ Configuration & Customization

### Audio Mix Settings
Adjust volume levels in `backend/api/submit_job.py`:
```python
music_volume_db=-8,    # Music volume (negative = quieter)
vocals_volume_db=2,    # Vocals volume (positive = louder)
```

### Music Generation Settings
Modify in `backend/workers/music_worker.py`:
```python
seconds=25.0,              # Duration (max ~47s for Stable Audio)
num_inference_steps=150,  # Quality (50-200, higher = better but slower)
```

### Model Selection
Customize models in `backend/modal_app.py`:
```python
BLIP_MODEL="Salesforce/blip2-flan-t5-xl"  # Image captioning
BARK_MODEL_ID="suno/bark"                  # Voice synthesis
```

---

## 🧪 Testing

### Local Testing
```bash
cd backend
modal run modal_app.py
```

This runs a local test with sample images and prints the result.

### API Testing
Use the deployed Modal endpoints:
```bash
# Upload photos
curl -X POST https://your-app.modal.run/upload_photo \
  -H "Content-Type: application/json" \
  -d '{"image_urls": ["https://example.com/photo.jpg"]}'

# Submit job
curl -X POST https://your-app.modal.run/submit_job \
  -H "Content-Type: application/json" \
  -d '{"job_id": "...", "genre": "pop", "mood": "nostalgic"}'
```

---

## 📊 Performance & Quality

### Processing Times
- **First run**: ~60-90 seconds (model downloads)
- **Subsequent runs**: ~30-45 seconds (cached models)
- **Music generation**: ~15-20 seconds
- **Vocal synthesis**: ~5-10 seconds
- **Audio mixing**: ~1-2 seconds

### Resource Requirements
- **GPU**: A10G (10GB VRAM) recommended
- **Memory**: ~10-12GB GPU memory during processing
- **Storage**: Persistent volumes for photos and audio files

### Quality Ratings
- **Melodiousness**: ⭐⭐⭐⭐⭐ (hybrid music + vocals approach)
- **Professional sound**: ⭐⭐⭐⭐⭐ (proper audio mixing)
- **Emotional impact**: ⭐⭐⭐⭐⭐ (context-aware generation)
- **Lyrics quality**: ⭐⭐⭐⭐ (story-driven, genre-aware)

---

## 🔄 Workflow Example

1. **User uploads 3 family photos** of a birthday party
2. **Selects genre**: "pop" and mood: "happy"
3. **Backend processes**:
   - BLIP-2: "A joyful birthday celebration with family members gathered around a cake"
   - Qwen Summary: "A warm family gathering celebrating a special birthday, filled with laughter and love"
   - Qwen Lyrics: "[Verse 1] Candles glowing bright tonight... [Chorus] Happy birthday, love surrounds us..."
   - Stable Audio: Generates upbeat pop instrumental
   - Bark TTS: Synthesizes vocals singing the lyrics
   - Mixing: Combines into final track
4. **User receives**: Complete song with music, vocals, lyrics, and story summary
5. **User downloads**: Professional-quality WAV file ready to share

---

## 🛠️ Troubleshooting

### Common Issues

**Model download failures**
- Solution: Ensure stable internet connection, Modal handles retries automatically

**Audio mixing errors**
- Solution: Check that `pydub` is installed in Modal image, fallback to vocals-only

**LLM API unavailable**
- Solution: System automatically falls back to rule-based generators for summary/lyrics

**GPU memory errors**
- Solution: Reduce `num_inference_steps` in music generation or use smaller models

**Silent audio generation**
- Solution: Bark includes fallback tone generation, check Modal logs for details

---

## 🚀 Future Enhancements

- **Multiple voice options** - Support for different voice presets in Bark
- **Longer songs** - Extend beyond 47 seconds with multiple segments
- **Video generation** - Create music videos from photos
- **Social sharing** - Direct sharing to social media platforms
- **Batch processing** - Process multiple photo sets simultaneously
- **Custom model fine-tuning** - Fine-tune models on specific music styles
- **Real-time generation** - WebSocket-based progress updates

---

## 📝 Project Structure

```
Remira/
├── backend/
│   ├── api/
│   │   ├── upload_photo.py      # Photo upload endpoints
│   │   ├── submit_job.py         # Job submission and pipeline
│   │   ├── get_status.py         # Status checking
│   │   ├── fetch_result.py       # Result retrieval
│   │   └── download_audio.py     # Audio file download
│   ├── workers/
│   │   ├── image_analysis_worker.py  # BLIP-2 captioning
│   │   ├── summary_worker.py         # LLM story generation
│   │   ├── lyrics_worker.py          # Lyrics generation
│   │   ├── music_worker.py           # Stable Audio music generation
│   │   ├── vocal_worker.py            # Bark TTS vocal synthesis
│   │   └── packaging_worker.py        # Result packaging
│   ├── modal_app.py              # Modal app configuration
│   ├── requirements.txt          # Python dependencies
│   └── HYBRID_AUDIO_CHANGES.md   # Implementation details
├── images/                       # Sample images
└── README.md                     # This file
```

---

## 🎓 Key Learnings & Technologies

### AI/ML Stack
- **Vision-language models** - BLIP-2 for image understanding
- **Large language models** - Qwen for text generation
- **Audio generation** - Stable Audio for music synthesis
- **Text-to-speech** - Bark for vocal generation
- **Audio processing** - Pydub for professional mixing

### Infrastructure
- **Serverless computing** - Modal for GPU-accelerated ML workloads
- **Persistent storage** - Modal volumes for file management
- **API design** - FastAPI for RESTful endpoints
- **Job queue system** - Modal's async function spawning

### Development Tools
- **Lovable.dev** - Rapid frontend development
- **Version control** - Git for code management
- **Dependency management** - Requirements.txt for Python packages

---

## 📄 License

This project uses open-source models and libraries. Please check individual model licenses:
- **BLIP-2**: BSD License
- **Qwen**: Tongyi Qianwen License
- **Stable Audio Open**: Apache 2.0
- **Bark**: MIT License

---

## 🙏 Acknowledgments

- **Modal.com** - For providing serverless GPU infrastructure
- **Lovable.dev** - For enabling rapid frontend development
- **Hugging Face** - For model hosting and Transformers library
- **Stability AI** - For Stable Audio Open model
- **Suno AI** - For Bark TTS model
- **Salesforce Research** - For BLIP-2 vision-language model
- **Qwen Team** - For Qwen LLM models

---

## 📧 Contact & Support

For questions, issues, or contributions, please open an issue in the repository.

---

**Built with ❤️ using AI to preserve and celebrate family memories through music**
# REMIRA
