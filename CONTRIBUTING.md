# Contributing

Thanks for your interest in contributing to Glucose Actions — Glucose Monitor & Alert System!

## How to contribute

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Make your changes
4. Run the tests (`pytest tests/ -v`)
5. Commit your changes
6. Push to your branch and open a Pull Request

## Adding a new output

The easiest way to contribute is by adding a new alert output:

1. Create `src/outputs/your_output.py` extending `BaseOutput`
2. Implement the `send_alert()` method
3. Add the output type in `build_outputs()` in `src/main.py`
4. Add configuration section in `config.example.yaml`
5. Add tests in `tests/`
6. Document the setup in `README.md`

## Reporting issues

Open an issue with:
- What you expected to happen
- What actually happened
- Steps to reproduce
- Your Python version and OS

## WhatsApp output testing

The WhatsApp Cloud API output has been implemented but **not yet tested with a real Meta Business account**. If you test it, please share your experience by opening an issue or PR — your feedback will help other users.

## Code style

- Python 3.12+ with type hints
- Run `pytest tests/ -v` before submitting
- Keep it simple — no over-engineering
