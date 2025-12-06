# File Checksums

Track file states to avoid repeating work on unchanged inputs.

## Watched Files

| File | Last Processed | Hash/Marker | Action Taken |
|------|----------------|-------------|--------------|
| design2/human-notes.md | 2025-12-06 | v2-reformatted | Reformatted English, fixed typos |

## How This Works

Before reformatting or processing a file:
1. Check if the file has changed since last processed
2. If unchanged, skip the work
3. If changed, process and update this table

## Format Notes
- Hash/Marker can be a simple version marker or actual hash
- This prevents re-reformatting unchanged files
