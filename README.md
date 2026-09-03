# palspal
Python wrapper for analyses in PALSfit3

palspal is a Python package that provides an object oriented approach to interacting with and manipulating input and output to the PALSfit3 software. 

## Features
palspal can:
- Read and write the ResolutionFit (`.rfc`) and PositronFit (`.pfc`) input files
- Read the `.out` output files
- Run the PALSfit3 analysis by calling the PATFIT19 program, available at https://palsfit.dk/Download.

## Installation
palspal can be installed using:
- conda: `conda install -c conda-forge package-not-yet-available`
- pip: `python -m pip install package-not-yet-available`

Alternatively, users can install the latest version from GitHub, either directly:

```
python -m pip install git+https://github.com/bctapia/palspal.git
```
or by downloading the source code:
```
git clone https://github.com/bctapia/palspal.git
cd palspal
python -m pip install .
```
For developers, it is recommended to download the source code and install in editable mode by replacing `python -m pip install .` with `python -m pip install -e .`.

## Example
To motivate the benefits of palspal, we provide the following example. Here, a sensitivity analysis of the effect of source correction on the outpuit lifetimes is being computed by running PALSfit3 with a source correction from 0% to 20% in 0.5% increments.

```
import numpy as np
from palspal import inputter

pfc = inputter.PFCFile.read("in.pfc")
for corr in np.arange(0, 20, 0.5):
    pfc.source_total = corr
    pfc.write(f"in_{corr:.1f}.pfc")
    pfc.run(exe_path="pos19.exe")
```

## License
Copyright © 2026 The Massachusetts Institute of Technology

This work is licensed under the MIT license (see `LICENSE`)