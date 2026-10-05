.. _manipulating-input-files:

Manipulating Input Files
========================

PFC File
------------------

.. list-table::
   :header-rows: 1
   :widths: 45 35 35

   * - PALSfit3 label
     - PALSpal variable
     - Type / value
   * - **Spectrum**
     -
     -
   * - Spectrum file
     - ``spectrum_path``
     - ``str``
   * - Data format
     - ``format``
     - ``str``
   * - Channels in spectrum
     - ``num_channels``
     - ``int``
   * - Area min/max ch.
     - ``area``
     - ``[area_min, area_max]``
   * - Fit min/max ch.
     - ``fit``
     - ``[fit_min, fit_max]``
   * - Time zero (channel)
     - ``timezero``
     - ``int``
   * - Time zero fixed or guessed
     - ``timezero_constraint``
     - ``"F"`` or ``"G"``
   * - Time scale (ns/ch.)
     - ``timescale``
     - ``float``
   * - **Resolution Function**
     -
     -
   * - Number of Gaussian components
     - ``res_components``
     - ``int``
   * - FWHM (ns)
     - ``res_fwhm``
     - ``[FWHM_1, FWHM_2, etc.]``
   * - Intensities (%)
     - ``res_intensity``
     - ``[int_1, int_2, etc.]``
   * - Shifts (ns)
     - ``res_shift``
     - ``[shift_1, shift_2, etc.]``
   * - **Background and Area**
     -
     -
   * - Free background
     - ``bg_constraint``
     - ``0``
   * - Background fixed to spectrum mean
     - ``bg_constraint``
     - ``1``
   * - Background fixed to input value
     - ``bg_constraint``
     - ``2``
   * - Between channel no. and channel no.
     - ``bg_channels``
     - ``[bg_min, bg_max]``
   * - Fixed background value
     - ``bg_fixed``
     - ``float``
   * - No area constraints
     - ``area_constraint``
     - ``0``
   * - Area including background fixed to measured spectrum area
     - ``area_constraint``
     - ``1``
   * - Area including background fixed to input value
     - ``area_constraint``
     - ``2``
   * - Between channel no. and channel no.
     - ``area``
     - ``[area_min, area_max]``
   * - Fixed area value
     - ``area_fixed``
     - ``float``
   * - **Lifetimes and Corrections**
     -
     -
   * - Number of lifetime components
     - ``lt_components``
     - ``int``
   * - Lifetimes (ns)
     - ``lt``
     - ``[lt_1, lt_2, etc.]``
   * - Lifetimes guessed or fixed
     - ``lt_constraint``
     - ``"FGG"``, ``"GF"``, etc.
   * - Sigma (ns)
     - ``ln_broadening``
     - ``[sigma_1, sigma_2, etc.]``
   * - Sigma guessed or fixed
     - ``ln_constraint``
     - ``"FGG"``, ``"GF"``, etc.
   * - No intensity constraints
     - ``num_int_constraint``
     - ``0``
   * - Fixed intensities
     - ``num_int_constraint``
     - ``> 0``
   * - Linear combinations
     - ``num_int_constraint``
     - ``< 0``
   * - Linear combination values
     - ``XXX``
     - ``XXX``

RFC File
------------------

.. list-table::
   :header-rows: 1
   :widths: 45 35 35

   * - PALSfit3 label
     - PALSpal variable
     - Type / value
   * - **Spectrum**
     -
     -
   * - Spectrum file
     - ``spectrum_path``
     - ``str``
   * - Data format
     - ``format``
     - ``str``
   * - Channels in spectrum
     - ``num_channels``
     - ``int``
   * - Area min/max ch.
     - ``area``
     - ``[area_min, area_max]``
   * - Fit min/max ch.
     - ``fit``
     - ``[fit_min, fit_max]``
   * - Time zero (channel)
     - ``timezero``
     - ``int``
   * - Time scale (ns/ch.)
     - ``timescale``
     - ``float``
   * - **Resolution Function**
     -
     -
   * - Number of Gaussian components
     - ``res_components``
     - ``int``
   * - FWHM (ns)
     - ``res_fwhm``
     - ``[FWHM_1, FWHM_2, etc.]``
   * - FWHM Guessed or Fixed
     - ``res_lt_constraint``
     - ``"FGG"``, ``"GF"``, etc.
   * - Intensities (%)
     - ``res_intensity``
     - ``[int_1, int_2, etc.]``
   * - Shifts (ns)
     - ``res_shift``
     - ``[shift_1, shift_2, etc.]``
   * - Shifts Guessed or Fixed
     - ``res_shift_constraint``
     - ``"FGG"``, ``"GF"``, etc.
   * - **Background and Area**
     -
     -
   * - Free background
     - ``bg_constraint``
     - ``0``
   * - Background fixed to spectrum mean
     - ``bg_constraint``
     - ``1``
   * - Background fixed to input value
     - ``bg_constraint``
     - ``2``
   * - Between channel no. and channel no.
     - ``bg_channels``
     - ``[bg_min, bg_max]``
   * - Fixed background value
     - ``bg_fixed``
     - ``float``
   * - **Lifetimes and Corrections**
     -
     -
   * - Number of lifetime components
     - ``lt_components``
     - ``int``
   * - Lifetimes (ns)
     - ``lt``
     - ``[lt_1, lt_2, etc.]``
   * - Lifetimes guessed or fixed
     - ``lt_constraint``
     - ``"FGG"``, ``"GF"``, etc.
   * - No intensity constraints
     - ``num_int_constraint``
     - ``0``
   * - Fixed intensities
     - ``num_int_constraint``
     - ``> 0``
   * - Linear combinations
     - ``num_int_constraint``
     - ``< 0``
   * - Linear combination values
     - ``XXX``
     - ``XXX``
   * - Number of source corrections
     - ``source_components``
     - ``iunt``
   * - Source correction lifetimes (ns)
     - ``source_lt``
     - ``[lt_1, lt_2, etc.]``
   * - Source correction Sigma (ns)
     - ``source_broadening``
     - ``[broadening_1, broadening_2, etc.]``
   * - Source correction intensities
     - ``source_int``
     - ``[int_1, int_2, etc.]``
   * - Total (%)
     - ``source_total``
     - ``float``