
# Table of Contents

1.  [Installing](#orgab6e344)
2.  [Testing](#org72a82f3)
    1.  [Unit tests](#orgabc03a5)
    2.  [Liniting](#orgc376d4e)
3.  [Running](#orgb8665d6)


<a id="orgab6e344"></a>

# Installing

This has only been tested on Linux with Python v3.8.  The
instructions assume this is what is being used.

    python3 -m venv .venv
    . ./.venv/bin/activate
    ./setup.py install


<a id="org72a82f3"></a>

# Testing


<a id="orgabc03a5"></a>

## Unit tests

    python3 -m venv .venv
    . ./.venv/bin/activate
    ./setup.py test


<a id="orgc376d4e"></a>

## Liniting

    python3 -m venv .venv
    . ./.venv/bin/activate
    ./setup.py lint   


<a id="orgb8665d6"></a>

# Running

Using command line:

    texel-detect-frozen [-o output] [URL1 [URL2 ...]]

