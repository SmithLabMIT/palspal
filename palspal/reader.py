import re
from pathlib import Path

class RFCOutFile:
    """Provides an OOP approach to the parameters within an .out file from a ResolutionFit (.rfc) run in PALSfit3
    A file can be read in with RFCOutFile.read()
    The attributes are:
        excursions
        job_time
        comment
        in_file
        dataset
        time_scale
        area_range
        fit_range
        init_fwhm
        init_intensity
        init_shifts
        converged
        iterations
        chi_square
        dof
        reduced_chi_square
        reduced_chi_square_std
        res_fwhm
        res_fwhm_std
        res_intensity
        res_intensity_std
        res_shift
        res_shift_std
        lt_lifetime
        lt_lifetime_std
        lt_intensity
        lt_intensity_std
        background
        background_std
        time_zero
        time_zero_std
        total_area_fit
        total_area_table
    """
    def __init__(self, path=None):
        self.path = Path(path) if path else None
        self._raw_lines = []

        # global fit stats
        self.converged = None
        self.iterations = None
        self.chi_square = None
        self.dof = None
        self.reduced_chi_square = None
        self.reduced_chi_square_std = None

        # Resolution final
        self.res_fwhm = None
        self.res_fwhm_std = None
        self.res_intensity = None
        self.res_intensity_std = None
        self.res_shift = None
        self.res_shift_std = None

        # Lifetime final
        self.lt_lifetime = None
        self.lt_lifetime_std = None
        self.lt_intensity = None
        self.lt_intensity_std = None

        # Background + time-zero
        self.background = None
        self.background_std = None
        self.time_zero = None
        self.time_zero_std = None

        # Total area
        self.total_area_fit = None
        self.total_area_table = None

    @classmethod
    def read(cls, file_in):
        obj = cls(file_in)
        file_in = Path(file_in)

        with open(file_in, "r") as f:
            obj._raw_lines = f.readlines()

        obj.parse_settings()
        return obj

    # -------- helpers --------
    _float_re = re.compile(r"[-+]?\d*\.?\d+(?:[Ee][-+]?\d+)?")

    @classmethod
    def _floats_in_line(cls, s):
        return [float(x) for x in cls._float_re.findall(s)]

    @classmethod
    def _stddevs_in_line_allow_fixed(cls, s):
        """
        Returns list containing floats and None for 'FIXED'.
        Assumes tokens after ':' are either 'FIXED' or numbers.
        """
        if ":" in s:
            s = s.split(":", 1)[1]
        toks = s.strip().split()
        out = []
        for t in toks:
            if t.upper().startswith("FIXED"):
                out.append(None)
            else:
                m = cls._float_re.fullmatch(t)
                if m:
                    out.append(float(t))
        return out

    # -------- parser --------
    def parse_settings(self):
        lines = self._raw_lines

        in_final = False
        in_res = False
        in_lt = False
        in_bg = False
        in_t0 = False

        for raw in lines:
            line = raw.rstrip("\n")

            # Enter final results section
            if "F I N A L  R E S U L T S" in line:
                in_final = True
                continue

            if not in_final:
                # still can parse some global lines if desired, but easiest is parse after FINAL
                continue

            # ---- global stats ----
            if "CONVERGENCE" in line and "ITERATIONS" in line:
                # Extract iteration count
                vals = self._floats_in_line(line)
                if vals:
                    self.iterations = int(vals[0])
                # Determine convergence status
                if "NOT OBTAINED" in line:
                    self.converged = False
                elif "OBTAINED" in line:
                    self.converged = True
                continue


            if "CHI-SQUARE" in line and "DEGREES OF FREEDOM" in line:
                vals = self._floats_in_line(line)
                if len(vals) >= 2:
                    self.chi_square = float(vals[0])
                    self.dof = int(vals[1])
                continue

            if "REDUCED CHI-SQUARE" in line:
                vals = self._floats_in_line(line)
                if len(vals) >= 2:
                    self.reduced_chi_square = float(vals[0])
                    self.reduced_chi_square_std = float(vals[1])
                continue

            # ---- section toggles ----
            if line.strip().startswith("RESOLUTION FUNCTION:"):
                in_res, in_lt, in_bg, in_t0 = True, False, False, False
                continue

            if line.strip().startswith("LIFETIME COMPONENTS:"):
                in_res, in_lt, in_bg, in_t0 = False, True, False, False
                continue

            if line.strip().startswith("BACKGROUND:"):
                in_res, in_lt, in_bg, in_t0 = False, False, True, False
                continue

            if line.strip().startswith("TIME-ZERO"):
                in_res, in_lt, in_bg, in_t0 = False, False, False, True
                # Note: the time-zero value is on the same line after ':'
                vals = self._floats_in_line(line)
                if vals:
                    self.time_zero = float(vals[0])
                continue

            # ---- parse inside RESOLUTION ----
            if in_res:
                if "FWHM (NS)" in line and ":" in line:
                    self.res_fwhm = self._floats_in_line(line)
                    continue
                if "INTENSITIES (%)" in line and ":" in line:
                    self.res_intensity = self._floats_in_line(line)
                    continue
                if "SHIFTS (NS)" in line and ":" in line:
                    self.res_shift = self._floats_in_line(line)
                    continue
                if "STD DEVIATIONS" in line and ":" in line:
                    # Which std dev line is it? Use what was last set but simplest:
                    # If res_fwhm exists and res_fwhm_std not yet set -> assign there, else if shift std not yet set -> assign there.
                    stds = self._stddevs_in_line_allow_fixed(line)
                    if self.res_fwhm is not None and self.res_fwhm_std is None:
                        self.res_fwhm_std = stds
                    elif self.res_shift is not None and self.res_shift_std is None:
                        self.res_shift_std = stds
                    continue

            # ---- parse inside LIFETIME ----
            if in_lt:
                if "LIFETIMES (NS)" in line and ":" in line:
                    self.lt_lifetime = self._floats_in_line(line)
                    continue
                if "INTENSITIES (%)" in line and ":" in line:
                    self.lt_intensity = self._floats_in_line(line)
                    continue
                if "STD DEVIATIONS" in line and ":" in line:
                    stds = self._stddevs_in_line_allow_fixed(line)
                    if self.lt_lifetime is not None and self.lt_lifetime_std is None:
                        self.lt_lifetime_std = stds
                    elif self.lt_intensity is not None and self.lt_intensity_std is None:
                        # intensity std devs are always numeric in your snippet
                        self.lt_intensity_std = [x for x in stds if x is not None]  # type: ignore
                    continue

            # ---- parse BACKGROUND ----
            if in_bg:
                if "COUNTS/CHANNEL" in line and ":" in line:
                    vals = self._floats_in_line(line)
                    if vals:
                        self.background = float(vals[0])
                    continue
                if "STD DEVIATION" in line and ":" in line:
                    vals = self._floats_in_line(line)
                    if vals:
                        self.background_std = float(vals[0])
                    continue

            # ---- parse TIME-ZERO std dev ----
            if in_t0:
                if "STD DEVIATIONS" in line and ":" in line:
                    vals = self._floats_in_line(line)
                    if vals:
                        self.time_zero_std = float(vals[0])
                    continue

            # ---- total area ----
            if line.strip().startswith("TOTAL AREA"):
                # "TOTAL AREA   FROM FIT         : 8.82842E+06     FROM TABLE : 7.20363E+06"
                vals = self._floats_in_line(line)
                if len(vals) >= 2:
                    self.total_area_fit = float(vals[0])
                    self.total_area_table = float(vals[1])
                continue


