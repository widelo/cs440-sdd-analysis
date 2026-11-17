# Data validation and analysis contract

DATA_COLUMNS.md was read in full after it was added to the checkout. The validation implements its definitions without modifying or re-cleaning either input CSV.

- Repository grain: unique repo_name. Category grain: unique (repo_name, spec_tool). Both tables cover the same repository set.
- Required columns, nonnegative integer counts, boolean encodings, UTC timestamps and adoption_year/date consistency are checked.
- Clean days/years must be present and nonnegative exactly for valid statuses, absent otherwise. Validity flags and statuses must agree with full timestamp chronology; rounded raw -0.0 cannot override status. Clean/raw days must agree with timestamps within rounding tolerance.
- Cross-table metadata, category lists/counts, specification sums, and minimum category dates agree with repository records.
- Repository-age filter: adoption_age_status == 'valid'. Category-age filter: tool_adoption_age_status == 'valid'. Non-age plots retain all statuses. Trends exclude missing first-detection dates only.
- sdd_tools is observed as a comma-separated category list. spec_tool is a category identifier, including generic and location categories. No product classification is invented.
- repo_fork is constant False; repo_forks is a numeric popularity measure. Contributors count unique GitHub accounts committing to detected specification files.
- Results use days for ages. Supplied years are checked within rounding tolerance; the dictionary does not specify the day-to-year divisor.

## Input fingerprints

- `repo_summary.csv`: `747a92f9c9d92ce01e868b303237ceb54e729ac4c7d61fb973cef635dedc39bb`
- `repo_tool_adoption.csv`: `e95ff4eeb81eea20b222a516185d89d7247f3874a44aa679c45f997e73a43114`

Machine-readable counts, missingness, date ranges and versions are in results/validation_report.json.
