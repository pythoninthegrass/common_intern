### Playwright

* Install from the [Setup](../README.md#setup) section
* Usage
  * `pip` 
    ```bash
    # install
    pip install --upgrade pip
    pip install playwright
    playwright install

    # download new browsers (chromedriver, gecko)
    npx playwright install

  * `pipx`
    ```bash
    # install
    pipx install playwright  # install/upgrade
    cd ~/.local/pipx/venvs/playwright
    
    # inject dependencies manually
    source bin/activate
    playwright install
    deactivate
    ```
  * Both
    ```bash
    # generate code via macro
    playwright codegen \
        -b cr \                             # default: chromium (cr, ff, wk)
        --target python-async \             # default: python (python, python-async)
        --viewport-size "1280, 1400" \
        https://www.glassdoor.com/index.htm
    ```
* If `asdf` gives you lip
  ```bash
  # No preset version installed for command playwright
  asdf reshim python
  ```
