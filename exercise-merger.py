#!/usr/bin/env python3
import re
import sys
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.WARNING,
    format="%(levelname)s: %(message)s"
)

EXERCISES_DIR = Path("exercises")
MISSING_DIR_WARNED = False

def read_multiline_until_blank(prompt: str) -> str:
    """
    Read pasted multiline input from the terminal until the user presses Enter
    on an empty line.
    """
    print(prompt)
    print("(Finish by pressing Enter on a blank line.)")
    lines = []
    try:
        while True:
            line = input()
            if line == "":
                break
            lines.append(line)
    except EOFError:
        pass
    except KeyboardInterrupt:
        print("\nInput cancelled.")
        sys.exit(1)
    return "\n".join(lines) + ("\n" if lines else "")

def write_textfile(filepath: Path, text: str) -> None:
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with filepath.open("w", encoding="utf-8", newline="") as f:
        f.write(text)

def ensure_tex_extension(path_str: str) -> Path:
    """
    Append .tex extension if not already present.
    """
    path = Path(path_str)
    if path.suffix != ".tex":
        path = path.with_suffix(".tex")
    return path

def load_file_if_exists(rel_path_str: str) -> str | None:
    path = ensure_tex_extension(rel_path_str)
    if not path.is_file():
        logging.warning(f"Missing file: {path}")
        return None
    try:
        return path.read_text(encoding="utf-8")
    except Exception as e:
        logging.warning(f"Could not read {path}: {e}")
        return None

def _warn_missing_exercises_dir_once():
    global MISSING_DIR_WARNED
    if not MISSING_DIR_WARNED:
        logging.warning(f"Missing directory: {EXERCISES_DIR}")
        MISSING_DIR_WARNED = True

def replace_exsetinput(text: str) -> str:
    pattern = re.compile(r"""\\exsetinput\{([^}]+)\}""")

    def repl(match: re.Match) -> str:
        path = match.group(1)
        if not EXERCISES_DIR.exists():
            _warn_missing_exercises_dir_once()
            return match.group(0)
        contents = load_file_if_exists(path)
        return contents if contents is not None else match.group(0)

    return pattern.sub(repl, text)

def replace_exinput(text: str) -> str:
    pattern = re.compile(r"""\\exinput\{([^}]+)\}""")

    def repl(match: re.Match) -> str:
        path = match.group(1)
        if not EXERCISES_DIR.exists():
            _warn_missing_exercises_dir_once()
            return match.group(0)
        contents = load_file_if_exists(path)
        return contents if contents is not None else match.group(0)

    return pattern.sub(repl, text)

def replace_print_tokens(text: str) -> str:
    text = re.sub(r"\\printconcepts\b", "Terms and Concepts", text)
    text = re.sub(r"\\printproblems\b", "Problems", text)
    text = re.sub(r"\\printreview\b", "Review", text)
    return text

def process_once(input_text: str) -> str:
    t = replace_exsetinput(input_text)
    t = replace_exinput(t)
    t = replace_print_tokens(t)
    return t

def process_with_recursion(input_text: str, max_passes: int = 10) -> str:
    prev = input_text
    for _ in range(max_passes):
        curr = process_once(prev)
        if curr == prev:
            return curr
        prev = curr
    logging.warning(f"Reached max replacement passes ({max_passes}). Some nested directives may remain.")
    return prev

def main():
    filename = input("Enter a filename (without extension is fine): ").strip()
    if not filename:
        print("No filename provided. Exiting.")
        sys.exit(1)
    if not filename.lower().endswith(".txt"):
        filename += ".txt"
    out_path = Path(filename)

    prompt = "Paste your multiline input text below."
    raw_text = read_multiline_until_blank(prompt)
    write_textfile(out_path, raw_text)

    processed = process_with_recursion(raw_text, max_passes=10)
    write_textfile(out_path, processed)

    print(f"\nDone. Wrote processed output to: {out_path.resolve()}")

if __name__ == "__main__":
    main()
