"""
test_data_generator.py
Creates all test data files required by the SMS test suite.

Uses static, hard-coded test data.

Call generate_all() once at session start — files are written to tests/test_data/.
"""
import os
import csv

try:
    import openpyxl
    from openpyxl import Workbook
    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "tests", "test_data")

# Column headers for Sender ID import template
SENDER_ID_HEADERS = ["Sender ID", "Entity ID", "Country Code", "Description"]

# Column headers for the Template bulk-upload file — must match the live
# app's actual import format exactly (confirmed against a real sample
# provided by the user), not a guessed/generic set of names.
TEMPLATE_HEADERS = [
    "sender_id", "entity_id", "template_dlt_id", "template_name",
    "template_product", "content_type", "template_content", "template_sample",
]


def _ensure_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def _path(name):
    return os.path.join(DATA_DIR, name)


def _tmp_path(final_path):
    """Per-worker, per-process temp path for the atomic-write pattern used
    throughout this module — see _write_csv's docstring for why."""
    from utils.parallel import worker_id
    return f"{final_path}.{worker_id()}.{os.getpid()}.tmp"


# ══════════════════════════════════════════════════════════════════════════════
# File helpers
# ══════════════════════════════════════════════════════════════════════════════

def _write_csv(filename, rows, headers=None):
    """Writes to a per-worker temp file, then os.replace()s it onto the
    final shared path. generate_all() is called once per test MODULE (every
    SMS flow file's autouse `generate_test_data` fixture), and under
    parallel xdist execution several worker processes can call it at the
    same moment for the SAME shared file (these are static, deterministic
    files, not per-worker data — e.g. valid_template.xlsx). Without this,
    two workers writing the same path concurrently could race: one process
    reading the file mid-write by another. os.replace() is atomic on both
    POSIX and Windows, so every reader always sees either the fully-old or
    fully-new file, never a partial one."""
    from utils.parallel import worker_id
    final_path = _path(filename)
    tmp_path = f"{final_path}.{worker_id()}.{os.getpid()}.tmp"
    with open(tmp_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if headers:
            writer.writerow(headers)
        writer.writerows(rows)
    os.replace(tmp_path, final_path)


def _write_xlsx(filename, rows, headers=None):
    if not HAS_OPENPYXL:
        _write_csv(filename, rows, headers)
        return
    from utils.parallel import worker_id
    final_path = _path(filename)
    tmp_path = f"{final_path}.{worker_id()}.{os.getpid()}.tmp"
    wb = Workbook()
    ws = wb.active
    if headers:
        ws.append(headers)
    for row in rows:
        ws.append(list(row))
    wb.save(tmp_path)
    os.replace(tmp_path, final_path)


# ══════════════════════════════════════════════════════════════════════════════
# Sender ID file generators
# ══════════════════════════════════════════════════════════════════════════════

def gen_valid_sender_id_xlsx(rows):
    _write_xlsx("valid_sender_id.xlsx", rows, SENDER_ID_HEADERS)


def gen_valid_sender_id_csv(rows):
    _write_csv("valid_sender_id.csv", rows[:3], SENDER_ID_HEADERS)


def gen_invalid_format_pdf():
    final_path = _path("invalid_format.pdf")
    tmp_path = _tmp_path(final_path)
    with open(tmp_path, "wb") as f:
        f.write(b"%PDF-1.4 fake content for format rejection test")
    os.replace(tmp_path, final_path)


def gen_large_file_xlsx():
    """Excel file exceeding 5 MB (~80 000 rows)."""
    final_path = _path("large_file.xlsx")
    tmp_path = _tmp_path(final_path)
    if not HAS_OPENPYXL:
        with open(tmp_path, "w", encoding="utf-8") as f:
            f.write(",".join(SENDER_ID_HEADERS) + "\n")
            for i in range(80000):
                f.write(f"SID{i:06d},ENT001,IN,Description {i}\n")
        os.replace(tmp_path, final_path)
        return
    wb = Workbook(write_only=True)
    ws = wb.create_sheet()
    ws.append(SENDER_ID_HEADERS)
    for i in range(80000):
        ws.append([f"SID{i:06d}", "ENT001", "IN", f"Description {i}"])
    wb.save(tmp_path)
    os.replace(tmp_path, final_path)


def gen_duplicate_sender_ids_csv(rows):
    _write_csv("duplicate_sender_ids.csv", rows, SENDER_ID_HEADERS)


def gen_invalid_length_sender_ids_csv(rows):
    _write_csv("invalid_length_sender_ids.csv", rows, SENDER_ID_HEADERS)


def gen_special_chars_sender_ids_csv(rows):
    _write_csv("special_chars_sender_ids.csv", rows, SENDER_ID_HEADERS)


def gen_missing_entity_id_col_csv(rows):
    incomplete_headers = ["Sender ID", "Country Code", "Description"]
    _write_csv("missing_entity_id_col.csv", rows, incomplete_headers)


def gen_invalid_country_code_csv(rows):
    _write_csv("invalid_country_code.csv", rows, SENDER_ID_HEADERS)


def gen_mixed_valid_invalid_csv(rows):
    _write_csv("mixed_valid_invalid.csv", rows, SENDER_ID_HEADERS)


# ══════════════════════════════════════════════════════════════════════════════
# Contact file generators
# ══════════════════════════════════════════════════════════════════════════════

def gen_valid_contacts_csv(numbers):
    rows = [[n] for n in numbers]
    _write_csv("valid_contacts.csv", rows, ["Phone Number"])


def gen_invalid_contacts_csv(numbers):
    rows = [[n] for n in numbers]
    _write_csv("invalid_contacts.csv", rows, ["Phone Number"])


# ══════════════════════════════════════════════════════════════════════════════
# Template file generators
# ══════════════════════════════════════════════════════════════════════════════

def gen_valid_template_xlsx(templates):
    """*templates* is a list of dicts keyed exactly like TEMPLATE_HEADERS
    (sender_id, entity_id, template_dlt_id, template_name, template_product,
    content_type, template_content, template_sample) — written out in that
    column order so the file matches the live app's real import format."""
    rows = [
        [
            t["sender_id"], t["entity_id"], t["template_dlt_id"],
            t["template_name"], t["template_product"], t["content_type"],
            t["template_content"], t.get("template_sample", ""),
        ]
        for t in templates
    ]
    _write_xlsx("valid_template.xlsx", rows, TEMPLATE_HEADERS)


def gen_large_template_xlsx():
    """Template file exceeding 10 MB."""
    final_path = _path("large_template.xlsx")
    tmp_path = _tmp_path(final_path)
    if not HAS_OPENPYXL:
        with open(tmp_path, "w", encoding="utf-8") as f:
            f.write(",".join(TEMPLATE_HEADERS) + "\n")
            for i in range(150000):
                f.write(f"DUMMY,1701158046444780002,DLT{i},Tmpl{i},transactional,N,Content row {i},\n")
        os.replace(tmp_path, final_path)
        return
    wb = Workbook(write_only=True)
    ws = wb.create_sheet()
    ws.append(TEMPLATE_HEADERS)
    for i in range(150000):
        ws.append([
            "DUMMY", "1701158046444780002", f"DLT{i}", f"Tmpl{i}",
            "transactional", "N", f"Content row {i}", "",
        ])
    wb.save(tmp_path)
    os.replace(tmp_path, final_path)


def gen_invalid_template_format():
    final_path = _path("invalid_template_format.pdf")
    tmp_path = _tmp_path(final_path)
    with open(tmp_path, "wb") as f:
        f.write(b"%PDF-1.4 fake file for format rejection test")
    os.replace(tmp_path, final_path)


# ══════════════════════════════════════════════════════════════════════════════
# Master generator
# ══════════════════════════════════════════════════════════════════════════════

def generate_all():
    """
    Generate every test data file.
    Uses static, hard-coded test data.
    Called once per test session from conftest.py.
    """
    _ensure_dir()

    sid = {
        "valid": [
            ["AUTOTEST1", "ENT001", "IN", "Auto test sender 1"],
            ["AUTOTEST2", "ENT001", "IN", "Auto test sender 2"],
            ["AUTOTEST3", "ENT002", "SG", "Auto test sender 3"],
            ["AUTOTEST4", "ENT002", "SG", "Auto test sender 4"],
            ["AUTOTEST5", "ENT003", "MY", "Auto test sender 5"],
        ],
        "invalid_length": [
            ["AB",            "ENT001", "IN", "Too short (2 chars)"],
            ["A",             "ENT001", "IN", "Too short (1 char)"],
            ["TOOLONGSIDXX",  "ENT001", "IN", "Too long (12 chars)"],
            ["VERYLONGID123", "ENT001", "IN", "Too long (13 chars)"],
        ],
        "invalid_chars": [
            ["TEST!@#", "ENT001", "IN", "Special chars"],
            ["SID$%^&", "ENT001", "IN", "Special chars 2"],
            ["ID<>?/",  "ENT001", "IN", "Special chars 3"],
        ],
        "duplicates": [
            ["DUPTEST1", "ENT001", "IN", "Duplicate test 1"],
            ["DUPTEST1", "ENT001", "IN", "Duplicate test 1 again"],
            ["DUPTEST2", "ENT001", "IN", "Duplicate test 2"],
            ["DUPTEST2", "ENT002", "SG", "Duplicate test 2 again"],
        ],
        "mixed": [
            ["MIXVALID1", "ENT001", "IN", "Valid row"],
            ["MIXVALID2", "ENT001", "SG", "Valid row"],
            ["AB",        "ENT001", "IN", "Invalid — too short"],
            ["TEST!@#",   "ENT001", "IN", "Invalid — special chars"],
            ["MIXVALID3", "ENT002", "MY", "Valid row"],
        ],
        "missing_col": [
            ["MISSCOL1", "IN", "Missing entity ID"],
            ["MISSCOL2", "SG", "Missing entity ID 2"],
        ],
        "invalid_country": [
            ["CNTTEST1", "ENT001", "XX", "Invalid country XX"],
            ["CNTTEST2", "ENT001", "ZZ", "Invalid country ZZ"],
            ["CNTTEST3", "ENT001", "99", "Invalid country 99"],
        ],
    }
    # Real bulk-upload rows in the live app's actual import format (provided
    # by the user) — entity_id is the account's fixed entity ID, sender_id
    # alternates DUMMY (transactional) / AM-SMS (promotional), content_type
    # is N (plain/GSM) or U (Unicode, e.g. the Hindi row below).
    _ENTITY_ID = "1701158046444780002'"
    tmpl = {
        "valid": [
            {"sender_id": "DUMMY", "entity_id": _ENTITY_ID, "template_dlt_id": "1707161580895840027'",
             "template_name": "Template1", "template_product": "transactional", "content_type": "N",
             "template_content": "Dear Candidate, your password has been reset. Your new password is {{1}} - GTS",
             "template_sample": "Dear Candidate, your password has been reset. Your new password is 9876 - GTS"},
            {"sender_id": "AM-SMS", "entity_id": _ENTITY_ID, "template_dlt_id": "1707161580898730014'",
             "template_name": "Template2", "template_product": "promotional", "content_type": "U",
             "template_content": "प्रिय उम्मीदवार, आपका पासवर्ड रीसेट कर दिया गया है। आपका नया पासवर्ड {{1}} है - GTS",
             "template_sample": ""},
            {"sender_id": "DUMMY", "entity_id": _ENTITY_ID, "template_dlt_id": "8274981748172940",
             "template_name": "Template3", "template_product": "transactional", "content_type": "N",
             "template_content": "Hello {name}, your OTP is {otp}", "template_sample": ""},
            {"sender_id": "AM-SMS", "entity_id": _ENTITY_ID, "template_dlt_id": "12849821798217800",
             "template_name": "Template4", "template_product": "promotional", "content_type": "N",
             "template_content": "Get 50% off today! Visit our store.", "template_sample": ""},
            {"sender_id": "DUMMY", "entity_id": _ENTITY_ID, "template_dlt_id": "812349821491874",
             "template_name": "Template5", "template_product": "transactional", "content_type": "N",
             "template_content": "Your OTP is {otp}. Valid for 10 minutes.", "template_sample": ""},
        ],
        "no_vars": [
            {"sender_id": "AM-SMS", "entity_id": _ENTITY_ID, "template_dlt_id": "8274981748172940",
             "template_name": "Template6", "template_product": "promotional", "content_type": "N",
             "template_content": "Hello {name}, your OTP is {otp}", "template_sample": ""},
            {"sender_id": "DUMMY", "entity_id": _ENTITY_ID, "template_dlt_id": "12849821798217800",
             "template_name": "Template7", "template_product": "transactional", "content_type": "N",
             "template_content": "Get 50% off today! Visit our store.", "template_sample": ""},
            {"sender_id": "AM-SMS", "entity_id": _ENTITY_ID, "template_dlt_id": "812349821491874",
             "template_name": "Template8", "template_product": "promotional", "content_type": "N",
             "template_content": "Your OTP is {otp}. Valid for 10 minutes.", "template_sample": ""},
            {"sender_id": "DUMMY", "entity_id": _ENTITY_ID, "template_dlt_id": "8274981748172940",
             "template_name": "Template9", "template_product": "transactional", "content_type": "N",
             "template_content": "Hello {name}, your OTP is {otp}", "template_sample": ""},
            {"sender_id": "AM-SMS", "entity_id": _ENTITY_ID, "template_dlt_id": "12849821798217800",
             "template_name": "Template10", "template_product": "promotional", "content_type": "N",
             "template_content": "Get 50% off today! Visit our store.", "template_sample": ""},
            {"sender_id": "DUMMY", "entity_id": _ENTITY_ID, "template_dlt_id": "812349821491874",
             "template_name": "Template11", "template_product": "transactional", "content_type": "N",
             "template_content": "Your OTP is {otp}. Valid for 10 minutes.", "template_sample": ""},
        ],
    }
    ctct = {
        "valid": [
            "917973059161", "917206955509", "917015571043",
            "919463126539", "919464980661", "919415643267",
            "919854673456", "918727973010", "918570810853",
            "919034424020", "917815578155",
        ],
        "invalid": ["12345", "abcdefghij", "00000", "INVALID"],
    }

    # Write Sender ID files
    gen_valid_sender_id_xlsx(sid["valid"])
    gen_valid_sender_id_csv(sid["valid"])
    gen_invalid_format_pdf()
    gen_large_file_xlsx()
    gen_duplicate_sender_ids_csv(sid["duplicates"])
    gen_invalid_length_sender_ids_csv(sid["invalid_length"])
    gen_special_chars_sender_ids_csv(sid["invalid_chars"])
    gen_missing_entity_id_col_csv(sid["missing_col"])
    gen_invalid_country_code_csv(sid["invalid_country"])
    gen_mixed_valid_invalid_csv(sid["mixed"])

    # Write Contact files
    gen_valid_contacts_csv(ctct["valid"])
    gen_invalid_contacts_csv(ctct["invalid"])

    # Write Template files
    all_templates = tmpl.get("valid", []) + tmpl.get("no_vars", [])
    gen_valid_template_xlsx(all_templates)
    gen_large_template_xlsx()
    gen_invalid_template_format()

    print(f"\n[TestData] All files generated in: {DATA_DIR}")
