import os
import sys
import logging
import logging.handlers
import subprocess
from typing import Optional


def setup_logger(
    name: str,
    log_file: Optional[str] = None,
    level: str = "INFO",
    max_bytes: int = 10485760,  # 10MB
    backup_count: int = 5
) -> logging.Logger:
    logger = logging.getLogger(name)
    log_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(log_level)

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    if log_file:
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)

        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: Plaintext password.

    Returns:
        Hashed password.
    """
    try:
        import bcrypt
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    except ImportError:
        raise ImportError("Install bcrypt: pip install bcrypt")

def ensure_directory(path: str, mode: int = 0o755) -> None:
    os.makedirs(path, mode=mode, exist_ok=True)


def ensure_file_permissions(path: str, mode: int = 0o600) -> None:
    if os.path.exists(path):
        os.chmod(path, mode)


def main():
    import argparse

    parser = argparse.ArgumentParser(description='MailHarbor Utilities')
    parser.add_argument(
        'command',
        choices=['hash_password'],
        help='Command to execute.'
    )
    parser.add_argument(
        'args',
        nargs='*',
        help='Command arguments.'
    )

    args = parser.parse_args()

    if args.command == 'hash_password':
        if not args.args:
            print("Usage: python -m src.utils hash_password <password>")
            sys.exit(1)

        password = args.args[0]
        hashed = hash_password(password)
        print(f"Plaintext: {password}")
        print(f"Hashed: {hashed}")
        print("\nUse in config:")
        print(f"  password: \"{hashed}\"")
        print(f"  password_scheme: BLF-CRYPT")


if __name__ == '__main__':
    main()
