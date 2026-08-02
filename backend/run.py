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

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
