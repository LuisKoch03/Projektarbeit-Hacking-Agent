"""Tests for the Hashcat tool argument handling."""

from pathlib import Path
import os
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from hacking_agent.tools.hashcat import list_hashcat_wordlists, run_hashcat


class RunHashcatTests(unittest.TestCase):
    def test_direct_hash_with_mask_uses_temporary_file(self) -> None:
        captured_arguments: list[str] = []
        temporary_hash_path: Path | None = None

        def fake_run(arguments: list[str]) -> subprocess.CompletedProcess[str]:
            nonlocal captured_arguments, temporary_hash_path
            captured_arguments = arguments
            matches = list(work_directory.rglob("hash.txt"))
            self.assertEqual(len(matches), 1)
            temporary_hash_path = matches[0]
            self.assertTrue(temporary_hash_path.is_file())
            self.assertEqual(temporary_hash_path.read_text(encoding="utf-8"), "abc123\n")
            return subprocess.CompletedProcess(arguments, 0, stdout="Recovered", stderr="")

        with tempfile.TemporaryDirectory() as temp_dir:
            work_directory = Path(temp_dir)
            with (
                patch.dict(os.environ, {"HASHCAT_WORK_DIR": temp_dir}),
                patch("hacking_agent.tools.hashcat._run_hashcat", side_effect=fake_run),
            ):
                result = run_hashcat.func(
                    hash_mode=0,
                    hash_value="abc123",
                    attack_mode=3,
                    mask="?d?d?d?d",
                )

        self.assertEqual(result, "Recovered")
        self.assertEqual(captured_arguments[:4], ["-m", "0", "-a", "3"])
        self.assertTrue(captured_arguments[6].startswith("/data/work/hacking-agent-hashcat-"))
        self.assertTrue(captured_arguments[6].endswith("/hash.txt"))
        self.assertEqual(captured_arguments[7], "?d?d?d?d")
        self.assertIn("--potfile-disable", captured_arguments)
        self.assertIsNotNone(temporary_hash_path)
        self.assertFalse(temporary_hash_path.exists())

    def test_hash_file_uses_configured_wordlist_in_dictionary_mode(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            work_directory = root / "work"
            wordlist_directory = root / "wordlists"
            work_directory.mkdir()
            wordlist_directory.mkdir()
            hash_path = work_directory / "hashes.txt"
            wordlist_path = wordlist_directory / "words.txt"
            hash_path.write_text("abc123\n", encoding="utf-8")
            wordlist_path.write_text("password\n", encoding="utf-8")

            completed = subprocess.CompletedProcess([], 0, stdout="Done", stderr="")
            with (
                patch.dict(
                    os.environ,
                    {
                        "HASHCAT_WORK_DIR": str(work_directory),
                        "HASHCAT_WORDLIST_DIR": str(wordlist_directory),
                        "HASHCAT_WORDLIST": "words.txt",
                    },
                ),
                patch(
                    "hacking_agent.tools.hashcat._run_hashcat",
                    return_value=completed,
                ) as mocked_run,
            ):
                result = run_hashcat.func(hash_mode=0, hash_file=str(hash_path))

        self.assertEqual(result, "Done")
        arguments = mocked_run.call_args.args[0]
        self.assertEqual(arguments[:4], ["-m", "0", "-a", "0"])
        self.assertEqual(
            arguments[6:8],
            ["/data/work/hashes.txt", "/data/wordlists/words.txt"],
        )

    def test_dictionary_mode_uses_wordlist_from_environment(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            work_directory = root / "work"
            wordlist_directory = root / "wordlists"
            work_directory.mkdir()
            wordlist_directory.mkdir()
            wordlist_path = wordlist_directory / "default-words.txt"
            wordlist_path.write_text("password\n", encoding="utf-8")
            completed = subprocess.CompletedProcess([], 0, stdout="Done", stderr="")

            with (
                patch.dict(
                    os.environ,
                    {
                        "HASHCAT_WORK_DIR": str(work_directory),
                        "HASHCAT_WORDLIST_DIR": str(wordlist_directory),
                        "HASHCAT_WORDLIST": "default-words.txt",
                    },
                ),
                patch(
                    "hacking_agent.tools.hashcat._run_hashcat",
                    return_value=completed,
                ) as mocked_run,
            ):
                result = run_hashcat.func(hash_mode=0, hash_value="abc123")

        self.assertEqual(result, "Done")
        arguments = mocked_run.call_args.args[0]
        self.assertEqual(arguments[7], "/data/wordlists/default-words.txt")

    def test_dictionary_mode_selects_name_inside_configured_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            directory = root / "wordlists"
            work_directory = root / "work"
            directory.mkdir()
            work_directory.mkdir()
            wordlist_path = directory / "john.lst"
            wordlist_path.write_text("password\n", encoding="utf-8")
            completed = subprocess.CompletedProcess([], 0, stdout="Done", stderr="")

            with (
                patch.dict(
                    os.environ,
                    {
                        "HASHCAT_WORDLIST_DIR": str(directory),
                        "HASHCAT_WORK_DIR": str(work_directory),
                    },
                ),
                patch(
                    "hacking_agent.tools.hashcat._run_hashcat",
                    return_value=completed,
                ) as mocked_run,
            ):
                result = run_hashcat.func(
                    hash_mode=0,
                    hash_value="abc123",
                    wordlist_name="john.lst",
                )

        self.assertEqual(result, "Done")
        self.assertEqual(
            mocked_run.call_args.args[0][7], "/data/wordlists/john.lst"
        )

    def test_wordlist_name_cannot_leave_configured_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.dict(os.environ, {"HASHCAT_WORDLIST_DIR": temp_dir}):
                result = run_hashcat.func(
                    hash_mode=0,
                    hash_value="abc123",
                    wordlist_name="../outside.txt",
                )

        self.assertIn("must stay inside", result)

    def test_lists_files_in_configured_wordlist_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            (directory / "rockyou.txt").write_text("password\n", encoding="utf-8")
            (directory / "nested").mkdir()

            with patch.dict(os.environ, {"HASHCAT_WORDLIST_DIR": temp_dir}):
                result = list_hashcat_wordlists.invoke({})

        self.assertIn("rockyou.txt", result)
        self.assertNotIn("nested", result)

    def test_dictionary_mode_explains_missing_default_wordlist(self) -> None:
        with patch.dict(os.environ, {"HASHCAT_WORDLIST": ""}):
            result = run_hashcat.func(hash_mode=0, hash_value="abc123")

        self.assertIn("Set HASHCAT_WORDLIST", result)

    def test_requires_exactly_one_hash_source(self) -> None:
        no_source = run_hashcat.func(hash_mode=0)
        both_sources = run_hashcat.func(
            hash_mode=0,
            hash_file="hashes.txt",
            hash_value="abc123",
        )

        self.assertIn("exactly one", no_source)
        self.assertIn("exactly one", both_sources)

    def test_mask_attack_requires_mask(self) -> None:
        missing_mask = run_hashcat.func(
            hash_mode=0, hash_value="abc123", attack_mode=3
        )

        self.assertIn("requires a mask", missing_mask)


if __name__ == "__main__":
    unittest.main()
