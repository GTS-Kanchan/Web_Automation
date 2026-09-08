"""
test_data_generator.py
Creates all test data files required by the SMS test suite.

Uses static, hard-coded test data.

Call generate_all() once at session start — files are written to tests/test_data/.
"""
import os
import csv
import time

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

def _write_csv(filename, rows, headers=None, directory=None):
    """Writes to a per-worker temp file, then os.replace()s it onto the
    final path (DATA_DIR/filename, or `directory`/filename when given).
    generate_all() is called once per test MODULE (every SMS flow file's
    autouse `generate_test_data` fixture), and under parallel xdist
    execution several worker processes can call it at the same moment for
    the SAME shared file (these are static, deterministic files, not
    per-worker data — e.g. valid_template.xlsx). Without this, two workers
    writing the same path concurrently could race: one process reading the
    file mid-write by another. os.replace() is atomic on both POSIX and
    Windows, so every reader always sees either the fully-old or
    fully-new file, never a partial one.

    That atomicity guarantee is NOT enough on its own for a file whose
    *content* is randomized per call (see gen_sender_id_sample_csv()) — two
    workers can each atomically write a COMPLETE but DIFFERENT random
    payload to the same shared path, and a test that reads the file once
    for verification and lets it be read again (e.g. Playwright's
    set_input_files()) for upload can end up acting on two different
    writers' bytes across those two reads, even though every individual
    write was torn-free. The `directory` param lets a caller sidestep that
    class of bug entirely by pointing at a worker-scoped directory (see
    utils.parallel.worker_scoped_dir) so two workers never share the path
    at all, rather than merely never observing a torn write on it."""
    from utils.parallel import worker_id
    final_path = os.path.join(directory or DATA_DIR, filename)
    tmp_path = f"{final_path}.{worker_id()}.{os.getpid()}.tmp"
    with open(tmp_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if headers:
            writer.writerow(headers)
        writer.writerows(rows)
    for attempt in range(5):
        try:
            os.replace(tmp_path, final_path)
            break
        except PermissionError:
            if attempt == 4:
                raise
            time.sleep(0.1)


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
    for attempt in range(5):
        try:
            os.replace(tmp_path, final_path)
            break
        except PermissionError:
            if attempt == 4:
                raise
            time.sleep(0.1)


# ══════════════════════════════════════════════════════════════════════════════
# Sender ID file generators
# ══════════════════════════════════════════════════════════════════════════════

def gen_valid_sender_id_xlsx(rows):
    _write_xlsx("valid_sender_id.xlsx", rows, SENDER_ID_HEADERS)


def gen_valid_sender_id_csv(rows):
    _write_csv("valid_sender_id.csv", rows[:3], SENDER_ID_HEADERS)


# Column headers for sender_id_sample.csv -- CONFIRMED from a real sample
# file (Sender_ID, Type, Country_Code, Entity_ID). This is a DIFFERENT
# schema from SENDER_ID_HEADERS above (that one matches this app's own
# bulk-import TEMPLATE headers; sender_id_sample.csv is a separate,
# hand-provided real upload sample used specifically by
# tests/sms/sender_id/test_sms_sender_id.py's
# TestUploadSenderIds.test_upload_csv_and_verify_in_list).
SENDER_ID_SAMPLE_HEADERS = ["Sender_ID", "Type", "Country_Code", "Entity_ID"]


def sender_id_sample_csv_path():
    """Path to THIS WORKER's own sender_id_sample.csv, under
    DATA_DIR/<worker_id>/ (see utils.parallel.worker_scoped_dir) rather
    than the single shared DATA_DIR/sender_id_sample.csv every worker used
    to write. worker_id() is fixed for the lifetime of one xdist worker
    process, so this path is safe to compute once at import time -- unlike
    the file's own CONTENT, which must never be read at import time (see
    the comment above TestUploadSenderIds in test_sms_sender_id.py).

    Why this needs to be worker-scoped at all: a real run showed
    test_upload_csv_and_verify_in_list uploading one set of Sender_IDs but
    verifying a completely different set that was never uploaded. Root
    cause -- the test reads the CSV once (to know what to verify) and
    Playwright's upload_file()/set_input_files() reads the SAME shared
    path a second, independent time (to actually upload). generate_all()
    runs once per test MODULE, and under `--dist loadscope` a DIFFERENT
    module on a DIFFERENT worker can call it concurrently -- if that
    worker's gen_sender_id_sample_csv() call landed in the gap between
    this test's two reads, the bytes verified and the bytes uploaded came
    from two different writers. Routing every worker to its own
    subdirectory removes the shared path entirely, so no other worker can
    ever land a write in between this worker's own two reads."""
    from utils.parallel import worker_scoped_dir
    return os.path.join(worker_scoped_dir(DATA_DIR), "sender_id_sample.csv")


def gen_sender_id_sample_csv():
    """sender_id_sample.csv -- the 3-row bulk-upload sample
    test_upload_csv_and_verify_in_list uploads and then verifies every row
    landed in the Sender ID list. Written to THIS WORKER's own
    subdirectory (see sender_id_sample_csv_path()) rather than the shared
    DATA_DIR, so two workers regenerating it concurrently can never race
    on the same path.

    UPDATED (2026-09): this file used to be committed as static, hand-placed
    content with a FIXED Sender_ID triple (GYAFZG/GULWRA/QKQKON) that
    generate_all() never touched at all -- every run re-uploaded the exact
    same 3 sender IDs. That worked the very first time this file was used
    against a given environment (fresh IDs, fresh rows), but every run
    after that was re-submitting IDs that already existed from the
    previous run, and this app's response to an all-duplicate-rows import
    is NOT the same "success" response a genuinely-new import gets --
    that's what caused test_upload_csv_and_verify_in_list to fail with
    "CSV upload should show a success message or toast after import" once
    the account had already run this test once (the test's own docstring
    already listed "IDs already existed and were rejected as duplicates"
    as a suspected cause, but nothing generated fresh ones until now).

    Only the Sender_ID column is randomized here -- Type/Country_Code/
    Entity_ID are left EXACTLY as the original confirmed-working sample
    had them (same values, same row order), since those were proven to
    make this exact upload succeed and there's no reason to risk that by
    also randomizing fields that don't need to be unique (Entity_ID in
    particular refers to this account's one existing DLT-registered
    entity -- reusing it across rows is expected, not a duplicate
    conflict). This mirrors how gen_valid_template_xlsx's `ts` suffix in
    generate_all() already keeps Template DLT IDs/names unique per run
    while leaving everything else about those rows untouched.

    Making the Sender_ID column random is *why* this file also needed to
    become worker-scoped (see sender_id_sample_csv_path()'s docstring) --
    back when its content was 100% static, two workers racing to write the
    same shared path was harmless (last writer wins, but with identical
    bytes either way); once the content differs per call, "last writer
    wins" can mean a reader observes different writers across two reads of
    what it assumed was one stable file."""
    import random, string
    from utils.parallel import worker_scoped_dir

    def _rand_sender_id():
        return "".join(random.choices(string.ascii_uppercase + string.digits, k=6))

    rows = [
        [_rand_sender_id(), "Transactional", "IN", "'170115804644479'"],
        [_rand_sender_id(), "OTP",           "IN", "'170115804644478'"],
        [_rand_sender_id(), "Promotional",   "IN", "'170115804644477'"],
    ]
    _write_csv(
        "sender_id_sample.csv", rows, SENDER_ID_SAMPLE_HEADERS,
        directory=worker_scoped_dir(DATA_DIR),
    )


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
    Uses static, hard-coded test data -- EXCEPT sender_id_sample.csv, whose
    Sender_ID column is randomized on every call and which is written to a
    worker-scoped subdirectory rather than DATA_DIR itself (see
    gen_sender_id_sample_csv()'s and sender_id_sample_csv_path()'s
    docstrings for why -- re-uploading the exact same sender IDs on every
    run broke test_upload_csv_and_verify_in_list, and once the content was
    randomized, two workers racing on one shared path could make a reader
    observe different workers' bytes across two separate reads of it), and
    the Template DLT IDs/names in the `tmpl` dict below, which were already
    randomized per call via the `ts` suffix before this change.
    Called once per test module (each SMS/RCS/WhatsApp/Email flow test
    file's own autouse `generate_test_data` fixture calls this).
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
    import random, string
    ts = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    tmpl = {
        "valid": [
            {"sender_id": "DUMMY", "entity_id": _ENTITY_ID, "template_dlt_id": f"170716158089584{ts}",
             "template_name": f"Template1_{ts}", "template_product": "transactional", "content_type": "N",
             "template_content": "Dear Candidate, your password has been reset. Your new password is {{1}} - GTS",
             "template_sample": "Dear Candidate, your password has been reset. Your new password is 9876 - GTS"},
            {"sender_id": "AM-SMS", "entity_id": _ENTITY_ID, "template_dlt_id": f"170716158089873{ts}",
             "template_name": f"Template2_{ts}", "template_product": "promotional", "content_type": "U",
             "template_content": "प्रिय उम्मीदवार, आपका पासवर्ड रीसेट कर दिया गया है। आपका नया पासवर्ड {{1}} है - GTS",
             "template_sample": ""},
            {"sender_id": "DUMMY", "entity_id": _ENTITY_ID, "template_dlt_id": f"82749817481{ts}3",
             "template_name": f"Template3_{ts}", "template_product": "transactional", "content_type": "N",
             "template_content": "Hello {name}, your OTP is {otp}", "template_sample": ""},
            {"sender_id": "AM-SMS", "entity_id": _ENTITY_ID, "template_dlt_id": f"12849821798{ts}4",
             "template_name": f"Template4_{ts}", "template_product": "promotional", "content_type": "N",
             "template_content": "Get 50% off today! Visit our store.", "template_sample": ""},
            {"sender_id": "DUMMY", "entity_id": _ENTITY_ID, "template_dlt_id": f"81234982149{ts}5",
             "template_name": f"Template5_{ts}", "template_product": "transactional", "content_type": "N",
             "template_content": "Your OTP is {otp}. Valid for 10 minutes.", "template_sample": ""},
        ],
        "no_vars": [
            {"sender_id": "AM-SMS", "entity_id": _ENTITY_ID, "template_dlt_id": f"82749817481{ts}6",
             "template_name": f"Template6_{ts}", "template_product": "promotional", "content_type": "N",
             "template_content": "Hello {name}, your OTP is {otp}", "template_sample": ""},
            {"sender_id": "DUMMY", "entity_id": _ENTITY_ID, "template_dlt_id": f"12849821798{ts}7",
             "template_name": f"Template7_{ts}", "template_product": "transactional", "content_type": "N",
             "template_content": "Get 50% off today! Visit our store.", "template_sample": ""},
            {"sender_id": "AM-SMS", "entity_id": _ENTITY_ID, "template_dlt_id": f"81234982149{ts}8",
             "template_name": f"Template8_{ts}", "template_product": "promotional", "content_type": "N",
             "template_content": "Your OTP is {otp}. Valid for 10 minutes.", "template_sample": ""},
            {"sender_id": "DUMMY", "entity_id": _ENTITY_ID, "template_dlt_id": f"82749817481{ts}9",
             "template_name": f"Template9_{ts}", "template_product": "transactional", "content_type": "N",
             "template_content": "Hello {name}, your OTP is {otp}", "template_sample": ""},
            {"sender_id": "AM-SMS", "entity_id": _ENTITY_ID, "template_dlt_id": f"12849821798{ts}10",
             "template_name": f"Template10_{ts}", "template_product": "promotional", "content_type": "N",
             "template_content": "Get 50% off today! Visit our store.", "template_sample": ""},
            {"sender_id": "DUMMY", "entity_id": _ENTITY_ID, "template_dlt_id": f"81234982149{ts}11",
             "template_name": f"Template11_{ts}", "template_product": "transactional", "content_type": "N",
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
    # sender_id_sample.csv: NOT built from the static `sid` dict above --
    # see gen_sender_id_sample_csv()'s own docstring for why its Sender_ID
    # column is randomized on every call instead.
    gen_sender_id_sample_csv()
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