class PFCOutFile:
    def __init__(self, path=None):
        self.path = Path(path) if path else None
        self._raw_lines = []

        self.time_scale_ns_per_channel = None
        self.area_range_start_ch = None
        self.area_range_end_ch = None
        self.fit_range_start_ch = None
        self.fit_range_end_ch = None
        self.res_fwhm = None
        self.res_intensity = None
        self.res_shift = None

        # Before source correction
        self.no_corr_converged = None
        self.no_corr_iterations = None
        self.no_corr_chi_square = None
        self.no_corr_dof = None
        self.no_corr_reduced_chi_square = None
        self.no_corr_reduced_chi_square_std = None

        self.no_corr_lifetime = None
        self.no_corr_lifetime_std = None
        self.no_corr_intensity = None
        self.no_corr_intensity_std = None

        self.no_corr_background = None
        self.no_corr_background_std = None
        self.no_corr_time_zero = None
        self.no_corr_time_zero_std = None

        self.no_corr_total_area_fit = None
        self.no_corr_total_area_table = None

        # Source Correction
        self.source_lifetime = None
        self.source_intensity = None
        self.source_total = None

        # After source correction / Final results
        self.converged = None
        self.iterations = None
        self.chi_square = None
        self.dof = None
        self.reduced_chi_square = None
        self.reduced_chi_square_std = None
        self.lifetime = None
        self.lifetime_std = None
        self.sigma = None
        self.sigma_std = None
        self.intensity = None
        self.intensity_std = None
        self.mean_lifetime = None
        self.mean_lifetime_std = None
        self.background = None
        self.background_std = None
        self.time_zero = None
        self.time_zero_std = None
        self.total_area_fit = None
        self.total_area_table = None

    @classmethod
    def read(cls, file_in):
        obj = cls(file_in)
        file_in = Path(file_in)

        with open(file_in, "r") as f:
            obj._raw_lines = f.readlines()

        obj.parse_settings()
        return obj
    
    # -------- helpers --------
    _float_re = re.compile(r"[-+]?\d*\.?\d+(?:[Ee][-+]?\d+)?")

    @classmethod
    def _floats_in_line(cls, s):
        return [float(x) for x in cls._float_re.findall(s)]

    @classmethod
    def _stddevs_in_line_allow_fixed(cls, s):
        """
        Returns list containing floats and None for 'FIXED'.
        Assumes tokens after ':' are either 'FIXED' or numbers.
        """
        if ":" in s:
            s = s.split(":", 1)[1]
        toks = s.strip().split()
        out = []
        for t in toks:
            if t.upper().startswith("FIXED"):
                out.append(None)
            else:
                m = cls._float_re.fullmatch(t)
                if m:
                    out.append(float(t))
        return out
    
    # -------- parser --------
    def parse_settings(self):
        lines = self._raw_lines

        # ---- state flags ----
        in_initial = False
        in_no_corr_results = False
        in_source_corr = False
        in_final = False

        # ---- small helper ----
        def has(s, key):  # safe contains
            return key in s

        for raw in lines:
            line = raw.rstrip("\n")

            # -------------------------
            # Global / section switches
            # -------------------------
            if "----------------- I N I T I A L   P A R A M E T E R S ------------------" in line:
                in_initial = True
                in_no_corr_results = False
                in_source_corr = False
                in_final = False
                continue

            if "----- R E S U L T S  B E F O R E  S O U R C E  C O R R E C T I O N -----" in line:
                in_initial = False
                in_no_corr_results = True
                in_source_corr = False
                in_final = False
                continue

            if "------------------- S O U R C E  C O R R E C T I O N -------------------" in line:
                in_initial = False
                in_no_corr_results = False
                in_source_corr = True
                in_final = False
                continue

            # explicit "no source correction" banner (means: there is no before-corr results block)
            if "N O  S O U R C E  C O R R E C T I O N" in line:
                in_initial = False
                in_no_corr_results = False
                in_source_corr = False
                # final still coming; keep in_final False until we hit FINAL RESULTS banner
                continue

            if "####################### F I N A L  R E S U L T S #######################" in line:
                in_initial = False
                in_no_corr_results = False
                in_source_corr = False
                in_final = True
                continue

            # When we hit the end banner, stop parsing final
            if "######################### P O S I T R O N F I T ########################" in line:
                in_final = False
                continue

            # -------------------------
            # Parse "header-ish" values
            # -------------------------
            if has(line, "TIME SCALE") and ":" in line:
                vals = self._floats_in_line(line)
                if vals:
                    self.time_scale_ns_per_channel = float(vals[0])
                continue

            if has(line, "AREA RANGE") and "STARTS IN CH" in line and "ENDS IN CH" in line:
                vals = self._floats_in_line(line)
                if len(vals) >= 2:
                    self.area_range_start_ch = int(vals[0])
                    self.area_range_end_ch = int(vals[1])
                continue

            if has(line, "FIT RANGE") and "STARTS IN CH" in line and "ENDS IN CH" in line:
                vals = self._floats_in_line(line)
                if len(vals) >= 2:
                    self.fit_range_start_ch = int(vals[0])
                    self.fit_range_end_ch = int(vals[1])
                continue

            if has(line, "RESOLUTION") and has(line, "FWHM (NS)") and ":" in line:
                vals = self._floats_in_line(line)
                if vals:
                    self.res_fwhm = [float(x) for x in vals]  # can be 1 or 2 values
                continue

            if has(line, "FUNCTION") and has(line, "INTENSITIES") and ":" in line:
                vals = self._floats_in_line(line)
                if vals:
                    self.res_intensity = [float(x) for x in vals]
                continue

            if has(line, "SHIFTS (NS)") and ":" in line:
                vals = self._floats_in_line(line)
                if vals:
                    self.res_shift = [float(x) for x in vals]
                continue

            # -------------------------
            # Initial parameters block
            # -------------------------
            if in_initial:
                if line.strip().startswith("TIME-ZERO"):
                    vals = self._floats_in_line(line)
                    if vals:
                        self.init_time_zero = float(vals[0])
                    continue

                if line.strip().startswith("LIFETIMES (NS)"):
                    vals = self._floats_in_line(line)
                    if vals:
                        self.init_lifetime = [float(x) for x in vals]
                    continue

                if line.strip().startswith("SIGMA (NS)"):
                    vals = self._floats_in_line(line)
                    if vals:
                        self.init_sigma = [float(x) for x in vals]
                    continue

            # -----------------------------------------
            # Results BEFORE source correction (optional)
            # -----------------------------------------
            if in_no_corr_results:
                if "CONVERGENCE" in line and "ITERATIONS" in line:
                    vals = self._floats_in_line(line)
                    if vals:
                        self.no_corr_iterations = int(vals[0])
                    if "NOT OBTAINED" in line:
                        self.no_corr_converged = False
                    elif "OBTAINED" in line:
                        self.no_corr_converged = True
                    continue

                if "CHI-SQUARE" in line and "DEGREES OF FREEDOM" in line:
                    vals = self._floats_in_line(line)
                    if len(vals) >= 2:
                        self.no_corr_chi_square = float(vals[0])
                        self.no_corr_dof = int(vals[1])
                    continue

                # (some files may include reduced chi-square before-corr; your first example doesn't)
                if "REDUCED CHI-SQUARE" in line:
                    vals = self._floats_in_line(line)
                    if len(vals) >= 2:
                        self.no_corr_reduced_chi_square = float(vals[0])
                        self.no_corr_reduced_chi_square_std = float(vals[1])
                    continue

                if "LIFETIMES (NS)" in line and ":" in line:
                    vals = self._floats_in_line(line)
                    if vals:
                        self.no_corr_lifetime = [float(x) for x in vals]
                    continue

                if "SIGMA (NS)" in line and ":" in line:
                    vals = self._floats_in_line(line)
                    if vals:
                        self.no_corr_sigma = [float(x) for x in vals]
                    continue

                if "INTENSITIES (%)" in line and ":" in line:
                    vals = self._floats_in_line(line)
                    if vals:
                        self.no_corr_intensity = [float(x) for x in vals]
                    continue

                if line.strip().startswith("BACKGROUND"):
                    vals = self._floats_in_line(line)
                    if vals:
                        self.no_corr_background = float(vals[0])
                    continue

                if line.strip().startswith("TIME-ZERO"):
                    vals = self._floats_in_line(line)
                    if vals:
                        self.no_corr_time_zero = float(vals[0])
                    continue

                if line.strip().startswith("TOTAL AREA"):
                    # grabs both FROM FIT and FROM TABLE
                    vals = self._floats_in_line(line)
                    if len(vals) >= 2:
                        self.no_corr_total_area_fit = float(vals[0])
                        self.no_corr_total_area_table = float(vals[1])
                    continue

            # -------------------------
            # Source correction (optional)
            # -------------------------
            if in_source_corr:
                if "LIFETIMES (NS)" in line and ":" in line:
                    vals = self._floats_in_line(line)
                    if vals:
                        self.source_lifetime = [float(x) for x in vals]
                    continue

                if "INTENSITIES (%)" in line and ":" in line:
                    vals = self._floats_in_line(line)
                    if vals:
                        self.source_intensity = [float(x) for x in vals]
                    continue

                if "TOTAL (%)" in line and ":" in line:
                    vals = self._floats_in_line(line)
                    if vals:
                        self.source_total = float(vals[0])
                    continue

            # -------------------------
            # Final results (always)
            # -------------------------
            if in_final:
                if "CONVERGENCE" in line and "ITERATIONS" in line:
                    vals = self._floats_in_line(line)
                    if vals:
                        self.iterations = int(vals[0])
                    if "NOT OBTAINED" in line:
                        self.converged = False
                    elif "OBTAINED" in line:
                        self.converged = True
                    continue

                if "CHI-SQUARE" in line and "DEGREES OF FREEDOM" in line:
                    vals = self._floats_in_line(line)
                    if len(vals) >= 2:
                        self.chi_square = float(vals[0])
                        self.dof = int(vals[1])
                    continue

                if "REDUCED CHI-SQUARE" in line:
                    vals = self._floats_in_line(line)
                    if len(vals) >= 2:
                        self.reduced_chi_square = float(vals[0])
                        self.reduced_chi_square_std = float(vals[1])
                    continue

                # lifetimes and lifetime stddevs
                if "LIFETIMES (NS)" in line and ":" in line:
                    vals = self._floats_in_line(line)
                    if vals:
                        self.lifetime = [float(x) for x in vals]
                    continue

                if line.strip().startswith("STD DEVIATIONS") and (self.lifetime is not None) and (self.lifetime_std is None):
                    # first "STD DEVIATIONS" after lifetimes can include FIXED
                    vals = self._stddevs_in_line_allow_fixed(line)
                    if vals:
                        self.lifetime_std = vals
                    continue

                # sigma and sigma stddevs (can be *****)
                if "SIGMA (NS)" in line and ":" in line:
                    # if sigma line contains stars, floats_in_line may be empty; treat as None
                    vals = self._floats_in_line(line)
                    self.sigma = [float(x) for x in vals] if vals else None
                    continue

                if line.strip().startswith("STD DEVIATIONS") and ("sigma" in self.__dict__) and (self.sigma_std is None):
                    vals = self._stddevs_in_line_allow_fixed(line)
                    self.sigma_std = vals if vals else None
                    continue

                # intensities and intensity stddevs
                if "INTENSITIES (%)" in line and ":" in line:
                    vals = self._floats_in_line(line)
                    if vals:
                        self.intensity = [float(x) for x in vals]
                    continue

                if line.strip().startswith("STD DEVIATIONS") and (self.intensity is not None) and (self.intensity_std is None):
                    vals = self._stddevs_in_line_allow_fixed(line)
                    if vals:
                        self.intensity_std = vals
                    continue

                # mean lifetime + std
                if "MEAN LIFETIME" in line and ":" in line:
                    vals = self._floats_in_line(line)
                    if vals:
                        self.mean_lifetime = float(vals[0])
                    continue

                if line.strip().startswith("STD DEVIATION") and ("mean_lifetime" in self.__dict__) and (self.mean_lifetime_std is None):
                    vals = self._floats_in_line(line)
                    if vals:
                        self.mean_lifetime_std = float(vals[0])
                    continue

                # background + std
                if line.strip().startswith("BACKGROUND"):
                    vals = self._floats_in_line(line)
                    if vals:
                        self.background = float(vals[0])
                    continue

                if line.strip().startswith("STD DEVIATIONS") and (self.background is not None) and (self.background_std is None):
                    vals = self._floats_in_line(line)
                    if vals:
                        self.background_std = float(vals[0])
                    continue

                # time-zero + std
                if line.strip().startswith("TIME-ZERO"):
                    vals = self._floats_in_line(line)
                    if vals:
                        self.time_zero = float(vals[0])
                    continue

                if line.strip().startswith("STD DEVIATIONS") and (self.time_zero is not None) and (self.time_zero_std is None):
                    vals = self._floats_in_line(line)
                    if vals:
                        self.time_zero_std = float(vals[0])
                    continue

                # total area
                if line.strip().startswith("TOTAL AREA"):
                    vals = self._floats_in_line(line)
                    if len(vals) >= 2:
                        self.total_area_fit = float(vals[0])
                        self.total_area_table = float(vals[1])
                    continue
