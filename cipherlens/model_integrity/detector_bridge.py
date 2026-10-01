import torch
import torch.nn as nn
from cipherlens.utils.logging_config import get_logger

logger = get_logger(__name__)


class FasterRCNNSurrogate(nn.Module):
    """Surrogate classification model for Faster R-CNN.
    
    This wraps a torchvision Faster R-CNN model and exposes only the shared backbone
    followed by a Global Average Pooling (GAP) layer and a single linear layer
    matching the classification head's size.
    
    This allows standard classifier-based Neural Cleanse to optimize triggers that
    activate the backbone features without wrestling with NMS or anchor math.
    """
    
    def __init__(self, faster_rcnn_model: nn.Module):
        super().__init__()
        self.backbone = faster_rcnn_model.backbone
        # Extract the number of output channels from the backbone.
        # Faster R-CNN with FPN outputs an OrderedDict of feature maps.
        # We'll use the '0' feature map for simplicity in the surrogate.
        # This is an approximation for NC gradient flow.
        try:
            out_channels = self.backbone.out_channels
        except AttributeError:
            out_channels = 256 # Default FPN out channels
            
        self.gap = nn.AdaptiveAvgPool2d((1, 1))
        
        # We don't have the exact num_classes easily accessible without inspecting the box_predictor.
        # However, for Neural Cleanse, we just need a projection space.
        # If we can't find it, we default to 91 (COCO).
        num_classes = 91 
        if hasattr(faster_rcnn_model, 'roi_heads') and hasattr(faster_rcnn_model.roi_heads, 'box_predictor'):
            if hasattr(faster_rcnn_model.roi_heads.box_predictor, 'cls_score'):
                num_classes = faster_rcnn_model.roi_heads.box_predictor.cls_score.out_features
                
        # We use a 1x1 convolution instead of a Linear layer to project
        # the feature map channels to num_classes while preserving the spatial grid.
        self.classifier = nn.Conv2d(out_channels, num_classes, kernel_size=1)
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass for the surrogate.
        
        Args:
            x: Input image batch (B, C, H, W)
            
        Returns:
            Dense spatial grid of logits (B, num_classes, H', W')
        """
        features = self.backbone(x)
        
        # We take the lowest resolution/highest level feature map ('0' usually)
        # to represent the global receptive field.
        # Alternatively, summing across FPN levels resized to the largest map is possible,
        # but for simplicity we take the '0' feature map.
        feat = features['0']
        
        # Apply 1x1 conv to get dense class logits over the spatial grid
        return self.classifier(feat)


def is_faster_rcnn(model_obj: nn.Module) -> bool:
    """Check if the model is a torchvision Faster R-CNN architecture."""
    # We duck-type instead of relying on exact class names to handle compiled/wrapped models
    has_backbone = hasattr(model_obj, "backbone")
    has_rpn = hasattr(model_obj, "rpn")
    has_roi = hasattr(model_obj, "roi_heads")
    return has_backbone and has_rpn and has_roi


def compute_target_1_loss(logits: torch.Tensor, target_class: int) -> torch.Tensor:
    """Compute the Target 1 adversarial loss for trigger reconstruction.
    
    Instead of a hard maximum over the spatial grid, we use logsumexp
    for a smoother, continuous gradient during optimization.
    
    Args:
        logits: Dense spatial grid (B, num_classes, H, W)
        target_class: The class index to hallucinate
        
    Returns:
        Scalar loss value to be minimized.
    """
    # Extract the target class spatial grid: (B, H, W)
    target_logits = logits[:, target_class, :, :]
    # Flatten spatial dimensions: (B, H * W)
    flattened = target_logits.view(target_logits.size(0), -1)
    
    # Smooth max over the grid
    # L_adv = -logsumexp(Obj * P(c_t))
    return -torch.logsumexp(flattened, dim=1).mean()


def wrap_detector_if_needed(model_obj: nn.Module) -> nn.Module:
    """Wrap a supported object detector in a classification surrogate.
    
    If the model is not a supported detector, it returns the model unchanged.
    """
    if is_faster_rcnn(model_obj):
        logger.info("Detected torchvision Faster R-CNN architecture. Wrapping in GAP surrogate.")
        return FasterRCNNSurrogate(model_obj)
        
    # Other architectures (YOLO, SSD) are out of scope for Phase 8.
    return model_obj
