#!/bin/env python
#
# Module name: visualizations.py
#
# Description: Functions to generate PSD topoplots from source level activity
#
# Authora: Santiago Flores <santiago_flores_alonso@sfu.ca> & Jack Solomon <jack_solomon@sfu.ca>
#
# License: BSD (3-clause)

import mne
import numpy as np
import matplotlib.pyplot as plt
import scipy

def stc_per_band(morph, power, stc, subject):
    """
    Creates a SourceEstimate object for a specific frequency band and applies morphing.

    Parameters:
        morph: mne.SourceMorph
            The morph object used to morph the SourceEstimate to a common space.
        power: ndarray
            Power values for the frequency band, corresponding to vertices.
        stc: mne.SourceEstimate
            SourceEstimate object containing the original vertex and subject information.
        subject: str
            Subject identifier in the FreeSurfer directory.

    Returns:
        stc_band_morph: mne.SourceEstimate
            Morphed SourceEstimate object for the frequency band.
    """
    # Create the SourceEstimate for the band
    stc_band = mne.SourceEstimate( data=power, vertices=stc.vertices, tmin=0, tstep=0.25, subject=subject)

    # Apply morphing to the SourceEstimate
    stc_band_morph = morph.apply(stc_band)
    return stc_band_morph

def generate_brain_screenshot(stc_band_morph, views, power, surfer_kwargs):
    """
    Generates a screenshot of the brain visualization for a given SourceEstimate.

    Parameters:
        stc_band_morph: mne.SourceEstimate
            The morphed SourceEstimate object to be visualized.
        views: list or str
            View(s) to display (e.g., 'lateral', 'medial', etc.).
        power: ndarray
            Power values to define the color limits (clim).
        surfer_kwargs: dict
            Additional keyword arguments for the brain visualization.

    Returns:
        img: ndarray
            Screenshot image of the brain visualization.
    """
    # Update visualization parameters
    surfer_kwargs['views'] = views
    surfer_kwargs['hemi'] = 'lh'
    if views == 'dorsal':
        surfer_kwargs['hemi'] = 'both'
    clim = dict(kind="value", lims=[0, max(power) / 2, max(power)]) #Colorband limits
    brain = stc_band_morph.plot(**surfer_kwargs, clim=clim)  # Plot the brain with the specified clim and additional arguments
    #img = brain.screenshot() # Capture the screenshot
    #brain.close()# Close the interactive brain object

    return brain

def brains_plot(i, band, axes, img_lateral, img_medial, img_dorsal):
    """
    Places brain images into subplots and labels the frequency band.

    Parameters:
        i: int
            Row index in the subplot grid.
        band: str
            Name of the frequency band to display as a label.
        axes: ndarray
            Array of subplot axes.
        img_lateral: ndarray
            Image array for the lateral view of the brain.
        img_medial: ndarray
            Image array for the medial view of the brain.

    Returns:
        None
    """
    # Place the images into the subplots
    axes[i, 0].imshow(img_lateral)
    axes[i, 0].axis('off')
    axes[i, 1].imshow(img_medial)
    axes[i, 1].axis('off')
    axes[i, 2].imshow(img_dorsal)
    axes[i, 2].axis('off')

    # Add the frequency band name as a vertical title in the first column
    axes[i, 0].text(-0.1, 0.5, band, fontsize=14, va='center', ha='right',
                   transform=axes[i, 0].transAxes, rotation=90)

def stc_band_power_plot(stc, band_powers, morph, subject, surfer_kwargs):
    # Create a figure with a grid of subplots (6 rows, 3 columns)
    fig, axes = plt.subplots(6, 3, figsize=(10, 10))
    axes = axes.reshape(6, 3)

    # Add column titles to the top row
    axes[0, 0].set_title("Lateral", fontsize=16)
    axes[0, 1].set_title("Medial", fontsize=16)
    axes[0, 2].set_title("Dorsal", fontsize=16)

    # Initialize storage for morphed band powers
    band_powers_morph = None

    for i, (band, power) in enumerate(band_powers.items()):
        # Morph the band power to fsaverage
        stc_band_morph = stc_per_band(morph, power, stc, subject)

        # Initialize band power matrix on the first iteration
        if band_powers_morph is None:
            lh_vertices, rh_vertices = stc_band_morph.vertices
            total_vertices = len(lh_vertices) + len(rh_vertices)
            band_powers_morph = np.zeros((total_vertices, len(band_powers)))

        # Store the morphed data for the current band
        band_powers_morph[:, i] = stc_band_morph.data.flatten()

        # Generate screenshots for lateral and medial views
        img_lateral = generate_brain_screenshot(stc_band_morph, 'lat', power, surfer_kwargs)
        img_medial = generate_brain_screenshot(stc_band_morph, 'med', power, surfer_kwargs)
        img_dorsal = generate_brain_screenshot(stc_band_morph, 'dor', power, surfer_kwargs)

        # Plot the images in subplots
        brains_plot(i,band,axes,img_lateral,img_medial,img_dorsal)
    
    return fig
