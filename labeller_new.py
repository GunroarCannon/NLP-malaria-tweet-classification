"""
=============================================================
  MALARIA TWEET ANNOTATOR  —  Crash-Safe Edition
  For: BERTweet Topic Classification (Nigeria)
=============================================================
  Features:
    ✅ Auto-save every 5 labels + on every Ctrl+C / crash
    ✅ Backup file so a corrupt save never loses all work
    ✅ Session stats: speed, ETA, time elapsed
    ✅ Resume exactly where you stopped
    ✅ Second-annotator mode (isolated 100-tweet slice)
    ✅ IAA export: compare your labels vs second annotator
=============================================================
"""

import pandas as pd
import os
import sys
import json
import signal
import atexit
import time
from datetime import datetime, timedelta
from IPython.display import clear_output

def get_single_key(n=""):
    """Reads a single keystroke from the terminal without waiting for Enter."""
    # Check for Windows operating system
    print(n, end='', flush=True)
    if os.name == 'nt':
        import msvcrt
        
        # msvcrt.getch() blocks until a key is pressed, returning bytes
        char = msvcrt.getch()
        # Handle special keys (arrows, function keys) which return 2 bytes
        if char in (b'\x00', b'\xe0'):
            char += msvcrt.getch()
        return char.decode('utf-8', errors='ignore')
        
    # Check for Unix-based systems (Linux and macOS)
    else:
        import tty
        import termios
        fd = sys.stdin.fileno()
        # Save the current terminal configuration
        old_settings = termios.tcgetattr(fd)
        try:
            # Switch terminal to raw mode to intercept raw keystrokes
            tty.setraw(fd)
            char = sys.stdin.read(1)
        finally:
            # Always restore original terminal settings
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return char

# ─────────────────────────────────────────────
#  CONFIGURATION — edit these if needed
# ─────────────────────────────────────────────
FILE_PATH         = 'unique_malaria_tweets.json'
BACKUP_PATH       = 'unique_malaria_tweets.BACKUP.json'
SESSION_LOG_PATH  = 'annotation_session_log.json'
SECOND_ANNOT_PATH = 'second_annotator_slice.json'   # exported for your colleague
IAA_EXPORT_PATH   = 'iaa_comparison.csv'

AUTO_SAVE_EVERY   = 5          # save after every N labels
SECOND_ANNOT_SIZE = 100        # tweets given to second annotator

CATEGORIES = {
    "1": "Symptoms & Burden",
    "2": "Treatment & Health System",
    "3": "Prevention & Awareness",
    "4": "Misinformation",
    "5": "Irrelevant",
}

# ─────────────────────────────────────────────
#  STATE  (module-level so atexit can reach it)
# ─────────────────────────────────────────────
df             = None
session_start  = None
session_labels = 0          # labels given THIS session

# ─────────────────────────────────────────────
#  SAVE / LOAD
# ─────────────────────────────────────────────

def load_data():
    global df
    if not os.path.exists(FILE_PATH):
        print(f"❌  File not found: {FILE_PATH}")
        sys.exit(1)

    df = pd.read_json(FILE_PATH)

    # Ensure required columns exist
    if 'label'      not in df.columns: df['label']      = -1
    if 'label_name' not in df.columns: df['label_name'] = ''
    if 'annotator'  not in df.columns: df['annotator']  = ''

    print(f"✅  Loaded {len(df)} tweets from {FILE_PATH}")


def save_progress(quiet=False):
    """Atomic save: write to backup first, then overwrite main file."""
    if df is None:
        return
    # Step 1 — write backup
    df.to_json(BACKUP_PATH, orient='records', indent=2)
    # Step 2 — overwrite main only after backup succeeded
    df.to_json(FILE_PATH, orient='records', indent=2)
    if not quiet:
        done  = int((df['label'] != -1).sum())
        total = len(df)
        print(f"💾  Saved  [{done}/{total} labeled]  →  {os.path.basename(FILE_PATH)}")


def emergency_save(signum=None, frame=None):
    """Called on Ctrl+C or SIGTERM — never lose work."""
    print("\n\n⚡  Interrupt detected — emergency saving...")
    save_progress()
    _write_session_log()
    print("✅  Safe to close. Resume anytime with start_labeling().")
    sys.exit(0)


# Register emergency save on process exit and SIGINT
atexit.register(save_progress)
signal.signal(signal.SIGINT, emergency_save)
try:
    signal.signal(signal.SIGTERM, emergency_save)
except (OSError, ValueError):
    pass   # not available in all environments (e.g. Jupyter threads)

# ─────────────────────────────────────────────
#  SESSION LOG
# ─────────────────────────────────────────────

