"""`python -m tck` -- same as the `acp-tck` console script. Useful for the self-tests
(the CLI tests under `tests/v{1,2}/cli/`) to invoke the CLI as a subprocess without depending on
the console script being installed on `PATH`."""

from tck import main

if __name__ == "__main__":
    raise SystemExit(main())
