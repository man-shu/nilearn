"""Benchmarks for masker objects under nilearn.maskers module."""

# ruff: noqa: RUF012

from ..common import Benchmark
from ..utils import apply_mask, load


class NiftiMaskerBenchmark(Benchmark):
    """
    Benchmark for applying a mask to an image using NiftiMasker with different
    parameters.
    """

    # try different combinations of parameters for the NiftiMasker object
    param_names = ["smoothing_fwhm", "standardize", "detrend"]
    params = (
        [None, 6],
        [False, "zscore_sample", "zscore", "psc"],
        [False, True],
    )

    def time_nifti_masker(
        self,
        smoothing_fwhm,
        standardize,
        detrend,
    ):
        """Time the loading (only with nilearn here) and then masking with
        different parameters.
        """
        mask, img = load("nilearn")
        apply_mask(
            mask,
            img,
            "nilearn",
            nifti_masker_params={
                "smoothing_fwhm": smoothing_fwhm,
                "standardize": standardize,
                "detrend": detrend,
            },
        )

    def peakmem_nifti_masker(
        self,
        smoothing_fwhm,
        standardize,
        detrend,
    ):
        """Peak memory for the loading (only with nilearn here) and then
        masking with different parameters.
        """
        mask, img = load("nilearn")
        apply_mask(
            mask,
            img,
            "nilearn",
            nifti_masker_params={
                "smoothing_fwhm": smoothing_fwhm,
                "standardize": standardize,
                "detrend": detrend,
            },
        )
