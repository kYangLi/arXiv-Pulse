"""
English translations for arXiv Pulse backend.
"""

EN_DICT: dict = {
    # Common
    "common": {
        "success": "Success",
        "error": "Error",
        "loading": "Loading...",
        "saving": "Saving...",
        "done": "Done",
        "cancel": "Cancel",
        "confirm": "Confirm",
        "delete": "Delete",
        "edit": "Edit",
        "save": "Save",
    },
    # API messages
    "api": {
        "config": {
            "saved": "Configuration saved",
            "save_failed": "Failed to save",
            "not_initialized": "System not initialized",
            "api_key_required": "API Key is required",
            "model_required": "Model name is required",
        },
        "papers": {
            "not_found": "Paper not found",
            "search_empty": "Please enter search keywords",
            "searching": "Searching...",
            "syncing": "Syncing...",
            "sync_done": "Sync completed",
            "no_new_papers": "No new papers",
            "papers_added": "{count} papers added",
            "updating": "Updating...",
            "update_done": "Update completed",
            "translating": "Translating...",
            "summarizing": "Summarizing...",
        },
        "collections": {
            "created": "Collection created",
            "updated": "Collection updated",
            "deleted": "Collection deleted",
            "not_found": "Collection not found",
            "name_required": "Name is required",
            "paper_added": "Paper added to collection",
            "paper_removed": "Paper removed from collection",
        },
        "chat": {
            "thinking": "Thinking...",
            "processing": "Processing...",
            "no_session": "Session not found",
            "session_created": "Session created",
            "session_deleted": "Session deleted",
            "message_sent": "Message sent",
        },
        "export": {
            "exporting": "Exporting...",
            "export_done": "Export completed",
            "no_papers": "No papers to export",
        },
    },
    # SSE progress messages
    "progress": {
        "connecting": "Connecting...",
        "connected": "Connected",
        "fetching_papers": "Fetching papers...",
        "papers_fetched": "{count} papers fetched",
        "processing_papers": "Processing papers...",
        "paper_processed": "Processed {current}/{total}",
        "ai_analyzing": "AI analyzing...",
        "translating_title": "Translating title...",
        "translating_abstract": "Translating abstract...",
        "generating_summary": "Generating summary...",
        "extracting_figure": "Extracting figure...",
        "done": "Done",
        "error": "Error: {error}",
    },
    # Sync task messages
    "sync": {
        "starting": "Starting sync...",
        "checking_updates": "Checking for updates...",
        "downloading": "Downloading papers...",
        "processing": "Processing papers...",
        "completed": "Sync completed",
        "failed": "Sync failed",
        "no_papers": "No new papers found",
        "papers_synced": "{count} papers synced",
    },
    # Chat messages
    "chat": {
        "welcome": "Hello! I'm an AI assistant that can help you analyze papers and answer questions. How can I help you?",
        "system_prompt": """You are a professional academic research assistant helping users analyze arXiv papers.

You can:
- Summarize the core content and contributions of papers
- Explain technical concepts and methods in papers
- Compare similarities and differences between papers
- Answer user questions about papers
- Provide research suggestions

Please respond in a professional yet accessible language, citing original paper text when necessary.""",
        "no_context": "Please select a paper to analyze first.",
        "paper_context": "Currently analyzing paper: {title}",
    },
    # Research fields (for API responses)
    "fields": {
        "condensed_matter": "Condensed Matter Physics",
        "dft": "Density Functional Theory (DFT)",
        "machine_learning": "Machine Learning",
        "force_fields": "Force Fields & Molecular Dynamics",
        "first_principles": "First-Principles Calculations",
        "quantum_physics": "Quantum Physics",
        "computational_physics": "Computational Physics",
        "chemical_physics": "Chemical Physics",
        "molecular_dynamics": "Molecular Dynamics",
        "computational_materials": "Computational Materials Science",
        "quantum_chemistry": "Quantum Chemistry",
        "astrophysics": "Astrophysics",
        "high_energy": "High Energy Physics",
        "nuclear_physics": "Nuclear Physics",
        "artificial_intelligence": "Artificial Intelligence",
        "numerical_analysis": "Numerical Analysis",
        "statistics": "Statistics",
        "quantitative_biology": "Quantitative Biology",
        "electrical_engineering": "Electrical Engineering",
        "mathematical_physics": "Mathematical Physics",
    },
    # Category explanations
    "categories": {
        "cond-mat.mes-hall": "Mesoscopic Systems and Quantum Hall Effect",
        "cond-mat.mtrl-sci": "Materials Science",
        "cond-mat.other": "Other Condensed Matter",
        "cond-mat.quant-gas": "Quantum Gases",
        "cond-mat.soft": "Soft Condensed Matter",
        "cond-mat.stat-mech": "Statistical Mechanics",
        "cond-mat.str-el": "Strongly Correlated Electrons",
        "cond-mat.supr-con": "Superconductivity",
        "physics.chem-ph": "Chemical Physics",
        "physics.comp-ph": "Computational Physics",
        "quant-ph": "Quantum Physics",
        "cs.LG": "Machine Learning",
        "cs.AI": "Artificial Intelligence",
        "cs.NE": "Neural and Evolutionary Computing",
    },
    # Time related
    "time": {
        "just_now": "Just now",
        "minutes_ago": "{n} minutes ago",
        "hours_ago": "{n} hours ago",
        "days_ago": "{n} days ago",
        "yesterday": "Yesterday",
        "never": "Never",
    },
    # Status
    "status": {
        "running": "Running",
        "completed": "Completed",
        "failed": "Failed",
        "pending": "Pending",
        "cancelled": "Cancelled",
    },
}
