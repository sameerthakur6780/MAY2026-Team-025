import sys

# deepface (and its dependencies) log emoji/unicode characters that Windows'
# default console codepage (cp1252) can't encode, crashing whatever request
# triggered the log line. errors="replace" also guards against any other
# unencodable character a dependency logs in the future.
if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr.encoding.lower() != "utf-8":
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from app import create_app

# If deploying this behind gunicorn (`gunicorn run:app`), run it with a
# single worker (-w 1). NotificationService's atomic claim step (see
# app/services/notification_service.py) stops two workers from double-
# sending the same notification, but the scheduler's job store is still
# in-memory per-process -- more than one worker means more than one copy of
# every scheduled job, which is extra background work for no benefit at
# this project's scale. -w 1 is the tested/supported configuration.
app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
