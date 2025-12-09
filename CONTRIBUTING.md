# Contributing

Guidelines for contributing to Destroyer-DoS Framework.

## Code of Conduct

- Be respectful and constructive
- Focus on technical merit
- No harassment or discrimination
- Do not promote illegal activities

## Getting Started

1. Fork the repository
2. Clone your fork
3. Create a feature branch
4. Make changes
5. Submit a pull request

## Development Setup

```bash
git clone https://github.com/YOUR_USERNAME/Destroyer-DoS.git
cd Destroyer-DoS
python -m venv venv
source venv/bin/activate  # Linux/macOS
pip install -r requirements.txt
pip install pytest black flake8
```

## Making Changes

### Branch Naming

- `feature/description` - New features
- `bugfix/description` - Bug fixes
- `docs/description` - Documentation

### Commit Messages

Use clear, descriptive messages:

```
Add UDP packet size optimization
Fix memory leak in TCP flood
Update installation documentation
```

### Code Style

- Follow PEP 8
- Use type hints
- Add docstrings to functions
- Keep functions focused and small

```python
def calculate_pps(packets: int, duration: float) -> float:
    """Calculate packets per second.

    Args:
        packets: Total packets sent
        duration: Time in seconds

    Returns:
        Packets per second
    """
    if duration <= 0:
        return 0.0
    return packets / duration
```

### Formatting

```bash
black .
flake8 .
```

## Testing

```bash
# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=core
```

All new features should include tests.

## Pull Request Process

1. Update your branch with main
2. Run tests locally
3. Format code with black
4. Create pull request
5. Describe changes clearly
6. Wait for review

### PR Checklist

- [ ] Tests pass
- [ ] Code is formatted
- [ ] Documentation updated
- [ ] No breaking changes

## Reporting Issues

### Bug Reports

Include:

- Description of the bug
- Steps to reproduce
- Expected vs actual behavior
- OS and Python version
- Error messages

### Feature Requests

Include:

- Description of the feature
- Use case
- Proposed implementation

## Questions

- Check existing issues first
- Read the documentation
- Open a discussion if needed
