import numpy as np
import pytest

from nilearn._utils.estimator_checks import check_estimator
from nilearn.maskers import SurfaceMasker
from nilearn.surface import SurfaceImage
from nilearn.surface.utils import (
    assert_polydata_equal,
    assert_surface_image_equal,
)


@pytest.mark.parametrize(
    "estimator, check, name",
    check_estimator(estimator=[SurfaceMasker()]),
)
def test_check_estimator(estimator, check, name):  # noqa: ARG001
    """Check compliance with sklearn estimators."""
    check(estimator)


@pytest.mark.xfail(reason="invalid checks should fail")
@pytest.mark.parametrize(
    "estimator, check, name",
    check_estimator(estimator=[SurfaceMasker()], valid=False),
)
def test_check_estimator_invalid(estimator, check, name):  # noqa: ARG001
    """Check compliance with sklearn estimators."""
    check(estimator)


def test_fit_list_surf_images(surf_img_2d):
    """Test fit on list of surface images.

    resulting mask should have a single 'timepoint'.
    """
    masker = SurfaceMasker()
    masker.fit([surf_img_2d(3), surf_img_2d(5)])
    assert masker.mask_img_.shape == (surf_img_2d(1).shape[0],)


def test_fit_list_surf_images_with_mask(surf_mask_1d, surf_img_2d):
    """Test fit on list of surface images when masker has a mask."""
    masker = SurfaceMasker(mask_img=surf_mask_1d)
    masker.fit([surf_img_2d(3), surf_img_2d(5)])
    assert masker.mask_img_.shape == (surf_img_2d(1).shape[0],)


@pytest.mark.parametrize("surf_mask_dim", [1, 2])
def test_transform_list_surf_images(
    surf_mask_dim,
    surf_mask_1d,
    surf_mask_2d,
    surf_img_1d,
    surf_img_2d,
):
    """Test transform on list of surface images."""
    surf_mask = surf_mask_1d if surf_mask_dim == 1 else surf_mask_2d()
    masker = SurfaceMasker(surf_mask).fit()
    signals = masker.transform([surf_img_1d, surf_img_1d, surf_img_1d])
    assert signals.shape == (3, masker.n_elements_)
    signals = masker.transform([surf_img_2d(5), surf_img_2d(4)])
    assert signals.shape == (9, masker.n_elements_)


@pytest.mark.parametrize("surf_mask_dim", [1, 2])
def test_inverse_transform_list_surf_images(
    surf_mask_dim, surf_mask_1d, surf_mask_2d, surf_img_2d
):
    """Test inverse_transform on list of surface images."""
    surf_mask = surf_mask_1d if surf_mask_dim == 1 else surf_mask_2d()
    masker = SurfaceMasker(surf_mask).fit()
    signals = masker.transform([surf_img_2d(3), surf_img_2d(4)])
    img = masker.inverse_transform(signals)
    assert img.shape == (surf_mask.mesh.n_vertices, 7)


@pytest.mark.parametrize("n_timepoints", [3])
def test_transform_inverse_transform_no_mask(surf_mesh, n_timepoints):
    """Check output of inverse transform when not using a mask."""
    # make a sample image with data on the first timepoint/sample 1-4 on
    # left part and 10-50 on right part
    img_data = {}
    for i, (key, val) in enumerate(surf_mesh.parts.items()):
        data_shape = (val.n_vertices, n_timepoints)
        data_part = (
            np.arange(np.prod(data_shape)).reshape(data_shape[::-1]) + 1.0
        ) * 10**i
        img_data[key] = data_part.T

    img = SurfaceImage(surf_mesh, img_data)
    masker = SurfaceMasker().fit(img)
    signals = masker.transform(img)

    # make sure none of the data has been removed
    assert signals.shape == (n_timepoints, img.shape[0])
    assert np.array_equal(signals[0], [1, 2, 3, 4, 10, 20, 30, 40, 50])
    unmasked_img = masker.inverse_transform(signals)
    assert_polydata_equal(img.data, unmasked_img.data)


@pytest.mark.parametrize("n_timepoints", [1, 3])
def test_transform_inverse_transform_with_mask(surf_mesh, n_timepoints):
    """Check output of inverse transform when using a mask."""
    # make a sample image with data on the first timepoint/sample 1-4 on
    # left part and 10-50 on right part-
    img_data = {}
    for i, (key, val) in enumerate(surf_mesh.parts.items()):
        data_shape = (val.n_vertices, n_timepoints)
        data_part = (
            np.arange(np.prod(data_shape)).reshape(data_shape[::-1]) + 1.0
        ) * 10**i
        img_data[key] = data_part.T
    img = SurfaceImage(surf_mesh, img_data)

    # make a mask that removes first vertex of each part
    # total 2 removed
    mask_data = {
        "left": np.asarray([False, True, True, True]),
        "right": np.asarray([False, True, True, True, True]),
    }
    mask = SurfaceImage(surf_mesh, mask_data)

    masker = SurfaceMasker(mask).fit(img)
    signals = masker.transform(img)

    # check mask shape is as expected
    assert signals.shape == (n_timepoints, masker.n_elements_)

    # check the data for first seven vertices is as expected
    assert np.array_equal(signals.ravel()[:7], [2, 3, 4, 20, 30, 40, 50])

    # check whether inverse transform does not change the img
    unmasked_img = masker.inverse_transform(signals)
    # recreate data that we expect after unmasking
    expected_data = {k: v.copy() for (k, v) in img.data.parts.items()}
    for v in expected_data.values():
        v[0] = 0.0
    expected_img = SurfaceImage(img.mesh, expected_data)
    assert_surface_image_equal(unmasked_img, expected_img)
