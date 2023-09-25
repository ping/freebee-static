import argparse
import json
import logging
import random
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List

logger = logging.getLogger(__file__)
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
logger.addHandler(ch)
logger.setLevel(logging.INFO)


@dataclass
class PuzzleWord:
    word: str
    letters: List[str]


def get_filtered_words(wordlist_file) -> List[PuzzleWord]:
    filtered_words: List[PuzzleWord] = []
    with open(wordlist_file, "r", encoding="utf-8") as f:
        while True:
            word = f.readline().strip()
            if not word:
                break
            word = word[1:-1]
            if len(word) > 15 or len(word) < 4:
                continue
            puzzle_word = PuzzleWord(
                word=word, letters=sorted(list(set([a for a in word])))
            )
            filtered_words.append(puzzle_word)
    return filtered_words


def get_puzzle_words(filtered_words: List[PuzzleWord]) -> List[PuzzleWord]:
    puzzle_words: List[PuzzleWord] = []
    for fw in filtered_words:
        if len(fw.letters) != 7:
            continue
        if fw.word.endswith("s") and fw.word[-2:-1] not in "aeiou":
            # stupid filter for plurals
            continue
        puzzle_words.append(fw)
    return puzzle_words


def score(pz: PuzzleWord, letters: List[str]):
    if len(pz.word) == 4:
        return 1
    if len(pz.letters) == len(letters):
        return len(pz.word) + 7
    return len(pz.word)


def generate_puzzle_word(
    puzzle_words: List[PuzzleWord], filtered_words: List[PuzzleWord]
) -> Dict:
    attempt_count = 0
    while True:
        attempt_count += 1
        valid_puzzle_guesses: List[PuzzleWord] = []
        puzzle_word: PuzzleWord = random.choice(puzzle_words)
        centre_letter: str = random.choice(puzzle_word.letters)
        for w in filtered_words:
            if centre_letter not in w.letters:
                continue
            if [a for a in w.letters if (a not in puzzle_word.letters)]:
                continue
            valid_puzzle_guesses.append(w)
        total_score = sum(
            [score(guess, puzzle_word.letters) for guess in valid_puzzle_guesses]
        )
        if total_score < 300 and 20 <= len(valid_puzzle_guesses) <= 200:
            break
        if attempt_count >= 50:
            return {}

    return {
        "letters": "".join([a for a in puzzle_word.letters if a != centre_letter]),
        "center": centre_letter,
        "words": len(valid_puzzle_guesses),
        "total": total_score,
        "wordlist": [w.word for w in valid_puzzle_guesses],
    }


def valid_day(value: str) -> str:
    """
    Validate a day argument from the cli.

    :param value:
    :return:
    """

    try:
        start_date = datetime.strptime(value, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        raise argparse.ArgumentTypeError(f'"{value}" is not a valid date format')

    now_utc = datetime.now(tz=timezone.utc)
    if start_date > now_utc.replace(hour=0, minute=0, second=0, microsecond=0):
        raise argparse.ArgumentTypeError(f'"{value}" is in the future')

    return value


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("wordlist", type=str, help="Path to wordlist file")
    parser.add_argument("start_date", type=valid_day, help="Start date")
    parser.add_argument("output_folder", type=str, help="Output folder path")

    args = parser.parse_args()

    start_date = datetime.strptime(args.start_date, "%Y-%m-%d").replace(
        tzinfo=timezone.utc
    )
    output_folder = Path(args.output_folder)
    if not output_folder.exists():
        output_folder.mkdir(parents=True, exist_ok=True)

    fw = get_filtered_words(args.wordlist)
    pz = get_puzzle_words(fw)

    now = datetime.now(tz=timezone.utc)
    for d in range((now - start_date).days + 2):
        gen_date = start_date + timedelta(days=d)
        output_filename = output_folder.joinpath(f'{gen_date.strftime("%Y%m%d")}.json')
        if output_filename.exists():
            continue
        output = generate_puzzle_word(pz, fw)
        if not output:
            logger.warning(f"Unable to generate a puzzle for {output_filename}")
            continue
        logger.info(f"Generating {output_filename}")
        with output_filename.open("w", encoding="utf-8") as fp:
            json.dump(output, fp, separators=(",", ":"))
