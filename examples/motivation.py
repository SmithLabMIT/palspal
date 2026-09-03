import numpy as np
from palspal import inputter

pfc = inputter.PFCFile.read("in.pfc")
for corr in np.arange(0, 20, 0.5):
    pfc.source_total = corr
    pfc.write(f"in_{corr:.1f}.pfc")
    pfc.run(exe_path="pos19.exe")
