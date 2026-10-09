# DarkLab - Lightroom Classic Alternative

A modern, cross-platform photo editing application built with Python and PyQt6.

> Status: work in progress.

## Features

- **Import**: Import photos from cameras, memory cards, and folders
- **Library**: Organize and browse your photo collection
- **Develop**: Professional photo editing tools
- **Export**: Export photos in various formats
- **Print**: High-quality printing capabilities
- **Slideshow**: Create and present photo slideshows
- **Website**: Build photo galleries and websites

## Requirements

- Python 3.8+
- PyQt6
- Pillow
- NumPy
- OpenCV
- RawPy
- ExifRead

## Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

```bash
python main.py
```

## Architecture

The application follows a modular architecture with separate components:

- `src/ui/`: User interface components
- `src/config/`: Configuration management
- `src/ui/panels/`: Individual functional panels
- `src/ui/themes.py`: Dark theme styling

## Design Principles

- Platform-independent code
- Dark theme with macOS-like styling
- Panel-based interface
- Configuration persistence
- Modular, maintainable code structure

## License

MIT License

## License

MIT. See [LICENSE](LICENSE).
