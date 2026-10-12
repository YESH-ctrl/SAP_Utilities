"""
Single-Command Master Release Verification Script for SAP Utilities RAG Engine V5.5.
Executes:
  1. Corpus SHA-256 and count verification
  2. Benchmark SHA-256 dataset verification
  3. Dependency environment check
  4. Unit test suite execution (pytest)
  5. API robustness and edge case validation
  6. Production smoke test suite

Returns EXIT 0 on PASS, non-zero on FAIL.
"""

import sys
import subprocess
import logging

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s]: %(message)s")
logger = logging.getLogger("master_release_verification")

def run_command(name: str, cmd: list) -> bool:
    logger.info(f"\n=========================================================")
    logger.info(f"   STEP: {name}")
    logger.info(f"=========================================================")
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(res.stdout)
        logger.info(f" -> PASS: {name} completed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(e.stdout)
        print(e.stderr)
        logger.error(f" -> FAIL: {name} failed with exit code {e.returncode}!")
        return False

def main():
    logger.info("=========================================================")
    logger.info("  SAP UTILITIES RAG V5.5 - MASTER RELEASE VERIFICATION  ")
    logger.info("=========================================================")

    python_exe = sys.executable

    steps = [
        ("1. Frozen Release Artifact Verification", [python_exe, "scripts/verify_v55_release_artifacts.py"]),
        ("2. Pytest Unit & Integration Test Suite", [python_exe, "-m", "pytest", "tests/"]),
        ("3. Functional API Robustness & Input Abuse Suite", [python_exe, "scripts/test_v55_api_robustness.py"]),
        ("4. Production Smoke Test Suite", [python_exe, "scripts/test_v55_smoke_test.py"]),
        ("5. Failure Injection & Resilience Test Suite", [python_exe, "scripts/test_v55_failure_injection.py"])
    ]

    all_pass = True
    for name, cmd in steps:
        success = run_command(name, cmd)
        if not success:
            all_pass = False
            break

    logger.info("\n=========================================================")
    if all_pass:
        logger.info("   FINAL RESULT: EXIT 0 - RELEASE VALIDATION PASSED      ")
        logger.info("=========================================================")
        sys.exit(0)
    else:
        logger.error("   FINAL RESULT: EXIT 1 - RELEASE BLOCKED!             ")
        logger.error("=========================================================")
        sys.exit(1)

if __name__ == "__main__":
    main()