def _load_session_log():
    if os.path.exists(SESSION_LOG_PATH):
        with open(SESSION_LOG_PATH) as f:
            return json.load(f)
    return {"sessions": [], "total_labeled_at_last_exit": 0}


def _write_session_log():
    if session_start is None:
        return
    log = _load_session_log()
    elapsed = time.time() - session_start
    done    = int((df['label'] != -1).sum()) if df is not None else 0
    log["sessions"].append({
        "date":           datetime.now().strftime("%Y-%m-%d %H:%M"),
        "duration_min":   round(elapsed / 60, 1),
        "labels_this_session": session_labels,
        "total_labeled":  done,
    })
    log["total_labeled_at_last_exit"] = done
    with open(SESSION_LOG_PATH, "w") as f:
        json.dump(log, f, indent=2)

# ─────────────────────────────────────────────
#  PROGRESS DASHBOARD
# ─────────────────────────────────────────────

def _format_eta(seconds):
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        return f"{int(seconds//60)}m {int(seconds%60)}s"
    else:
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        return f"{h}h {m}m"


def _dashboard(current_idx):
    """Print the full status header above each tweet."""
    done      = int((df['label'] != -1).sum())
    remaining = len(df) - done
    pct       = done / len(df) * 100

    # Speed & ETA
    elapsed   = time.time() - session_start if session_start else 1
    speed_raw = session_labels / elapsed if session_labels > 0 else None   # labels/sec
    if speed_raw and speed_raw > 0:
        eta_sec = remaining / speed_raw
        speed_str = f"{speed_raw * 60:.1f} tweets/min"
        eta_str   = _format_eta(eta_sec)
    else:
        speed_str = "–"
        eta_str   = "–"

    # Bar
    bar_len  = 30
    filled   = int(bar_len * done / len(df))
    bar      = "█" * filled + "░" * (bar_len - filled)

    # Session info
    elapsed_str = _format_eta(elapsed) if session_start else "–"

    print("=" * 62)
    print("  🦟  MALARIA TWEET ANNOTATOR  |  Nigeria Corpus")
    print("=" * 62)
    print(f"  Progress  │ [{bar}] {pct:.1f}%")
    print(f"  Labeled   │ {done} done  /  {remaining} remaining  /  {len(df)} total")
    print(f"  This session │ {session_labels} labels  │  Elapsed: {elapsed_str}")
    print(f"  Speed     │ {speed_str}   │   ETA: {eta_str}")
    print(f"  Tweet idx │ #{current_idx}  (row {done + 1} of {len(df)})")
    print("=" * 62)


def show_history(n=5):
    """Print last N labeled tweets — useful after resuming."""
    done = df[df['label'] != -1].tail(n)
    if done.empty:
        print("No labeled tweets yet.")
        return
    print(f"\n──── Last {len(done)} labeled tweets ────")
    for _, row in done.iterrows():
        lname = CATEGORIES.get(str(int(row['label'])), "?")
        snippet = str(row['text'])[:60].replace('\n', ' ')
        print(f"  [{int(row['label'])}] {lname:<14}  →  {snippet}…")
    print()

# ─────────────────────────────────────────────
#  MAIN LABELING LOOP
# ─────────────────────────────────────────────

def start_labeling(annotator_name: str = "main"):
    """
    Main annotation loop.

    Parameters
    ----------
    annotator_name : str
        'main'   — labels the full dataset (you)
        'second' — labels only the pre-exported 100-tweet slice
    """
    global session_start, session_labels, df

    load_data()

    if annotator_name == "second":
        _run_second_annotator()
        return

    session_start  = time.time()
    session_labels = 0
    label_counter  = 0           # counter toward next auto-save

    # Resume info
    done_before = int((df['label'] != -1).sum())
    if done_before > 0:
        print(f"\n▶  Resuming from tweet #{done_before + 1}  "
              f"({len(df) - done_before} still to go)\n")
        show_history()
        time.sleep(1.5)

    while True:
        clear_output(wait=True)
        unlabeled = df[df['label'] == -1]

        if unlabeled.empty:
            save_progress()
            _write_session_log()
            print("🎉  ALL DONE!  Every tweet has been labeled.")
            print(f"    Total labeled: {len(df)}")
            _print_distribution()
            break

        current_idx = unlabeled.index[0]

        # ── Dashboard ──
        _dashboard(current_idx)

        # ── Tweet ──
        tweet_text = str(df.at[current_idx, 'text'])
        print(f"\n  {tweet_text}\n")
        print("─" * 62)

        # ── Options ──
        opts = "  ".join([f"[{k}] {v}" for k, v in CATEGORIES.items()])
        print(f"  {opts}")
        print("  [u] Undo last   [h] History   [d] Distribution   [s] Save & Quit")
        print("─" * 62)

        choice = get_single_key("  Label: ").strip().lower()

        # ── Handle choice ──
        if choice == 's':
            save_progress()
            _write_session_log()
            print(f"\n  Session ended. Come back soon! "
                  f"({len(df) - int((df['label'] != -1).sum())} tweets remaining)")
            break

        elif choice == 'u':
            _undo_last()

        elif choice == 'h':
            clear_output(wait=True)
            show_history(10)
            input("  Press Enter to continue…")

        elif choice == 'd':
            clear_output(wait=True)
            _print_distribution()
            input("  Press Enter to continue…")

        elif choice in CATEGORIES:
            df.at[current_idx, 'label']      = int(choice)
            df.at[current_idx, 'label_name'] = CATEGORIES[choice]
            df.at[current_idx, 'annotator']  = annotator_name
            session_labels += 1
            label_counter  += 1

            if label_counter >= AUTO_SAVE_EVERY:
                save_progress(quiet=True)
                label_counter = 0

        elif choice == '':
            # Enter / blank → skip
            continue

        else:
            print("  ⚠  Invalid input. Try again.")
            time.sleep(0.8)


