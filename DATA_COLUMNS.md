# Data Column Guide

This file explains the processed CSV files created by `build_datasets.py`.

## repo_summary.csv

Each row represents one GitHub repository found in the SpecMine dataset.

- `repo_name` - GitHub repository name in `owner/repository` format.
- `repo_language` - Main programming language reported by GitHub.
- `owner_type` - Type of repository owner, such as `User` or `Organization`.
- `repo_stars` - Number of GitHub stars the repository has.
- `repo_forks` - Number of times the repository has been forked.
- `repo_fork` - Whether the repository itself is a fork (`True` or `False`).
- `repo_created_at` - Date and time the GitHub repository was created.
- `first_sdd_at` - Earliest detected commit date for an SDD specification in the repository.
- `num_specs` - Number of unique SDD specification files detected in the repository.
- `num_sdd_tools` - Number of different SDD tool categories detected in the repository.
- `sdd_tools` - List of SDD tool categories detected in the repository.
- `num_logged_in_spec_contributors` - Number of unique GitHub accounts that committed to detected specification files.
- `adoption_age_raw_days` - Raw difference in days between repository creation and the first detected SDD commit. This can be negative when commit history predates the GitHub repository creation date.
- `adoption_age_status` - Indicates whether the repository's adoption age can be used for age analysis.
  - `valid` - The adoption age is usable.
  - `predates_repo_creation` - The first detected SDD commit predates the GitHub repository creation timestamp.
  - `missing_date` - One of the required dates is missing.
- `adoption_age_valid` - `True` when `adoption_age_status` is `valid`, otherwise `False`.
- `adoption_age_days` - Clean number of days between repository creation and SDD adoption. Invalid values are left blank.
- `adoption_age_years` - Clean adoption age converted from days to years.
- `adoption_year` - Calendar year of the first detected SDD specification.

### Age Analysis Rule

When analyzing how old repositories were when they adopted SDD, only use rows where:

`adoption_age_status == "valid"`

Repositories with other statuses should still be kept for analyses that do not depend on adoption age, such as language, ownership type, stars, forks, SDD tools, and number of specifications.

---

## repo_tool_adoption.csv

Each row represents one repository + SDD tool combination.

A repository can appear more than once in this file if multiple SDD tool categories were detected.

- `repo_name` - GitHub repository name.
- `spec_tool` - SDD tool or tool category detected.
- `repo_language` - Main programming language reported by GitHub.
- `owner_type` - Type of repository owner.
- `repo_stars` - Number of GitHub stars.
- `repo_forks` - Number of times the repository has been forked.
- `repo_fork` - Whether the repository itself is a fork.
- `repo_created_at` - Date and time the repository was created.
- `first_tool_adoption_at` - Earliest detected commit date for that specific SDD tool in the repository.
- `num_specs_for_tool` - Number of detected specification files associated with that tool.
- `tool_adoption_age_status` - Indicates whether the calculated tool adoption age can be used.
  - `valid`
  - `predates_repo_creation`
  - `missing_date`
- `tool_adoption_age_valid` - `True` when the tool adoption age is valid.
- `tool_adoption_age_days` - Clean number of days between repository creation and first detected use of that tool.
- `tool_adoption_age_years` - Tool adoption age converted to years.
- `adoption_year` - Calendar year when the tool first appears in the repository.

### Tool Age Analysis Rule

When analyzing when individual SDD tools were adopted, only use rows where:

`tool_adoption_age_status == "valid"`

For analyses such as tool popularity, programming language, repository ownership, stars, forks, or specification counts, the other rows can still be used.