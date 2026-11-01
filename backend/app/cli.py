"""python -m app.cli createuser <email> <password> [name]"""
import sys

from .auth import hash_password
from .db import SessionLocal
from .models import User


def main(argv: list[str]) -> int:
    if len(argv) >= 3 and argv[0] == "createuser":
        email, pw, name = argv[1].lower(), argv[2], (argv[3] if len(argv) > 3 else None)
        with SessionLocal() as db:
            if db.query(User).filter_by(email=email).first():
                print("exists")
                return 1
            db.add(User(email=email, password_hash=hash_password(pw), name=name))
            db.commit()
        print(f"created {email}")
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
