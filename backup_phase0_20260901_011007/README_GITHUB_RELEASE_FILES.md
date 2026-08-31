# GitHub release files

This archive contains two files for the SPEECHTIME repository:

```text
LICENSE
.github/workflows/tests.yml
```

## Apply

Extract this archive directly into the `SPEECHTIME-main` project root. Windows
will create the `.github/workflows/` folder structure automatically.

## MIT License

The MIT License is permissive: users may use, copy, modify, distribute, and
sell derivatives, provided that the copyright and license notices remain in
substantial copies of the software. The software is supplied without warranty.

The copyright holder is currently set to:

```text
Copyright (c) 2026 walidddhony-rgb
```

Change this line before publishing if you prefer your full legal name.

## GitHub Actions

The workflow runs on pushes and pull requests to `main`, plus manual runs from
the Actions tab. It uses Python 3.10 and 3.11, installs `requirements.txt`,
compiles key application files, then runs pytest.
