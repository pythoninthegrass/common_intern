# Software Engineering Job Application Bot
## 5 Python Projects in 5 Days - Day 5: Scripting

> A script to automatically search Glassdoor for job listings, aggregate every application URL, and apply to each job using pre-populated data. **All with one click!**
> 
> **📸YouTube Tutorial: [https://youtu.be/N_7d8vg_TQA](https://youtu.be/N_7d8vg_TQA)**

## Installation
* Install [asdf](https://asdf-vm.com/guide/getting-started.html) + [poetry](https://python-poetry.org/docs/#installation)
* Install dependencies
    ```bash
    # asdf
    asdf plugin add python
    asdf install python 3.11.3
    asdf install poetry 1.4.2

    # local .venv
    poetry config virtualenvs.in-project true

    # env
    poetry install
    poetry shell
    playwright install chromium
    ```

## Usage
### Links only
* Copy `.env.example` to `.env` and fill in the values
* Run `poetry run python get_links_pw.py`
* `exports` directory will have a `urls_<timestamp>.json` file with all the links

### To run the entire script (TODO)
1. Set a number of pages you'd like to iterate through here
2. Run `python apply.py`
3. The script will open [glassdoor.com](https://www.glassdoor.com/index.htm), at which point you should log-in
4. From there on, everything is automatic!

## TODO
* [Issues](https://github.com/pythoninthegrass/common_intern/issues)
* `selenium` -> `playwright`
  * ~~Refactor [`get_links.py`](get_links.py) with `playwright`~~
  * Refactor [`apply.py`](#to-run-the-entire-script-todo) with `playwright`
* Document fork changes
* [Makefile](Makefile)
  * Automate [Installation](#installation) section
* Docker
* CI/CD
  * ghcr

## License
### Fork
[License](LICENSE.md)

### OG
> This project is licensed under the MIT License - see the [LICENSE.md](https://github.com/harshibar/5-python-projects/blob/master/LICENSE) file for details.
