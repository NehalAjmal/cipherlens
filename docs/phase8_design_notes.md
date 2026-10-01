# Phase 8: Detector-Level Model Integrity Design Notes

## 1. The Challenge of Object Detector Backdoors

Unlike image classifiers which output a single probability distribution $P(y|x)$, object detectors (like YOLO, SSD, or Faster R-CNN) output a dense tensor of predictions representing:
1. **Objectness** (is there an object here?)
2. **Classification** (what is the object?)
3. **Bounding Box Regression** (where exactly is it?)

A backdoor in an object detector can manifest in several distinct ways:
- **Generation (False Positives):** A trigger causes the model to hallucinate a specific object class at a specific location or globally.
- **Evasion (False Negatives):** A trigger suppresses the objectness score, effectively making the model "blind" to objects in the scene.
- **Misclassification:** A trigger alters the class prediction of a valid bounding box without moving it.
- **Displacement:** A trigger forces the bounding box coordinates to shift away from the true object.

**Critical Constraint:** Phase 8 detector-level support is explicitly scoped and limited to **one** reference architecture: `torchvision.models.detection.fasterrcnn_resnet50_fpn`. This avoids introducing new dependencies and provides a standardized module structure that can be sliced reliably. Attempting to generalize across arbitrary YOLO or SSD architectures is out of scope.

Standard Neural Cleanse (NC) minimizes a cross-entropy loss to force a single global classification. Extending this to detectors requires rethinking the adversarial objective function.

---

## 2. Extending Neural Cleanse to Detectors

To reconstruct a trigger $(m, p)$ (mask and pattern) for a detector, we must define a differentiable target loss $L_{adv}$ that operates *before* Non-Maximum Suppression (NMS), as NMS breaks the computational graph.

### Target 1: Targeted Hallucination / Misclassification
To reverse-engineer a trigger that forces the detector to output a specific target class $c_t$, we want to maximize the classification confidence *and* the objectness score for at least one grid cell/anchor.

**Proposed Loss Formulation:**
$$ L_{adv} = - \log \left( \sum_{i, j} \exp\left( \text{Obj}_{i,j} \cdot P(y_{i,j} = c_t) \right) \right) $$
Where $i, j$ iterate over the dense spatial grid of the detector's output. By using the smooth `logsumexp` function instead of a hard maximum, we provide a continuous, non-sparse gradient during the trigger optimization loop, guiding the trigger to cause highly localized, high-confidence hallucinations.

### Target 2: Untargeted Evasion (Blindness Attack)
To reverse-engineer a trigger designed to hide objects (e.g., a "stealth" patch for a stop sign), we want to minimize the objectness score globally.

**Proposed Loss Formulation:**
$$ L_{adv} = \frac{1}{N} \sum_{i,j} \text{Obj}_{i,j}^2 $$
This pushes the objectness of all predicted bounding boxes toward zero.

### The Full Optimization Objective
As with standard NC, we balance the adversarial effect with an $L_1$ penalty on the mask size to find the smallest possible trigger:
$$ \min_{m, p} \left( L_{adv}(F((1-m) \odot x + m \odot p)) + \lambda \cdot \|m\|_1 \right) $$

---

## 3. Tightening the Crop-Classifier Bridge

Optimizing the above loss directly through a complex YOLOv8 or Faster R-CNN architecture is notoriously difficult due to extreme architecture variance (e.g., differing anchor box formats, decoupled heads, FPN layers). 

To bridge the gap between our Phase 4 classifier-focused NC and full detector NC, we can utilize a **Crop-Classifier Bridge**.

**The Current Strategy:**
In a naive crop-classifier approach, one might just crop ground-truth bounding boxes from the dataset, feed them to a standard classifier, and run NC. This fails because the backdoor trigger might rely on spatial context *outside* the bounding box, or the model might use a shared backbone.

**The Tightened Strategy (Phase 8 Proposal):**
1. **White-Box Sub-Graph Extraction:** Instead of treating the detector as a black box, we programmatically slice the PyTorch `nn.Module` to isolate the shared backbone and the classification head, bypassing the regression head.
2. **Global Average Pooling (GAP) Surrogate:** If the detector uses a fully convolutional architecture (like YOLO), we can attach a temporary GAP layer to the output of the final backbone feature map, effectively collapsing the dense grid into a single 1D feature vector per image.
3. **Surrogate Optimization:** We run the standard Neural Cleanse optimization loop over this surrogate GAP-classifier. 

*Why this works:* If a universal backdoor trigger exists in the weights, it must significantly activate specific feature maps in the shared backbone. By optimizing a trigger to maximize the average activation of the target class's feature map across the entire image, we can reconstruct the trigger without wrestling with bounding box anchor math.

**Implementation Details:**
The logic for slicing the Faster R-CNN model and computing the specialized losses will live in `cipherlens/model_integrity/detector_bridge.py`. It will be imported and dispatched dynamically from within `cipherlens/model_integrity/access_tier.py` when a supported detector architecture is identified. We will not create a new top-level orchestrator file.

---

## 4. Feasibility & Contingency Plan

**Risks:**
- Detector architectures in PyTorch are rarely standardized. Slicing a YOLO model to extract just the `L_cls` and `L_obj` logits is highly specific to the library (e.g., `ultralytics` vs `torchvision`).
- The surrogate GAP approach might fail to reconstruct spatially-dependent triggers (triggers that only work if placed in the corner of the image).
- Optimization time is severely multiplied when running backpropagation through high-resolution detector grids compared to standard 224x224 classifiers.

**Contingency (The "Honest Degradation" Rule):**
If wrapping arbitrary detector architectures into the generalized loss function proves too fragile or computationally intractable within the time budget, I will:
1. Halt implementation before introducing unstable, hard-coded hacks.
2. Document the exact structural limitations in `docs/COVERAGE_STATEMENT.md` (e.g., "White-box Neural Cleanse currently supports image classifiers only; object detectors degrade to black-box STRIP analysis").
3. Ensure the `access_tier.py` orchestrator cleanly catches unsupported detector architectures, logs an `INFO` skip reason, and gracefully defaults to the `STRIP` black-box battery (which is naturally architecture-agnostic).
