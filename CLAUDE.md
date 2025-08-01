# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

StoryLoom is an AI-enhanced tool for anime short film pre-production that converts scripts into visual production plans. It features a modular, task-oriented architecture with staged execution and comprehensive AI integration.

## Core Architecture

### Main Components
- **storyloom.py** - Main CLI entry point handling arguments and coordination
- **task_manager.py** - Task lifecycle, persistence, and staged execution orchestration  
- **ai_service.py** - OpenAI API integration with multi-provider support
- **models.py** - Data structures for scenes, characters, shots, and tasks
- **styles.py** - Built-in and custom visual style system

### Data Flow Pattern
```
Script Input → Parse Scenes → Extract Characters → Generate Storyboard → Optional Image Prompts
```

Each stage saves JSON data and markdown reports to `output/[task_id]/` directories.

## Development Commands

### Core Usage Patterns
```bash
# Main analysis with built-in style
python storyloom.py script.txt --style=ghibli

# Custom style with AI enhancement
python storyloom.py script.txt --custom-style="StyleName:Description of visual approach"

# Generate image prompts for existing task (cost-effective two-phase approach)
python storyloom.py --generate-prompts [task_id]

# List available built-in styles
python storyloom.py --style-list
```

### Environment Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Configure AI service (copy .env.example to .env)
export OPENAI_API_KEY="your-key"
export OPENAI_BASE_URL="https://api.openai.com/v1" 
export OPENAI_MODEL_NAME="gpt-4"
```

### Testing
```bash
# Test character extraction
python test_characters.py

# Use example scripts from examples/ directory
python storyloom.py "examples/YYDS的算法恋爱.txt" --style=anime
```

## Key Architectural Patterns

### Task-Oriented Design
- **Unique Task IDs**: 8-character UUID prefixes for easy reference
- **Staged Execution**: Main analysis runs independently from image prompt generation
- **Persistent State**: Tasks survive across sessions with full JSON persistence
- **Progress Tracking**: Boolean completion flags for each processing stage

### AI Service Integration
- **Multi-Provider Support**: OpenAI, Azure, DeepSeek, 智谱AI, 通义千问, DMX API
- **Batch Processing**: Image prompts generated in batches of 5 for efficiency
- **Token Tracking**: Comprehensive usage statistics with cost optimization
- **Graceful Degradation**: Falls back to basic mode if AI unavailable

### Visual Style System
- **Built-in Styles**: Ghibli, Shinkai, KyoAni, Pixar, Disney, etc.
- **Custom Styles**: AI-powered generation from user name/description input
- **Complete Parameters**: Each style defines shot characteristics, color palette, lighting, character design, backgrounds

## Data Persistence Structure

```
output/
├── tasks/[task_id].json     # Task metadata and progress
└── [task_id]/               # Task output directory
    ├── scenes.json          # Structured scene data
    ├── characters.json      # Character profiles + AI image prompts
    ├── shots.json           # Professional storyboard data
    ├── shooting_script.md   # Industry-standard shooting script
    ├── main_report.md       # Complete analysis report
    └── image_prompts.md     # Midjourney-style prompts (optional)
```

## Important Implementation Details

### Custom Style Usage
- Format: `--custom-style="Name:Description"`
- AI automatically generates complete style parameters
- Persisted in task data for image prompt generation phase

### Character Processing Optimization
- Characters extracted once during main analysis
- Reused during image prompt generation to avoid redundancy
- Each character includes AI-generated image prompts for consistency

### Professional Output Focus
- Industry-standard shooting script format
- Director-level "thinking" in storyboard generation
- Modern internet culture integration for network content
- Midjourney prompt formats (English/Chinese/Simple versions)

### Error Handling Strategy
- Comprehensive validation of AI responses
- Fallback to basic processing if AI services fail
- Clear error messages with actionable solutions
- Automatic retry logic for network issues

## Multi-Language Considerations

The tool is designed for Chinese script inputs but generates:
- Chinese markdown reports for human readability
- English image prompts for AI image generation compatibility
- Mixed-language output optimized for anime production workflows

## Development Workflow Notes

- Always test with actual script files from examples/ directory
- Monitor token usage through built-in statistics
- Use staged execution for cost-effective development
- Leverage existing task IDs to avoid reprocessing during development
- Custom styles require AI service - ensure proper API configuration