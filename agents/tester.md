# Tester
Write tests in `tests/`. Run them. Report pass/fail + bugs with repro steps.
- Python (native host): pytest — JSON→MD for all 4 content types, file writing, 4-byte length prefix protocol, error cases (bad JSON, bad paths, permissions)
- JS (extension): manual test scripts + HTML fixtures mimicking Teams DOM for each content type
- E2E: feed sample JSON to native host stdin, assert correct .md output (content, path, naming)
