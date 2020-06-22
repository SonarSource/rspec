# rspec


Structure
---------

`rules` directory
- `RSPEC_****` directory for each rule
  - a file per section shared between multiple languages: `main.adoc`, `compliant.adoc`, `noncompliant.adoc`, `exceptions.adoc`, `see.adoc`
  - `metadata.json`: metadatas shared between laguage. They can be overridden.
  - a directory per LANGUAGE: `java`, `c-family`, `python`...
    - `rule.adoc`: root file used to generate the rule description for the specific language. It can include parts from `*.adoc` files defined in the parent directory.
    - `metadata.json`: metadatas for the specific language. Each root key will completely override the key of the above `metadata.json` file. No "smart" merge takes place, which makes it easier to have in one glance the full value of a field.
    - `compliant.py/java/...`, `noncompliant.py/java/...`: source code files containing compliant and noncompliant code examples.

Metadata format
---------------
The metadata match closely what plugins expect.
Additional fields:
* `qualityProfile`: quality profile(s) in which the rule should be registered.