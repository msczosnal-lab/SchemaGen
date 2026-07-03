"""PRZESTARZALE. Usuwanie + retag obsluguje teraz scripts/apply_reassign.py.

Przegladarka scripts/element_review.py wypluwa `reassignments.json` (retag ORAZ
usun przez sentinel new_tag="__DELETE__"). Zastosuj:

    python scripts/apply_reassign.py --file reassignments.json          # dry-run
    python scripts/apply_reassign.py --file reassignments.json --apply  # zapis (+backup)
"""
import sys

if __name__ == "__main__":
    print(__doc__)
    sys.exit(0)
