# arXiv Pulse - Intelligent arXiv Literature Tracking System

[![Version](https://img.shields.io/pypi/v/arxiv-pulse.svg)](https://pypi.org/project/arxiv-pulse/)
![Python](https://img.shields.io/badge/python-3.12%2B-green)
![License](https://img.shields.io/badge/license-GPL--3.0-orange)

> 🌐 **Language**: [中文文档](README_CN.md)

**arXiv Pulse** is a Python package for automated crawling, summarizing, and tracking of the latest research papers from arXiv in condensed matter physics, density functional theory (DFT), machine learning, force fields, and computational materials science. It provides a modern web interface for a professional literature management experience.

## ✨ Key Features

- **🌐 Web Interface**: Modern FastAPI + Vue 3 web interface with real-time SSE streaming
- **🚀 One-Command Start**: Simply run `pulse serve` to start the service
- **📝 Web Configuration**: First-time setup wizard, all settings stored in database
- **📁 Paper Collections**: Create, edit, and delete collections to organize important papers
- **🤖 AI Auto-Processing**: Automatic translation, AI summarization, and figure extraction
- **🔍 Smart Search**: Natural language queries with AI-powered keyword parsing
- **💾 Database Storage**: SQLite database for paper metadata and configuration
- **⚙️ System Settings**: Web-based management of AI API, research fields, and sync options
- **🌍 Multilingual Support**: UI in Chinese/English, translation to Chinese/English
- **🎯 Research Focused**: Optimized for condensed matter physics, DFT, ML, force fields

## 🆕 v1.0.0 Major Update

### Multilingual Support
- **UI Language**: Switch between Chinese and English in settings
- **Translation Language**: Choose to translate papers to Chinese or keep original English
- **Bilingual Documentation**: README in both English and Chinese

### Service Management
- **Background Mode**: Default background execution with `pulse start`
- **Foreground Mode**: Use `-f` flag for foreground execution
- **Service Control**: `pulse status`, `pulse stop`, `pulse restart`

### Enhanced UI
- **Larger Icons**: More prominent action buttons on paper cards
- **Floating Widgets**: Paper basket, AI chat, and home button aligned at bottom-right
- **Improved Animations**: Smooth transitions and feedback

## 🚀 Quick Start

### Installation

```bash
pip install arxiv-pulse
```

### Start Service

```bash
# Create data directory
mkdir my_papers && cd my_papers

# Start web service (background mode by default)
pulse serve .

# Or specify port
pulse serve . --port 3000

# Foreground mode
pulse serve . -f
```

### Service Management

```bash
pulse status .          # Check service status
pulse stop .            # Stop service
pulse restart .         # Restart service
pulse stop . --force    # Force stop (SIGKILL)
```

### First-Time Setup

1. Visit http://localhost:8000
2. Follow the setup wizard:
   - **Step 1**: Configure AI API (key, model, endpoint)
   - **Step 2**: Select research fields
   - **Step 3**: Set sync parameters
   - **Step 4**: Start initial sync

### Daily Usage

- **Recent Papers**: View papers from the last N days
- **Search**: Natural language search with AI parsing
- **Collections**: Create collections to organize important papers
- **Settings**: Click the gear icon to modify configuration
- **AI Chat**: Ask questions about papers with AI assistant

## 📁 Project Structure

```
arxiv_pulse/
├── cli.py                     # CLI entry point
├── config.py                  # Configuration management
├── models.py                  # Database models
├── arxiv_crawler.py           # arXiv API interactions
├── summarizer.py              # Paper summarizer
├── search_engine.py           # Enhanced search engine
├── report_generator.py        # Report generator
├── research_fields.py         # Research field definitions
├── i18n/                      # Internationalization
│   ├── __init__.py
│   ├── zh.py                  # Chinese translations
│   └── en.py                  # English translations
└── web/
    ├── app.py                 # FastAPI application
    ├── static/index.html      # Vue 3 frontend
    └── api/
        ├── papers.py          # Paper API + SSE
        ├── collections.py     # Collections API
        ├── config.py          # Config API
        ├── tasks.py           # Sync tasks API
        ├── stats.py           # Statistics API
        ├── export.py          # Export API
        └── chat.py            # AI Chat API

Data Directory/
├── data/
│   └── arxiv_papers.db        # SQLite database (includes config)
└── web.log                    # Background service log
```

## 🔧 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/config` | GET/PUT | Get/update configuration |
| `/api/config/status` | GET | Get initialization status |
| `/api/config/init` | POST | Save initial configuration |
| `/api/config/init/sync` | POST (SSE) | Execute initial sync |
| `/api/papers/search/stream` | GET (SSE) | AI-powered search |
| `/api/papers/recent/update` | POST (SSE) | Update recent papers |
| `/api/collections` | GET/POST | List/create collections |
| `/api/stats` | GET | Database statistics |
| `/api/chat/sessions` | GET/POST | List/create chat sessions |
| `/api/chat/sessions/{id}/send` | POST (SSE) | Send message to AI |

## 🧪 Supported Research Fields

The system supports 20+ research fields, selectable in the web setup wizard:

| Field | Description |
|-------|-------------|
| Condensed Matter Physics | Superconductivity, strongly correlated electrons, mesoscopic systems |
| Density Functional Theory (DFT) | First-principles calculations, materials design |
| Machine Learning | ML applications in physics and materials science |
| Force Fields & MD | Force field development, MD simulations |
| First-Principles Calculations | Ab initio methods |
| Quantum Physics | Quantum information, quantum computing |
| Computational Physics | Numerical methods |
| Chemical Physics | Physical basis of chemical processes |
| Molecular Dynamics | MD simulation techniques |
| Computational Materials Science | Materials computation and simulation |
| Quantum Chemistry | Quantum chemistry methods |
| Astrophysics | Cosmology, astronomical observations |
| High Energy Physics | Particle physics theory and experiments |
| Nuclear Physics | Nuclear physics theory and experiments |
| Artificial Intelligence | AI, neural networks |
| Numerical Analysis | Numerical methods and algorithms |
| Statistics | Statistical theory and applications |
| Quantitative Biology | Bioinformatics, systems biology |
| Electrical Engineering | Signal processing, control systems |
| Mathematical Physics | Mathematical methods for physics |

## 🐛 Troubleshooting

### Common Issues

**Q: Forgot API key?**
A: Click the settings icon in the top-right corner to modify your API key and other configurations.

**Q: How to reinitialize?**
A: Delete the `data/arxiv_papers.db` database file and restart the service to enter the setup wizard again.

**Q: Port already in use?**
A: Use `pulse serve . --port 3000` to specify a different port.

**Q: Service shows "not running" but port is occupied?**
A: Check for stale lock file (`.pulse.lock`) and remove it, or use `pulse stop --force`.

### Debugging

```bash
# View detailed logs
pulse serve . -f

# Check background service log
tail -f web.log
```

## 🔧 Advanced Usage

### Auto-Scheduling with Systemd (Linux)

Create `/etc/systemd/system/arxiv-pulse.service`:
```ini
[Unit]
Description=arXiv Pulse Web Service
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/your/papers
ExecStart=/usr/local/bin/pulse serve .
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable the service:
```bash
sudo systemctl enable arxiv-pulse
sudo systemctl start arxiv-pulse
```

## 📄 License

This project is licensed under GPL-3.0 - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 🙏 Acknowledgments

- [arXiv.org](https://arxiv.org) for the API
- [DeepSeek](https://www.deepseek.com) for AI models
- Computational materials science community

## 📞 Support

For questions or suggestions:
1. Check [GitHub Issues](https://github.com/kYangLi/ArXiv-Pulse/issues)
2. Check the log files in your data directory
3. Review the configuration in the web settings

---

**arXiv Pulse** - Making arXiv literature tracking simple and efficient!
