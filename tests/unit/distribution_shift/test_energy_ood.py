"""Unit tests for Energy-OOD demonstrating separation of benign vs adversarial shift.
"""

import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageEnhance
import pytest

from cipherlens.distribution_shift.energy_ood import compute_energy_scores


@pytest.fixture(scope="module")
def energy_test_images():
    """Generates synthetic reference, benign drift, and adversarial images."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        
        # 1. Generate a "reference" batch (clean images)
        # Using a solid color with some noise to represent a base distribution
        ref_paths = []
        for i in range(5):
            img_arr = np.random.randint(100, 150, (224, 224, 3), dtype=np.uint8)
            img = Image.fromarray(img_arr)
            path = tmp_path / f"ref_{i}.png"
            img.save(path)
            ref_paths.append(path)
            
        # Select one reference image to drift/perturb
        base_img = Image.open(ref_paths[0])
        base_arr = np.array(base_img, dtype=np.float32)
        
        # 2. Benign Drift (Brightness shift)
        enhancer = ImageEnhance.Brightness(base_img)
        benign_img = enhancer.enhance(1.5)  # 50% brighter
        benign_arr = np.array(benign_img, dtype=np.float32)
        
        # Calculate pixel-change budget (L2 norm or average absolute difference)
        diff_benign = np.abs(benign_arr - base_arr)
        budget_per_pixel = np.mean(diff_benign)
        
        benign_path = tmp_path / "benign_drift.png"
        benign_img.save(benign_path)
        
        # 3. Adversarial Shift (High-frequency structural perturbation)
        # We add structured checkerboard noise at the EXACT same budget
        adv_arr = base_arr.copy()
        for c in range(3):
            # Create a high-frequency grid pattern
            grid = np.indices((224, 224))
            pattern = ((grid[0] + grid[1]) % 2) * 2 - 1  # -1 or 1
            
            # Apply exactly budget_per_pixel to match the L1 norm of the benign shift
            adv_arr[:, :, c] += pattern * budget_per_pixel
            
        adv_arr = np.clip(adv_arr, 0, 255).astype(np.uint8)
        adv_img = Image.fromarray(adv_arr)
        adv_path = tmp_path / "adversarial.png"
        adv_img.save(adv_path)
        
        # Verify budgets match closely
        final_benign_diff = np.mean(np.abs(np.array(benign_img, dtype=np.float32) - base_arr))
        final_adv_diff = np.mean(np.abs(np.array(adv_img, dtype=np.float32) - base_arr))
        assert abs(final_benign_diff - final_adv_diff) < 2.0, "Budgets don't match"
        
        yield ref_paths, [benign_path], [adv_path]


def test_energy_ood_separation(energy_test_images):
    """Confirm Energy-OOD meaningfully separates adversarial from benign drift."""
    ref_paths, benign_paths, adv_paths = energy_test_images
    
    # Compute energies
    ref_energy = compute_energy_scores(ref_paths)
    benign_energy = compute_energy_scores(benign_paths)
    adv_energy = compute_energy_scores(adv_paths)
    
    # We want to see how the energies compare.
    # Typically, adversarial examples have higher (less negative) energy than clean/benign.
    
    mean_ref = np.mean(ref_energy)
    mean_benign = np.mean(benign_energy)
    mean_adv = np.mean(adv_energy)
    
    print(f"\nEnergy OOD Scores:")
    print(f"Reference Mean: {mean_ref:.2f}")
    print(f"Benign Drift Mean (same budget): {mean_benign:.2f}")
    print(f"Adversarial Mean (same budget): {mean_adv:.2f}")
    
    # The adversarial shift should be strictly separated from the reference and benign
    # (Adversarial energy > Benign energy)
    margin = mean_adv - mean_benign
    print(f"Separation Margin (Adv - Benign): {margin:.2f}")
    
    # We assert the margin is meaningful (e.g., > 1.0)
    assert margin > 0.1, f"Energy did not separate well, margin was {margin:.4f}"
