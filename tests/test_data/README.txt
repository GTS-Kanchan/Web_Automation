Place the following test data files in this folder before running upload-related tests:

  valid_sender_id.xlsx          - Valid sender IDs, correct format, ≤5MB
  valid_sender_id.csv           - Same as above in CSV format
  invalid_format.pdf            - Any PDF file (for unsupported format test)
  large_file.xlsx               - Any Excel file >5MB (for size limit test)
  duplicate_sender_ids.csv      - CSV with duplicate Sender ID values
  invalid_length_sender_ids.csv - Sender IDs with <3 or >11 characters
  special_chars_sender_ids.csv  - Sender IDs containing !@#$% etc.
  missing_entity_id_col.csv     - CSV missing the Entity ID column header
  invalid_country_code.csv      - Rows with unsupported/fake country codes
  mixed_valid_invalid.csv       - Mix of valid and invalid Sender ID rows

Tests that need these files will automatically skip with a clear message
if the file is not present, so you can run all other tests without them.
