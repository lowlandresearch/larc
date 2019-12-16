# LARC Core Toolset

Collection of utilities for use across LARC projects.

## Installation

```
pip3 install larc
```

## How to Use

The `larc` library provides a number of utilities:

- `larc.common`: Collection of general-purpose functions and types,
  patterned after the
  [`toolz`](https://toolz.readthedocs.io/en/latest/api.html)
  functional programming library
- `larc.yaml`: A few simple wrapper functions around `ruamel.yaml`
  that provides a standard interface for reading/writing YAML files
- `larc.markdown`: Collection of
  [Python Markdown](https://python-markdown.github.io/extensions/)
  extensions
    - `MetaYamlExtension` (`meta_yaml`): A slight tweak to the
      [Meta-Data extension](https://python-markdown.github.io/extensions/meta_data/)
      for providing YAML metadata at the beginning of a markdown
      file
    - `SimpleTableExtension` (`simpletable`): A `<table>`-parsing
      extension for markdown that allows you to provide CSS classes
      for table elements within the markdown
    - `YamlDataExtension` (`yaml_data`): A more general YAML-parsing
      extension that allows you to provide chunks of YAML data
      throughout the markdown file (not just at the beginning)
- `larc.rest`: A ReST client-building tool that attempts to be more
  functional
- `larc.logging`: Some logging utility functions that relies on
  [`coloredlogs`](https://coloredlogs.readthedocs.io/en/latest/api.html)
  for log coloring
- `larc.parallel`: Some functional parallelization utility functions
  designed for use within the `toolz`-ish functional idiom
- `larc.signature`: Functions to construct a host signature, for use
  when "fingerprinting" clients is necessary
- `larc.shell`: Shell command functions

The library also provides the following command-line tools:

- `diffips`: Given two files with IPs (A and B), get difference A - B
- `intips`: Given two files with IPs (A and B), get intersection A & B
- `difflines`: Given two files with lines of text (A and B), get
  difference A - B
- `intlines`: Given two files with lines of text (A and B), get
  intersection A & B
- `sortips`: Given text content (from clipboard, file, or stdin),
  extract IPs sort them
- `getips`: Given text content (from clipboard, file, or stdin),
  extract IPs and print them