# ─────────────────────────────────────────────
#  UNDO
# ─────────────────────────────────────────────

def _undo_last():
    labeled = df[df['label'] != -1]
    if labeled.empty:
        print("  Nothing to undo.")
        time.sleep(0.8)
        return
    last_idx = labeled.index[-1]
    lname    = CATEGORIES.get(str(int(df.at[last_idx, 'label'])), "?")
    snippet  = str(df.at[last_idx, 'text'])[:55]
    df.at[last_idx, 'label']      = -1
    df.at[last_idx, 'label_name'] = ''
    df.at[last_idx, 'annotator']  = ''
    print(f"  ↩  Undone: [{lname}]  \"{snippet}…\"")
    time.sleep(1.2)

# ─────────────────────────────────────────────
#  DISTRIBUTION SUMMARY
# ─────────────────────────────────────────────

def _print_distribution():
    labeled = df[df['label'] != -1]
    if labeled.empty:
        print("  No labels yet.")
        return
    print(f"\n  ── Label Distribution ({len(labeled)} tweets) ──")
    counts = labeled['label'].value_counts().sort_index()
    for lbl, cnt in counts.items():
        name    = CATEGORIES.get(str(int(lbl)), "?")
        bar     = "█" * int(cnt / len(labeled) * 30)
        print(f"  [{int(lbl)}] {name:<14} {cnt:>4}  {bar}  ({cnt/len(labeled)*100:.1f}%)")
    print()

# ─────────────────────────────────────────────
#  SECOND ANNOTATOR SUPPORT
# ─────────────────────────────────────────────

def export_for_second_annotator(start_idx: int = 0):
    """
    Export SECOND_ANNOT_SIZE tweets (starting at start_idx) to a
    separate file for your second annotator.  Removes your labels
    so they annotate blindly.

    Usage:
        export_for_second_annotator()          # first 100 tweets
        export_for_second_annotator(200)       # tweets 200–299
    """
    load_data()
    slice_df = df.iloc[start_idx: start_idx + SECOND_ANNOT_SIZE].copy()
    slice_df['label']      = -1
    slice_df['label_name'] = ''
    slice_df['annotator']  = ''
    slice_df.to_json(SECOND_ANNOT_PATH, orient='records', indent=2)
    print(f"✅  Exported tweets [{start_idx}–{start_idx + SECOND_ANNOT_SIZE - 1}]"
          f"  →  {SECOND_ANNOT_PATH}")
    print(f"    Share this file with your second annotator.")
    print(f"    They should run:  start_labeling(annotator_name='second')")


