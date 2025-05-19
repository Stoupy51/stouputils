
# Imports
import itertools

from .keras.all import (
    VGG16,
    VGG19,
    ConvNeXtBase,
    ConvNeXtLarge,
    ConvNeXtSmall,
    ConvNeXtTiny,
    ConvNeXtXLarge,
    DenseNet121,
    DenseNet169,
    DenseNet201,
    EfficientNetB0,
    EfficientNetV2B0,
    EfficientNetV2L,
    EfficientNetV2M,
    EfficientNetV2S,
    MobileNet,
    MobileNetV2,
    MobileNetV3Large,
    MobileNetV3Small,
    ResNet50V2,
    ResNet101V2,
    ResNet152V2,
    SqueezeNet,
    Xception,
)
from .model_interface import ModelInterface

# Other models
from .sandbox import Sandbox


# Create a custom dictionary class to allow for documentation
class ModelClassMap(dict[type[ModelInterface], tuple[str, ...]]):
    pass

# Routine map
CLASS_MAP: ModelClassMap = ModelClassMap({
    SqueezeNet:         ("squeezenet", "squeezenets", "all", "often"),

    DenseNet121:        ("densenet121", "densenets", "all", "often", "good"),
    DenseNet169:        ("densenet169", "densenets", "all", "often", "good"),
    DenseNet201:        ("densenet201", "densenets", "all", "often", "good"),

    EfficientNetB0:     ("efficientnetb0", "efficientnets", "all"),
    EfficientNetV2B0:   ("efficientnetv2b0", "efficientnets", "all"),
    EfficientNetV2S:    ("efficientnetv2s", "efficientnets", "all", "often"),
    EfficientNetV2M:    ("efficientnetv2m", "efficientnets", "all", "often"),
    EfficientNetV2L:    ("efficientnetv2l", "efficientnets", "all", "often"),

    ConvNeXtTiny:       ("convnexttiny", "convnexts", "all", "often", "good"),
    ConvNeXtSmall:      ("convnextsmall", "convnexts", "all", "often"),
    ConvNeXtBase:       ("convnextbase", "convnexts", "all", "often", "good"),
    ConvNeXtLarge:      ("convnextlarge", "convnexts", "all", "often"),
    ConvNeXtXLarge:     ("convnextxlarge", "convnexts", "all", "often", "good"),

    VGG16:              ("vgg16", "vggs", "all"),
    VGG19:              ("vgg19", "vggs", "all"),

    MobileNet:          ("mobilenet", "mobilenets", "all"),
    MobileNetV2:        ("mobilenetv2", "mobilenets", "all", "often"),
    MobileNetV3Small:   ("mobilenetv3small", "mobilenets", "all", "often"),
    MobileNetV3Large:   ("mobilenetv3large", "mobilenets", "all", "often", "good"),

    ResNet50V2:         ("resnet50v2", "resnetsv2", "resnets", "all", "often"),
    ResNet101V2:        ("resnet101v2", "resnetsv2", "resnets", "all", "often"),
    ResNet152V2:        ("resnet152v2", "resnetsv2", "resnets", "all", "often"),

    Xception:           ("xception", "xceptions", "all", "often"),
    Sandbox:            ("sandbox",),
})

# All models names and aliases
ALL_MODELS: list[str] = sorted(set(itertools.chain.from_iterable(v for v in CLASS_MAP.values())))
""" All models names and aliases found in the `CLASS_MAP` dictionary. """

# Additional docstring
new_docstring: str = "\n\n" + "\n".join(f"- {k.__name__}: {v}" for k, v in CLASS_MAP.items())
ModelClassMap.__doc__ = "Dictionary mapping class to their names and aliases. " + new_docstring
CLASS_MAP.__doc__ = ModelClassMap.__doc__

