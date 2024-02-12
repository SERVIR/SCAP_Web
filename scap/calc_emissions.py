import rasterio
from rasterio.mask import mask
import numpy as np

# Replace with your actual file paths and desired output name
forest_change_path = "/home/alex/shared/SCAP/fcc_working/fcc/esri/INVERTED_REPROJECTED_fcc_esri_peru_2018_1ha.tif"
AGB_path = "/home/alex/shared/SCAP/agb/Resampled_1ha/global_agb_2000_liu_.tif"
output_path = "/home/alex/shared/SCAP/emissions_test.tif"

with rasterio.open(forest_change_path) as src_change, rasterio.open(AGB_path) as src_AGB:
    # Check if resolutions match
    if src_change.transform != src_AGB.transform:
        raise ValueError("Rasters must have the same resolution and transform!")

    # Create output TIF with matching profile
    profile = src_AGB.profile.copy()
    profile.update({'count': 1})  # Update band count to 1 for masked output
    with rasterio.open(output_path, 'w', **profile) as dst:

        for (_,window) in src_change.block_windows(1):
            # Read blocks of data
            forest_change_block = src_change.read(1, window=window)
            AGB_block = src_AGB.read(1, window=window)

            # Create mask for the block
            forest_loss_mask = forest_change_block == 1
            print(forest_loss_mask.shape)

            # Apply mask to AGB block
            AGB_masked_block = np.multiply(AGB_block, forest_loss_mask)

            # Write masked block to output TIF
            dst.write(AGB_masked_block, window=window, indexes=1)

print(f"Masked AGB values written to {output_path} in blocks")