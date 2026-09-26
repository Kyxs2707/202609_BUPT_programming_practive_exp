"""允许通过 python -m team_tasks 运行。"""

from .cli import main


if __name__ == "__main__":
    raise SystemExit(main())