def _run_second_annotator():
    """Inner loop for the second annotator working on their 100-tweet file."""
    global session_start, session_labels

    if not os.path.exists(SECOND_ANNOT_PATH):
        print(f"❌  {SECOND_ANNOT_PATH} not found.")
        print("    Ask the main annotator to run export_for_second_annotator() first.")
        return

    # Load their private file
    sa_df          = pd.read_json(SECOND_ANNOT_PATH)
    session_start  = time.time()
    session_labels = 0
    label_counter  = 0

    def _sa_save():
        sa_df.to_json(SECOND_ANNOT_PATH, orient='records', indent=2)

    print(f"✅  Loaded {len(sa_df)} tweets for second-annotator session.\n")

    while True:
        clear_output(wait=True)
        unlabeled = sa_df[sa_df['label'] == -1]

        if unlabeled.empty:
            _sa_save()
            print("🎉  You've finished all your tweets! Great work.")
            print(f"    Please send  '{SECOND_ANNOT_PATH}'  back to the main annotator.")
            break

        done = len(sa_df) - len(unlabeled)
        pct  = done / len(sa_df) * 100
        bar  = "█" * int(30 * done / len(sa_df)) + "░" * (30 - int(30 * done / len(sa_df)))

        elapsed = time.time() - session_start
        speed   = session_labels / elapsed if session_labels > 0 else None
        eta_str = _format_eta(len(unlabeled) / speed) if speed else "–"

        print("=" * 62)
        print("  🦟  SECOND ANNOTATOR MODE  |  Malaria Tweet Corpus")
        print("=" * 62)
        print(f"  Progress  │ [{bar}] {pct:.1f}%")
        print(f"  Labeled   │ {done} / {len(sa_df)}   │   ETA: {eta_str}")
        print("=" * 62)

        current_idx = unlabeled.index[0]
        print(f"\n  {str(sa_df.at[current_idx, 'text'])}\n")
        print("─" * 62)
        opts = "  ".join([f"[{k}] {v}" for k, v in CATEGORIES.items()])
        print(f"  {opts}")
        print("  [s] Save & Quit")
        print("─" * 62)

        choice = input("  Label: ").strip().lower()

        if choice == 's':
            _sa_save()
            print(f"  Saved. {len(unlabeled) - 1} tweets left for next time.")
            break
        elif choice in CATEGORIES:
            sa_df.at[current_idx, 'label']      = int(choice)
            sa_df.at[current_idx, 'label_name'] = CATEGORIES[choice]
            sa_df.at[current_idx, 'annotator']  = 'second'
            session_labels += 1
            label_counter  += 1
            if label_counter >= AUTO_SAVE_EVERY:
                _sa_save()
                label_counter = 0
        elif choice == '':
            continue
        else:
            print("  ⚠  Invalid. Try again.")
            time.sleep(0.8)


def compute_iaa():
    """
    Compute Cohen's Kappa between your labels and second annotator's labels
    on the overlapping 100 tweets. Exports a comparison CSV.

    Run AFTER the second annotator has finished and returned their file.
    """
    from sklearn.metrics import cohen_kappa_score
    load_data()

    if not os.path.exists(SECOND_ANNOT_PATH):
        print(f"❌  {SECOND_ANNOT_PATH} not found.")
        return

    sa_df = pd.read_json(SECOND_ANNOT_PATH)

    # Match on tweet text (robust to index shifts)
    merged = pd.merge(
        df[df['label'] != -1][['text', 'label']].rename(columns={'label': 'label_main'}),
        sa_df[sa_df['label'] != -1][['text', 'label']].rename(columns={'label': 'label_second'}),
        on='text', how='inner'
    )

    if len(merged) < 10:
        print(f"⚠  Only {len(merged)} matching labeled tweets found. "
              f"Check that files are aligned.")
        return

    kappa = cohen_kappa_score(merged['label_main'], merged['label_second'])
    merged.to_csv(IAA_EXPORT_PATH, index=False)

    print(f"\n  ── Inter-Annotator Agreement ──")
    print(f"  Overlapping tweets : {len(merged)}")
    print(f"  Cohen's Kappa      : {kappa:.4f}")
    print()
    if kappa >= 0.75:
        print("  ✅  Excellent agreement (κ ≥ 0.75) — proceed to training")
    elif kappa >= 0.60:
        print("  ⚠   Moderate agreement (0.60 ≤ κ < 0.75) — review disagreements")
        print("      Check the exported CSV and discuss edge cases")
    else:
        print("  ❌  Poor agreement (κ < 0.60) — revise annotation guidelines")
        print("      Re-annotate the overlapping set after clarifying rules")

    print(f"\n  Full comparison saved to: {IAA_EXPORT_PATH}")
    print("  Disagreements:")
    bad = merged[merged['label_main'] != merged['label_second']]
    print(f"  {len(bad)} disagreements out of {len(merged)} tweets "
          f"({len(bad)/len(merged)*100:.1f}%)\n")
    for _, row in bad.head(5).iterrows():
        m = CATEGORIES.get(str(int(row['label_main'])),    '?')
        s = CATEGORIES.get(str(int(row['label_second'])),  '?')
        print(f"  Main:{m:<14}  2nd:{s:<14}  \"{str(row['text'])[:45]}…\"")


# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────

import argparse
def main():
    parser = argparse.ArgumentParser(description="Malaria Tweet Annotator")
    parser.add_argument("-s", "--start", action="store_true", help="Start annotation session")

    args = parser.parse_args()


    if args.start:
        start_labeling()

if __name__ == "__main__":
    main()
if 0:

    print(__doc__)
    print("  Quick start:")
    print("    start_labeling()                         # you annotate")
    print("    export_for_second_annotator()            # give colleague 100 tweets")
    print("    start_labeling(annotator_name='second')  # colleague runs this")
    print("    compute_iaa()                            # after colleague returns file")
    print()