"""palsfit.writer"""
import platform
import re
import subprocess
from pathlib import Path

class RFCFile:
    """Represents a .rfc file with editable settings.
    """

    RESOLUTION_HEADER_1 = "RESOLUTIONFIT DATA BLOCK 1: OUTPUT OPTIONS"
    RESOLUTION_HEADER_2 = "RESOLUTIONFIT DATA BLOCK 2: SPECTRUM"
    RESOLUTION_HEADER_3 = "RESOLUTIONFIT DATA BLOCK 3: CHANNEL RANGES. TIME SCALE. TIME-ZERO."
    RESOLUTION_HEADER_4 = "RESOLUTIONFIT DATA BLOCK 4: RESOLUTION FUNCTION"
    RESOLUTION_HEADER_5 = "RESOLUTIONFIT DATA BLOCK 5: LIFETIMES AND INTENSITY CONSTRAINTS"
    RESOLUTION_HEADER_6 = "RESOLUTIONFIT DATA BLOCK 6: BACKGROUND CONSTRAINTS"

    def __init__(self, path=None):
        self.path = Path(path) if path else None
        self._raw_lines = []

        # Block 1 data (Output options)
        # Represented as an block of 0 (False) and 1 (True) (e.g., 0101)
        # Default: 0000
        self.echo = 0
        self.iteration = 0
        self.resid_plot = 0
        self.corr_matrix = 0

        # There is also a hidden log-normal fineness that can be applied if desired
        # Default: 32 (e.g., 0000 32 is the same as 0000 which is the same as 0000 0)
        self.log_normal_fineness = None  # If None, it will not be printed and default to 32
        
        # Block 2 data (Spectrum)
        self.num_channels = None  # Number of channels in the spectrum
        self.format = None  # Formatting of spectrum expressed in FORMAT style of FORTRAN
        self.spectrum_path = None  # File path of the spectrum
        self.spectrum_label = None  # Spectrum label (header row in the spectrum)
        self.inspec = 0  # Whether the spectrum is an intrinsic part of the spectrum (1) or not (0)

        # Block 3 data (CHANNEL RANGES. TIME SCALE. TIME-ZERO)
        self.area = None  # Integer array corresponding to the min and max area channels [area_min, area_max]
        self.fit = None  # Integer array corresponding to the min and max fit channels [fit_min, fit_max]
        self.timescale = None  # ns/ch
        self.timezero = None  # in channel number

        # Block 4 data (RESOLUTION FUNCTION)
        self.res_components = None  # Number of lifetime components in the resolution func.
        self.res_lt_constraint = None  # Whether components are guessed or fixed (e.g., "GFF")
        self.res_fwhm = None  # Array of FWHM (ns)
        self.res_intensity = None  # Intensity of lifetimes (%)
        self.res_shift_constraint = None  # Whether shifts are guessed or fixed (e.g., "GFF")
        self.res_shift = None  # Array of shifts (peak displacements) (ns)

        # Block 5 data (LIFETIMES AND INTENSITY CONSTRAINTS)
        self.lt_components = None  # Number of lifetime components in the material
        self.lt_constraint = None  # Whether components are guessed or fixed (e.g., "GFF")
        self.lt = None  # Lifetimes (ns)
        self.int_constraint = None # If m=0, relative intensities fixed, if m>0, TODO
        self.int_constraint_info = None  # TODO

        # Block 6 data (BACKGROUND CONSTRAINTS)
        self.bg_constraint = None  # 0=No constraint, 1=fit area between channels in self.bg_channels, 2=fit area specified in self.bg_fixed
        self.bg_channels = None
        self.bg_fixed = None


    @classmethod
    def read(cls, file_in):
        obj = cls(file_in)
        file_in = Path(file_in)

        with open(file_in, "r") as f:
            obj._raw_lines = f.readlines()

        obj.parse_settings()
        return obj

    @staticmethod
    def strip_comment(line):
        # Remove anything after a '#'
        return line.split("#", 1)[0].strip()

    @staticmethod
    def tokenize(lines):
        """Turn a list of raw lines into tokens, removing comments and blanks.
        Keeps ordering.
        """
        toks = []
        for raw in lines:
            s = RFCFile.strip_comment(raw)
            if not s:
                continue
            toks.extend(s.split())
        return toks

    def parse_settings(self):
        """Find and parse the resolution block.
        """

        # find header line index
        header_idx_1 = None
        header_idx_2 = None
        header_idx_3 = None
        header_idx_4 = None
        header_idx_5 = None
        header_idx_6 = None

        for i, raw in enumerate(self._raw_lines):
            if self.RESOLUTION_HEADER_1 in raw:
                header_idx_1 = i
            elif self.RESOLUTION_HEADER_2 in raw:
                header_idx_2 = i
            elif self.RESOLUTION_HEADER_3 in raw:
                header_idx_3 = i
            elif self.RESOLUTION_HEADER_4 in raw:
                header_idx_4 = i
            elif self.RESOLUTION_HEADER_5 in raw:
                header_idx_5 = i
            elif self.RESOLUTION_HEADER_6 in raw:
                header_idx_6 = i

        #==========================BLOCK 1============================
        toks = self.tokenize(self._raw_lines[header_idx_1 + 1:header_idx_2])

        self.echo = int(toks[0][0])
        self.iteration = int(toks[0][1])
        self.resid_plot = int(toks[0][2])
        self.corr_matrix = int(toks[0][3])

        extra = toks[0][4:].strip()
        self.log_normal_fineness = int(extra) if extra else None
    
        #==========================BLOCK 2============================
        lines = self._raw_lines[header_idx_2 + 1 : header_idx_3]

        clean_lines = []
        for raw in lines:
            s = self.strip_comment(raw)
            if s:
                clean_lines.append(s)

        self.num_channels = clean_lines[0].strip()
        self.format = clean_lines[1].strip()
        self.spectrum_path = clean_lines[2].strip()
        self.spectrum_label = clean_lines[3].strip()
        self.inspec = clean_lines[4].strip()

        #==========================BLOCK 3============================
        toks = self.tokenize(self._raw_lines[header_idx_3 + 1:header_idx_4])
        
        self.area = [toks[0], toks[1]]
        self.fit = [toks[2], toks[3]]
        self.timescale = toks[4]
        self.timezero = toks[5]

        #==========================BLOCK 4============================
        toks = self.tokenize(self._raw_lines[header_idx_4 + 1:header_idx_5])

        self.res_components = int(float(toks[0]))
        self.res_lt_constraint = toks[1]
        
        self.res_fwhm = []
        pos = 2
        for k in range(self.res_components):
            self.res_fwhm.append(float(toks[pos + k]))
        pos += self.res_components

        self.res_intensity = []
        for k in range(self.res_components):
            self.res_intensity.append(float(toks[pos + k]))
        pos += self.res_components

        self.res_shift_constraint = toks[pos]
        pos += 1

        self.res_shift = []
        for k in range(self.res_components):
            self.res_shift.append(float(toks[pos + k]))

        #==========================BLOCK 5============================
        # Tokenize everything AFTER the header line
        toks = self.tokenize(self._raw_lines[header_idx_5 + 1:header_idx_6])

        self.lt_components = int(float(toks[0]))
        self.lt_constraint = toks[1]
        
        pos = 2
        self.lt = []
        for k in range(self.lt_components):
            self.lt.append(float(toks[pos + k]))
        pos += self.lt_components
        self.int_constraint = toks[pos + k]
        self.int_constraint_info = None # TODO

        #==========================BLOCK 6============================
        toks = self.tokenize(self._raw_lines[header_idx_6 + 1 :])

        self.bg_constraint = toks[0]

        if int(float(self.bg_constraint)) == 1:
            self.bg_channels = [toks[1], toks[2]]
        elif int(float(self.bg_constraint)) == 2:
            self.bg_fixed = toks[1]


        # checking
        #if self.lt_components <= 0:
        #    raise RuntimeError(f"Lifetime components must be positive; got {n}")

    def write(self, file_out=None):
        """Write updated RFC data.

        If no file was loaded, write a blank/default RFC file.
        """

        file_out = Path(file_out) if file_out else self.path
        if file_out is None:
            raise ValueError("No output file specified and self.path is None.")

        self.path = Path(file_out)

        def as_int(x, default=0):
            if x is None:
                return default
            return int(float(x))

        def as_float(x, default=0.0):
            if x is None:
                return default
            return float(x)

        def as_str(x, default=""):
            if x is None:
                return default
            return str(x)

        def as_list(x, default=None):
            if x is None:
                return list(default or [])
            return list(x)

        new_lines = []

        if self._raw_lines:
            start_idx_1 = None
            for i, line in enumerate(self._raw_lines):
                if self.RESOLUTION_HEADER_1 in line:
                    start_idx_1 = i
                    break

            if start_idx_1 is not None:
                new_lines.extend(self._raw_lines[:start_idx_1])

        # Defaults
        echo = as_int(self.echo, 0)
        iteration = as_int(self.iteration, 0)
        resid_plot = as_int(self.resid_plot, 0)
        corr_matrix = as_int(self.corr_matrix, 0)

        num_channels = as_int(self.num_channels, 0)
        fmt = as_str(self.format, "(Spectrum format [Fortran specs])")
        spectrum_path = as_str(self.spectrum_path, "spectrum_name.dat")
        spectrum_label = as_str(self.spectrum_label, "Spectrum label")
        inspec = as_int(self.inspec, 0)

        area = as_list(self.area, [0, 0])
        fit = as_list(self.fit, [0, 0])
        timescale = as_float(self.timescale, 0.0)
        timezero = as_float(self.timezero, 0.0)

        res_components = as_int(self.res_components, 1)
        res_lt_constraint = as_str(self.res_lt_constraint, "X" * res_components)
        res_fwhm = as_list(self.res_fwhm, [0.0] * res_components)
        res_intensity = as_list(self.res_intensity, [100.0] + [0.0] * (res_components - 1))
        res_shift_constraint = as_str(self.res_shift_constraint, "X" * res_components)
        res_shift = as_list(self.res_shift, [0.0] * res_components)

        lt_components = as_int(self.lt_components, 1)
        lt_constraint = as_str(self.lt_constraint, "X" * lt_components)
        lt = as_list(self.lt, [0.0] * lt_components)
        int_constraint = as_int(self.int_constraint, 0)

        bg_constraint = as_int(self.bg_constraint, 0)

        # Normalize list lengths
        res_fwhm = (res_fwhm + [0.0] * res_components)[:res_components]
        res_intensity = (res_intensity + [0.0] * res_components)[:res_components]
        res_shift = (res_shift + [0.0] * res_components)[:res_components]
        lt = (lt + [0.0] * lt_components)[:lt_components]

        # ========================== BLOCK 1 ============================
        new_lines.append(f"{self.RESOLUTION_HEADER_1}\n")

        flags = f"{echo}{iteration}{resid_plot}{corr_matrix}"

        if self.log_normal_fineness is not None:
            new_lines.append(f"{flags} {as_int(self.log_normal_fineness, 32)}\n")
        else:
            new_lines.append(f"{flags}\n")

        # ========================== BLOCK 2 ============================
        new_lines.append(f"{self.RESOLUTION_HEADER_2}\n")
        new_lines.append(f"{num_channels:>10d}\n")
        new_lines.append(f"{fmt}\n")
        new_lines.append(f"{spectrum_path}\n")
        new_lines.append(f"{spectrum_label}\n")
        new_lines.append(f"{inspec:>2d}\n")

        if inspec == 1:
            new_lines.append(f"{spectrum_label}\n")

        # ========================== BLOCK 3 ============================
        new_lines.append(f"{self.RESOLUTION_HEADER_3}\n")
        new_lines.append(f"{as_int(area[0], 0):>10d}\n")
        new_lines.append(f"{as_int(area[1], 0):>10d}\n")
        new_lines.append(f"{as_int(fit[0], 0):>10d}\n")
        new_lines.append(f"{as_int(fit[1], 0):>10d}\n")
        new_lines.append(f"{timescale:>10f}\n")
        new_lines.append(f"{timezero:>10.3f}\n")

        # ========================== BLOCK 4 ============================
        new_lines.append(f"{self.RESOLUTION_HEADER_4}\n")
        new_lines.append(f"{res_components:>10d}\n")
        new_lines.append(f"{res_lt_constraint}\n")
        new_lines.append(" ".join(f"{as_float(x):>10.5f}" for x in res_fwhm) + "\n")
        new_lines.append(" ".join(f"{as_float(x):>10.3f}" for x in res_intensity) + "\n")
        new_lines.append(f"{res_shift_constraint}\n")
        new_lines.append(" ".join(f"{as_float(x):>10.5f}" for x in res_shift) + "\n")

        # ========================== BLOCK 5 ============================
        new_lines.append(f"{self.RESOLUTION_HEADER_5}\n")
        new_lines.append(f"{lt_components:>10d}\n")
        new_lines.append(f"{lt_constraint}\n")
        new_lines.append(" ".join(f"{as_float(x):>10.5f}" for x in lt) + "\n")
        new_lines.append(f"{int_constraint:>10d}\n")

        if self.int_constraint_info is not None:
            if isinstance(self.int_constraint_info, (list, tuple)):
                new_lines.append(" ".join(str(x) for x in self.int_constraint_info) + "\n")
            else:
                new_lines.append(f"{self.int_constraint_info}\n")

        # ========================== BLOCK 6 ============================
        new_lines.append(f"{self.RESOLUTION_HEADER_6}\n")
        new_lines.append(f"{bg_constraint:>10d}\n")

        if bg_constraint == 1:
            bg_channels = as_list(self.bg_channels, [0, 0])
            new_lines.append(f"{as_int(bg_channels[0], 0):>10d}\n")
            new_lines.append(f"{as_int(bg_channels[1], 0):>10d}\n")

        elif bg_constraint == 2:
            new_lines.append(f"{as_float(self.bg_fixed, 0.0):>10.5f}\n")

        with open(file_out, "w") as f:
            f.writelines(new_lines)

        self._raw_lines = new_lines


    def run(self, exe_path, out_file=None, timeout=None):

        if self.path is None:
            raise ValueError("RFCFile.path is None.")

        # If running on Linux (e.g. WSL), convert a Windows-style path to Linux if needed
        path_str = str(exe_path)
        if platform.system() != "Windows" and re.match(r'^[a-zA-Z]:\\', path_str):
            drive = path_str[0].lower()             # 'c'
            rest  = path_str[2:].replace('\\', '/') # '/Program Files/PATFIT19/res19.exe'
            exe_path = Path(f"/mnt/{drive}{rest}")
        else:
            exe_path = Path(exe_path)
        rfc_path = Path(self.path)

        if not exe_path.exists():
            raise FileNotFoundError(f"Executable not found: {exe_path}")

        if not rfc_path.exists():
            raise FileNotFoundError(f"RFC not found: {rfc_path}")

        # Default output name in SAME directory as RFC
        if out_file is None:
            out_file = rfc_path.with_suffix(".out")

        out_file = Path(out_file)

        proc = subprocess.Popen([str(exe_path)], cwd=str(rfc_path.parent), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,)

        # Only send filenames (not full paths)
        stdin_text = f"{rfc_path.name}\n{out_file.name}\n"

        stdout, stderr = proc.communicate(stdin_text, timeout=timeout)

        if proc.returncode != 0:
            raise RuntimeError(f"res19 failed (code {proc.returncode})\nSTDOUT:\n{stdout}\nSTDERR:\n{stderr}")

        produced = rfc_path.parent / out_file.name

        if not produced.exists():
            raise RuntimeError(f"Output file not created: {produced}")

        return produced


