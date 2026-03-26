# ONLY changed parts are marked

...
# inside loop

primary = None

if isinstance(primary_cell, str) and "secondary" in primary_cell.lower():
    if secondary is not None:
        primary = secondary + 10
else:
    primary = to_float(primary_cell)

if primary is None and secondary is not None:
    primary = secondary + 10

# duration FIX (minutes, keep column name)
duration = float(hold) if hold not in [None, ""] else 0

# TEST MODE FIX (per row, NOT global)
row_test_mode = test_mode
if primary == 0:
    row_test_mode = 1

rows.append({
    ...
    "Duration_s": duration,
    "Test_Mode": row_test_mode,
})
