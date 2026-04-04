# Contributing to PC Audio Monitor

Thanks for your interest in contributing! Here's how you can help.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR-USERNAME/pc-audio-monitor.git`
3. Create a feature branch: `git checkout -b feature/your-feature-name`
4. Install dependencies: `pip install -r requirements.txt`

## Development Setup

```bash
# Install development dependencies
pip install -r requirements.txt

# Run the app
python main.py

# Test the Home Assistant integration
python test_ha_integration.py
```

## Code Style

- Follow PEP 8
- Use meaningful variable names
- Add docstrings to functions
- Add comments for complex logic
- Keep lines under 100 characters

## Commit Messages

Use clear, descriptive commit messages:
```
git commit -m "Add feature: [description]"
git commit -m "Fix: [description]"
git commit -m "Docs: [description]"
```

Include the co-author trailer:
```
Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
```

## Testing

- Test your changes locally before submitting
- Check logs in `pc_audio_monitor.log`
- Verify `test_ha_integration.py` still works
- Test with different configuration settings

## Pull Request Process

1. Update documentation if needed
2. Add a description of your changes
3. Reference any related issues
4. Wait for review and feedback

## Areas for Contribution

- Bug fixes
- Documentation improvements
- New features (please open an issue first!)
- Testing improvements
- Performance optimizations

## Questions?

Open an issue or check the documentation in SETUP.md.

Thanks for contributing! 🚀