class PFCFile:
    """Represents a .pfc file with editable settings
    """

    POSITRON_HEADER_1 = "POSITRONFIT DATA BLOCK 1: OUTPUT OPTIONS"
    POSITRON_HEADER_2 = "POSITRONFIT DATA BLOCK 2: SPECTRUM"
    POSITRON_HEADER_3 = "POSITRONFIT DATA BLOCK 3: CHANNEL RANGES. TIME SCALE. TIME-ZERO."
    POSITRON_HEADER_4 = "POSITRONFIT DATA BLOCK 4: RESOLUTION FUNCTION"
    POSITRON_HEADER_5 = "POSITRONFIT DATA BLOCK 5: LIFETIMES AND INTENSITY CONSTRAINTS"
    POSITRON_HEADER_6 = "POSITRONFIT DATA BLOCK 6: BACKGROUND CONSTRAINTS"
    POSITRON_HEADER_7 = "POSITRONFIT DATA BLOCK 7: AREA CONSTRAINTS"
    POSITRON_HEADER_8 = "POSITRONFIT DATA BLOCK 8: SOURCE CORRECTION"

    def __init__(self, path=None):
        self.path = Path(path) if path else None
        self._raw_lines = []

        # Block 1 data (Output options)
        # Represented as an block of 0 (False) and 1 (True) (e.g., 0101)
        # Default: 0000
        self.echo = None
        self.iteration = None
        self.resid_plot = None
        self.corr_matrix = None

        # There is also a hidden log-normal fineness that can be applied if desired
        # Default: 32 (e.g., 0000 32 is the same as 0000 which is the same as 0000 0)
        self.log_normal_fineness = None

        # Block 2 data (Spectrum)
        self.num_channels = None  # Number of channels in the spectrum
        self.format = None  # Formatting of spectrum expressed in FORMAT style of FORTRAN
        self.spectrum_path = None  # File path of the spectrum
        self.spectrum_label = None  # Spectrum label (header row in the spectrum)
        self.inspec = None  # Whether the spectrum is an intrinsic part of the spectrum (1) or not (0)

        # Block 3 data (CHANNEL RANGES. TIME SCALE. TIME-ZERO)
        self.area = None  # Integer array corresponding to the min and max area channels [area_min, area_max]
        self.fit = None  # Integer array corresponding to the min and max fit channels [fit_min, fit_max]
        self.timescale = None  # ns/ch
        self.timezero_constraint = None
        self.timezero = None  # in channel number

        # Block 4 data (RESOLUTION FUNCTION)
        self.res_components = None # Number of lifetime components in the resolution func.
        self.res_fwhm = None # Array of FWHM (ns)
        self.res_intensity = None # Intensity of lifetimes (%)
        self.res_shift = None # Array of shifts (peak displacements) (ns)

        # Block 5 data (LIFETIMES AND INTENSITY CONSTRAINTS)
        self.lt_components = None  # Number of lifetime components in the material
        self.lt_constraint = None  # Whether components are guessed or fixed (e.g., "GFF")
        self.lt = None  # Lifetimes (ns)
        self.ln_constraint = None  # Whether log-normal components are guessed or fixed (e.g., "GFF")
        self.ln_broadening = None  # (ns)
        self.num_int_constraint = None # m=0, relative intensities free; m>0 relative intensities fixed; m<0 relative intensities linear combo
        self.int_constraint = None  # nested arrays of either [[fixed_int_index] [fixed_ints]] or [[lin_combo_1]...[lin_combo_j]]
        self.lt_components_2 = None  # Number of lifetime components in the material
        self.lt_constraint_2 = None  # Whether components are guessed or fixed (e.g., "GFF")
        self.lt_2 = None  # Lifetimes (ns)
        self.ln_constraint_2 = None  # Whether log-normal components are guessed or fixed (e.g., "GFF")
        self.ln_broadening_2 = None  # (ns)
        self.int_constraint_2 = None # If m=0, relative intensities fixed, if m>0, TODO
        self.int_constraint_info_2 = None  # TODO

        # Block 6 data (BACKGROUND CONSTRAINTS)
        self.bg_constraint = None  # 0=No constraint, 1=fit area between channels in self.bg_channels, 2=fit background specified in self.bg_fixed
        self.bg_channels = None
        self.bg_fixed = None

        # Block 7 data (AREA CONSTRAINTS)
        self.area_constraint = None # 0=No constraint, 1=fit area between channels in self.area_channels, 2=fit area specified in self.area_fixed
        self.area_channels = None
        self.area_fixed = None

        # Block 8 data (SOURCE CORRECTION)
        self.source_components = None  # Number of source correction components
        self.source_lt = None  # Lifetimes (ns)
        self.source_broadening = None  # (ns)
        self.source_int = None  # Relative intensities of the source correction components (%)
        self.source_total = None  # Percentage of positrons that annihilate in the source (%)
        self.new_cycle_input = None  # Whether to start source correction convergence from values obtained from no source correction convergence (0) or use new specified params. (1) and whether to also change t0 (2)
        self.source_components_2 = None  # Number of source correction components
        self.source_lt_2 = None  # Lifetimes (ns)
        self.source_broadening_2 = None  # (ns)
        self.source_int_2 = None  # Relative intensities of the source correction components (%)
        self.source_total_2 = None  # Percentage of positrons that annihilate in the source (%)
        self.timezero_constraint_2 = None
        self.timezero_2 = None

    @classmethod
    def read(cls, file_in):
        obj = cls(file_in)
        file_in = Path(file_in)

        with open(file_in, "r") as f:
            obj._raw_lines = f.readlines()

        obj.parse_settings()
        return obj

    @staticmethod
    def strip_comment(line):
        # Remove anything after a '#'
        return line.split("#", 1)[0].strip()

    @staticmethod
    def tokenize(lines):
        """Turn a list of raw lines into tokens, removing comments and blanks.
        Keeps ordering.
        """
        toks = []
        for raw in lines:
            s = PFCFile.strip_comment(raw)
            if not s:
                continue
            toks.extend(s.split())
        return toks

    def parse_settings(self):
        """Find and parse the resolution block.
        """

        header_idx_1 = None
        header_idx_2 = None
        header_idx_3 = None
        header_idx_4 = None
        header_idx_5 = None
        header_idx_6 = None
        header_idx_7 = None
        header_idx_8 = None
        for i, raw in enumerate(self._raw_lines):
            if self.POSITRON_HEADER_1 in raw:
                header_idx_1 = i
            elif self.POSITRON_HEADER_2 in raw:
                header_idx_2 = i
            elif self.POSITRON_HEADER_3 in raw:
                header_idx_3 = i
            elif self.POSITRON_HEADER_4 in raw:
                header_idx_4 = i
            elif self.POSITRON_HEADER_5 in raw:
                header_idx_5 = i
            elif self.POSITRON_HEADER_6 in raw:
                header_idx_6 = i
            elif self.POSITRON_HEADER_7 in raw:
                header_idx_7 = i
            elif self.POSITRON_HEADER_8 in raw:
                header_idx_8 = i

        #==========================BLOCK 1============================
        toks = self.tokenize(self._raw_lines[header_idx_1 + 1:header_idx_2])

        self.echo = int(toks[0][0])
        self.iteration = int(toks[0][1])
        self.resid_plot = int(toks[0][2])
        self.corr_matrix = int(toks[0][3])

        extra = toks[0][4:].strip()
        self.log_normal_fineness = int(extra) if extra else None

        #==========================BLOCK 2============================
        lines = self._raw_lines[header_idx_2 + 1:header_idx_3]

        clean_lines = []
        for raw in lines:
            s = self.strip_comment(raw)
            if s:
                clean_lines.append(s)

        self.num_channels = clean_lines[0].strip()
        self.format = clean_lines[1].strip()
        self.spectrum_path = clean_lines[2].strip()
        self.spectrum_label = clean_lines[3].strip()
        self.inspec = clean_lines[4].strip()

        #==========================BLOCK 3============================
        toks = self.tokenize(self._raw_lines[header_idx_3 + 1:header_idx_4])
        
        self.area = [toks[0], toks[1]]
        self.fit = [toks[2], toks[3]]
        self.timescale = toks[4]
        self.timezero_constraint = toks[5]
        self.timezero = toks[6]

        #==========================BLOCK 4============================
        # Tokenize everything AFTER the header line
        toks = self.tokenize(self._raw_lines[header_idx_4 + 1 :header_idx_5])

        self.res_components = int(float(toks[0]))

        pos = 1
        self.res_fwhm = []
        for k in range(self.res_components):
            self.res_fwhm.append(float(toks[pos + k]))
        pos += self.res_components

        self.res_intensity = []
        for k in range(self.res_components):
            self.res_intensity.append(float(toks[pos + k]))
        pos += self.res_components

        self.res_shift = []
        for k in range(self.res_components):
            self.res_shift.append(float(toks[pos + k]))

        #==========================BLOCK 5============================
        toks = self.tokenize(self._raw_lines[header_idx_5 + 1 :header_idx_6])

        self.lt_components = int(float(toks[0]))
        self.lt_constraint = toks[1]
        
        pos = 2
        self.lt = []
        for k in range(self.lt_components):
            self.lt.append(float(toks[pos + k]))
        pos += self.lt_components

        self.ln_constraint = toks[pos]

        pos += 1
        self.ln_broadening = []
        for k in range(self.lt_components):
            self.ln_broadening.append(float(toks[pos + k]))

        pos += self.lt_components
        if pos < header_idx_6:
            self.num_int_constraint = int(toks[pos])

            pos += 1
            self.int_constraint = []
            if self.num_int_constraint > 0:
                int_index = []
                for k in range(self.num_int_constraint):
                    int_index.append(int(toks[pos + k]))
                self.int_constraint.append(int_index)

                pos += self.num_int_constraint
                int_val = []
                for k in range(self.num_int_constraint):
                    int_val.append(float(toks[pos + k]))
                self.int_constraint.append(int_val)

            elif self.num_int_constraint < 0:
                for _ in range(abs(self.num_int_constraint)):
                    lin_combo = []
                    for k in range(self.lt_components):
                        lin_combo(float(toks[pos + k]))
                    pos += self.lt_components
                    self.int_constraint.append(lin_combo)

            # TODO: figure out potential second iter needed

        #==========================BLOCK 6============================
        toks = self.tokenize(self._raw_lines[header_idx_6 + 1 :header_idx_7])

        self.bg_constraint = toks[0]

        if int(float(self.bg_constraint)) == 1:
            self.bg_channels = [toks[1], toks[2]]
        elif int(float(self.bg_constraint)) == 2:
            self.bg_fixed = toks[1]

        #==========================BLOCK 7============================
        toks = self.tokenize(self._raw_lines[header_idx_7 + 1 :header_idx_8])

        self.area_constraint = toks[0]

        if self.area_constraint == 1:
            self.area_channels = [toks[1], toks[2]]
        elif self.area_constraint == 2:
            self.area_fixed = toks[1]

        #==========================BLOCK 8============================
        toks = self.tokenize(self._raw_lines[header_idx_8 + 1 :])

        self.source_components = int(float(toks[0]))

        pos = 1
        if self.source_components > 0:
            self.source_lt = []
            for k in range(self.source_components):
                self.source_lt.append(float(toks[pos + k]))
            pos += self.source_components

            self.source_broadening = []
            for k in range(self.source_components):
                self.source_broadening.append(float(toks[pos + k]))
            pos += self.source_components

            self.source_int = []
            for k in range(self.source_components):
                self.source_int.append(float(toks[pos + k]))
            pos += self.source_components

            self.source_total = float(toks[pos])
            pos += 1

            self.new_cycle_input = int(float(toks[pos]))
            pos += 1

            if self.new_cycle_input in [1, 2]:
                self.source_components_2 = int(float(toks[pos]))
                pos += 1
                self.source_lt_2 = []
                for k in range(self.source_components_2):
                    self.source_lt_2.append(float(toks[pos + k]))
                pos += self.source_components_2

                self.source_broadening_2 = []
                for k in range(self.source_components_2):
                    self.source_broadening_2.append(float(toks[pos + k]))
                pos += self.source_components_2

                self.source_int_2 = []
                for k in range(self.source_components_2):
                    self.source_int_2.append(float(toks[pos + k]))
                pos += self.source_components_2

                self.source_total_2 = float(toks[pos])
                pos += 1

                if self.new_cycle_input == 2:
                    self.timezero_constraint_2 = toks[pos]
                    self.timezero_2 = toks[pos+1]

    def write(self, file_out=None):
        """Write updated PFC data.

        If a file was loaded, preserve anything before block 1.
        If no file was loaded, write a blank/default PFC file.
        """

        file_out = Path(file_out) if file_out else self.path
        if file_out is None:
            raise ValueError("No output file specified and self.path is None.")

        self.path = Path(file_out)

        def as_int(x, default=0):
            if x is None:
                return default
            return int(float(x))

        def as_float(x, default=0.0):
            if x is None:
                return default
            return float(x)

        def as_str(x, default=""):
            if x is None:
                return default
            return str(x)

        def as_list(x, default=None):
            if x is None:
                return list(default or [])
            return list(x)

        new_lines = []

        if self._raw_lines:
            start_idx_1 = None
            for i, line in enumerate(self._raw_lines):
                if self.POSITRON_HEADER_1 in line:
                    start_idx_1 = i
                    break

            if start_idx_1 is not None:
                new_lines.extend(self._raw_lines[:start_idx_1])

        # Defaults
        echo = as_int(self.echo, 0)
        iteration = as_int(self.iteration, 0)
        resid_plot = as_int(self.resid_plot, 0)
        corr_matrix = as_int(self.corr_matrix, 0)

        num_channels = as_int(self.num_channels, 0)
        fmt = as_str(self.format, "(Spectrum format [Fortran specs])")
        spectrum_path = as_str(self.spectrum_path, "spectrum_name.dat")
        spectrum_label = as_str(self.spectrum_label, "Spectrum label")
        inspec = as_int(self.inspec, 0)

        area = as_list(self.area, [None, None])
        fit = as_list(self.fit, [None, None])
        timescale = as_float(self.timescale, 0.0)
        timezero_constraint = as_str(self.timezero_constraint, "X")
        timezero = as_float(self.timezero, 0.0)

        res_components = as_int(self.res_components, 1)
        res_fwhm = as_list(self.res_fwhm, [None] * res_components)
        res_intensity = as_list(
            self.res_intensity,
            [100.0] + [0.0] * (res_components - 1)
        )
        res_shift = as_list(self.res_shift, [0.0] * res_components)

        lt_components = as_int(self.lt_components, 1)
        lt_constraint = as_str(self.lt_constraint, "X" * lt_components)
        lt = as_list(self.lt, [0.0] * lt_components)
        ln_constraint = as_str(self.ln_constraint, "X" * lt_components)
        ln_broadening = as_list(self.ln_broadening, [0.0] * lt_components)
        num_int_constraint = as_int(self.num_int_constraint, 0)

        bg_constraint = as_int(self.bg_constraint, 0)
        area_constraint = as_int(self.area_constraint, 0)

        source_components = as_int(self.source_components, 0)
        source_lt = as_list(self.source_lt, [0.0] * source_components)
        source_broadening = as_list(self.source_broadening, [0.0] * source_components)
        source_int = as_list(self.source_int, [100.0] + [0.0] * max(source_components - 1, 0))
        source_total = as_float(self.source_total, 0.0)
        new_cycle_input = as_int(self.new_cycle_input, 0)

        # Normalize lengths
        res_fwhm = (res_fwhm + [0.0] * res_components)[:res_components]
        res_intensity = (res_intensity + [0.0] * res_components)[:res_components]
        res_shift = (res_shift + [0.0] * res_components)[:res_components]

        lt = (lt + [0.0] * lt_components)[:lt_components]
        ln_broadening = (ln_broadening + [0.0] * lt_components)[:lt_components]

        source_lt = (source_lt + [0.0] * source_components)[:source_components]
        source_broadening = (
            source_broadening + [0.0] * source_components
        )[:source_components]
        source_int = (source_int + [0.0] * source_components)[:source_components]

        # ========================== BLOCK 1 ============================
        new_lines.append(f"{self.POSITRON_HEADER_1}\n")

        flags = f"{echo}{iteration}{resid_plot}{corr_matrix}"

        if self.log_normal_fineness is not None:
            new_lines.append(f"{flags} {as_int(self.log_normal_fineness, 32)}\n")
        else:
            new_lines.append(f"{flags}\n")

        # ========================== BLOCK 2 ============================
        new_lines.append(f"{self.POSITRON_HEADER_2}\n")
        new_lines.append(f"{num_channels:>10d}\n")
        new_lines.append(f"{fmt}\n")
        new_lines.append(f"{spectrum_path}\n")
        new_lines.append(f"{spectrum_label}\n")
        new_lines.append(f"{inspec:>2d}\n")

        if inspec == 1:
            new_lines.append(f"{spectrum_label}\n")

        # ========================== BLOCK 3 ============================
        new_lines.append(f"{self.POSITRON_HEADER_3}\n")
        new_lines.append(f"{as_int(area[0], 0):>10d}\n")
        new_lines.append(f"{as_int(area[1], 0):>10d}\n")
        new_lines.append(f"{as_int(fit[0], 0):>10d}\n")
        new_lines.append(f"{as_int(fit[1], 0):>10d}\n")
        new_lines.append(f"{timescale:>10f}\n")
        new_lines.append(f"{timezero_constraint}\n")
        new_lines.append(f"{timezero:>10.3f}\n")

        # ========================== BLOCK 4 ============================
        new_lines.append(f"{self.POSITRON_HEADER_4}\n")
        new_lines.append(f"{res_components:>10d}\n")
        new_lines.append("".join(f"{as_float(x):>10.5f}" for x in res_fwhm) + "\n")
        new_lines.append("".join(f"{as_float(x):>10.3f}" for x in res_intensity) + "\n")
        new_lines.append("".join(f"{as_float(x):>10.5f}" for x in res_shift) + "\n")

        # ========================== BLOCK 5 ============================
        new_lines.append(f"{self.POSITRON_HEADER_5}\n")
        new_lines.append(f"{lt_components:>10d}\n")
        new_lines.append(f"{lt_constraint}\n")
        new_lines.append("".join(f"{as_float(x):>10.4f}" for x in lt) + "\n")
        new_lines.append(f"{ln_constraint}\n")
        new_lines.append("".join(f"{as_float(x):>10.4f}" for x in ln_broadening) + "\n")

        new_lines.append(f"{as_int(num_int_constraint):>10d}\n")
        if self.num_int_constraint > 0:
            new_lines.append(" ".join(f"{as_int(x):>10d}" for x in self.int_constraint[0]) + "\n")
            new_lines.append(" ".join(f"{as_float(x):>10.4f}" for x in self.int_constraint[1]) + "\n")
        elif self.num_int_constraint < 0:
            for j in range(self.num_int_constraint):
                new_lines.append(" ".join(f"{as_float(x):>10.4f}" for x in self.int_constraint[j]) + "\n")
            
        if self.lt_components_2 is not None:
            lt_components_2 = as_int(self.lt_components_2, 1)
            lt_constraint_2 = as_str(self.lt_constraint_2, "F" * lt_components_2)
            lt_2 = as_list(self.lt_2, [0.0] * lt_components_2)
            ln_constraint_2 = as_str(self.ln_constraint_2, "F" * lt_components_2)
            ln_broadening_2 = as_list(
                self.ln_broadening_2,
                [0.0] * lt_components_2
            )

            lt_2 = (lt_2 + [0.0] * lt_components_2)[:lt_components_2]
            ln_broadening_2 = (
                ln_broadening_2 + [0.0] * lt_components_2
            )[:lt_components_2]

            new_lines.append(f"{lt_components_2:>10d}\n")
            new_lines.append(f"{lt_constraint_2}\n")
            new_lines.append(" ".join(f"{as_float(x):>10.5f}" for x in lt_2) + "\n")
            new_lines.append(f"{ln_constraint_2}\n")
            new_lines.append(" ".join(f"{as_float(x):>10.5f}" for x in ln_broadening_2) + "\n")

            if self.int_constraint_2 is not None:
                new_lines.append(f"{as_int(self.int_constraint_2):>10d}\n")

                if self.int_constraint_info_2 is not None:
                    if isinstance(self.int_constraint_info_2, (list, tuple)):
                        new_lines.append(
                            " ".join(str(x) for x in self.int_constraint_info_2) + "\n"
                        )
                    else:
                        new_lines.append(f"{self.int_constraint_info_2}\n")

        # ========================== BLOCK 6 ============================
        new_lines.append(f"{self.POSITRON_HEADER_6}\n")
        new_lines.append(f"{bg_constraint:>10d}\n")

        if bg_constraint == 1:
            bg_channels = as_list(self.bg_channels, [0, 0])
            new_lines.append(f"{as_int(bg_channels[0], 0):>10d}\n")
            new_lines.append(f"{as_int(bg_channels[1], 0):>10d}\n")

        elif bg_constraint == 2:
            new_lines.append(f"{as_float(self.bg_fixed, 0.0):>11.5f}\n")

        # ========================== BLOCK 7 ============================
        new_lines.append(f"{self.POSITRON_HEADER_7}\n")
        new_lines.append(f"{area_constraint:>10d}\n")

        if area_constraint == 1:
            area_channels = as_list(self.area_channels, [0, 0])
            new_lines.append(f"{as_int(area_channels[0], 0):>10d}\n")
            new_lines.append(f"{as_int(area_channels[1], 0):>10d}\n")

        elif area_constraint == 2:
            new_lines.append(f"{as_float(self.area_fixed, 0.0):>10.5f}\n")

        # ========================== BLOCK 8 ============================
        new_lines.append(f"{self.POSITRON_HEADER_8}\n")
        new_lines.append(f"{source_components:>10d}\n")

        if source_components > 0:
            new_lines.append(" ".join(f"{as_float(x):>10.5f}" for x in source_lt) + "\n")
            new_lines.append(
                " ".join(f"{as_float(x):>10.5f}" for x in source_broadening) + "\n"
            )
            new_lines.append(" ".join(f"{as_float(x):>10.5f}" for x in source_int) + "\n")

            new_lines.append(f"{source_total:>10.5f}\n")
            new_lines.append(f"{new_cycle_input:>10d}\n")

            if new_cycle_input in [1, 2]:
                source_components_2 = as_int(self.source_components_2, 0)
                source_lt_2 = as_list(self.source_lt_2, [0.0] * source_components_2)
                source_broadening_2 = as_list(
                    self.source_broadening_2,
                    [0.0] * source_components_2
                )
                source_int_2 = as_list(
                    self.source_int_2,
                    [100.0] + [0.0] * max(source_components_2 - 1, 0)
                )

                source_lt_2 = (
                    source_lt_2 + [0.0] * source_components_2
                )[:source_components_2]
                source_broadening_2 = (
                    source_broadening_2 + [0.0] * source_components_2
                )[:source_components_2]
                source_int_2 = (
                    source_int_2 + [0.0] * source_components_2
                )[:source_components_2]

                new_lines.append(f"{source_components_2:>10d}\n")

                if source_components_2 > 0:
                    new_lines.append(
                        " ".join(f"{as_float(x):>10.5f}" for x in source_lt_2) + "\n"
                    )
                    new_lines.append(
                        " ".join(f"{as_float(x):>10.5f}" for x in source_broadening_2) + "\n"
                    )
                    new_lines.append(
                        " ".join(f"{as_float(x):>10.5f}" for x in source_int_2) + "\n"
                    )

                new_lines.append(f"{as_float(self.source_total_2, 0.0):>10.5f}\n")

                if new_cycle_input == 2:
                    new_lines.append(f"{as_str(self.timezero_constraint_2, 'F')}\n")
                    new_lines.append(f"{as_float(self.timezero_2, 0.0):>10.3f}\n")

        with open(file_out, "w") as f:
            f.writelines(new_lines)

        self._raw_lines = new_lines

    def run(self, exe_path, out_file=None, timeout=None):

        if self.path is None:
            raise ValueError("PFCFile.path is None.")

        # If running on Linux (e.g. WSL), convert a Windows-style path to Linux if needed
        path_str = str(exe_path)
        if platform.system() != "Windows" and re.match(r'^[a-zA-Z]:\\', path_str):
            drive = path_str[0].lower()             # 'c'
            rest  = path_str[2:].replace('\\', '/') # '/Program Files/PATFIT19/res19.exe'
            exe_path = Path(f"/mnt/{drive}{rest}")
        else:
            exe_path = Path(exe_path)
        pfc_path = Path(self.path)

        if not exe_path.exists():
            raise FileNotFoundError(f"Executable not found: {exe_path}")

        if not pfc_path.exists():
            raise FileNotFoundError(f"PFC not found: {exe_path}")

        # Default output name in SAME directory as PFC
        if out_file is None:
            out_file = pfc_path.with_suffix(".out")

        out_file = Path(out_file)

        proc = subprocess.Popen([str(exe_path)], cwd=str(pfc_path.parent), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,)

        # Only send filenames (not full paths)
        stdin_text = f"{pfc_path.name}\n{out_file.name}\n"

        stdout, stderr = proc.communicate(stdin_text, timeout=timeout)

        if proc.returncode != 0:
            raise RuntimeError(f"res19 failed (code {proc.returncode})\nSTDOUT:\n{stdout}\nSTDERR:\n{stderr}")

        produced = pfc_path.parent / out_file.name

        if not produced.exists():
            raise RuntimeError(f"Output file not created: {produced}")

        return produced