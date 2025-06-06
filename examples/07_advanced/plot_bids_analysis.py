"""
BIDS dataset first and second level analysis
============================================

Full step-by-step example of fitting a :term:`GLM`
to perform a first and second level
analysis in a :term:`BIDS` dataset and visualizing the results.
Details about the :term:`BIDS` standard can be consulted at
`https://bids.neuroimaging.io/ <https://bids.neuroimaging.io/>`_.

More specifically:

1. Download an :term:`fMRI` :term:`BIDS` dataset
   with two language conditions to contrast.
2. Extract first level model objects automatically
   from the :term:`BIDS` dataset.
3. Fit a second level model on the fitted first level models.
   Notice that in this case the preprocessed :term:`bold<BOLD>`
   images were already normalized to the same :term:`MNI` space.
"""

from nilearn import plotting

# %%
# Fetch example :term:`BIDS` dataset
# ----------------------------------
# We download a simplified :term:`BIDS` dataset made available for illustrative
# purposes. It contains only the necessary
# information to run a statistical analysis using Nilearn. The raw data
# subject folders only contain bold.json and events.tsv files, while the
# derivatives folder includes the preprocessed files preproc.nii and the
# confounds.tsv files.
from nilearn.datasets import fetch_language_localizer_demo_dataset

data = fetch_language_localizer_demo_dataset(legacy_output=False)

# %%
# Here is the location of the dataset on disk.
print(data.data_dir)

# %%
# Obtain automatically FirstLevelModel objects and fit arguments
# --------------------------------------------------------------
# From the dataset directory we automatically obtain
# the FirstLevelModel objects
# with their subject_id filled from the :term:`BIDS` dataset.
# Moreover, we obtain for each model a dictionary with run_imgs,
# events and confounder regressors
# since in this case a confounds.tsv file is available
# in the :term:`BIDS` dataset.
# To get the first level models we only have to specify the dataset directory
# and the task_label as specified in the file names.
from nilearn.glm.first_level import first_level_from_bids

task_label = "languagelocalizer"
(
    models,
    models_run_imgs,
    models_events,
    models_confounds,
) = first_level_from_bids(
    data.data_dir,
    task_label,
    img_filters=[("desc", "preproc")],
    n_jobs=2,
    space_label="",
    smoothing_fwhm=8,
)

# %%
# Quick sanity check on fit arguments
# -----------------------------------
# Additional checks or information extraction from pre-processed data can
# be made here.

# %%
# We just expect one run_img per subject.
from pathlib import Path

print([Path(run).name for run in models_run_imgs[0]])

# %%
# The only confounds stored are regressors obtained from motion correction. As
# we can verify from the column headers of the confounds table corresponding
# to the only run_img present.
print(models_confounds[0][0].columns)

# %%
# During this acquisition the subject read blocks of sentences and
# consonant strings. So these are our only two conditions in events.
# We verify there are 12 blocks for each condition.
print(models_events[0][0]["trial_type"].value_counts())

# %%
# First level model estimation
# ----------------------------
# Now we simply fit each first level model and plot for each subject the
# :term:`contrast` that reveals the language network (language - string).
# Notice that we can define a :term:`contrast`
# using the names of the conditions specified in the events dataframe.
# Sum, subtraction and scalar multiplication are allowed.

# %%
# Set the threshold as the z-variate with an uncorrected p-value of 0.001.
from scipy.stats import norm

p001_unc = norm.isf(0.001)

# %%
# Prepare figure for concurrent plot of individual maps.
from math import ceil

import matplotlib.pyplot as plt
import numpy as np

ncols = 2
nrows = ceil(len(models) / ncols)

fig, axes = plt.subplots(nrows=nrows, ncols=ncols, figsize=(10, 12))
axes = np.atleast_2d(axes)
model_and_args = zip(models, models_run_imgs, models_events, models_confounds)
for midx, (model, imgs, events, confounds) in enumerate(model_and_args):
    # fit the GLM
    model.fit(imgs, events, confounds)
    # compute the contrast of interest
    zmap = model.compute_contrast("language-string")
    plotting.plot_glass_brain(
        zmap,
        threshold=p001_unc,
        title=f"sub-{model.subject_label}",
        axes=axes[int(midx / ncols), int(midx % ncols)],
        plot_abs=False,
        colorbar=True,
        display_mode="x",
        vmin=-12,
        vmax=12,
    )
fig.suptitle("subjects z_map language network (unc p<0.001)")
plotting.show()

# %%
# Second level model estimation
# -----------------------------
# We just have to provide the list of fitted FirstLevelModel objects
# to the SecondLevelModel object for estimation. We can do this because
# all subjects share a similar design matrix (same variables reflected in
# column names).
from nilearn.glm.second_level import SecondLevelModel

second_level_input = models

# %%
# Note that we apply a smoothing of 8mm.
second_level_model = SecondLevelModel(smoothing_fwhm=8.0, n_jobs=2)
second_level_model = second_level_model.fit(second_level_input)

# %%
# Computing contrasts at the second level is as simple as at the first level.
# Since we are not providing confounders we are performing a one-sample test
# at the second level with the images determined by the specified first level
# contrast.
zmap = second_level_model.compute_contrast(
    first_level_contrast="language-string"
)

# %%
# The group level :term:`contrast` reveals a left lateralized fronto-temporal
# language network.
plotting.plot_glass_brain(
    zmap,
    threshold=p001_unc,
    title="Group language network (unc p<0.001)",
    plot_abs=False,
    display_mode="x",
    figure=plt.figure(figsize=(5, 4)),
)
plotting.show()

# %%
# Generate and save the GLM report at the group level.
report_slm = second_level_model.generate_report(
    contrasts="intercept",
    first_level_contrast="language-string",
    threshold=p001_unc,
    display_mode="x",
)

# %%
# View the GLM report at the group level.
report_slm

# %%
# Or in a separate browser window
# report_slm.open_in_browser()

# %%
# Save the report to disk
output_dir = Path.cwd() / "results" / "plot_bids_analysis"
output_dir.mkdir(exist_ok=True, parents=True)
report_slm.save_as_html(output_dir / "report_slm.html")
