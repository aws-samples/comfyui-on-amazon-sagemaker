from .sagemaker_node import Text2ImageNode


NODE_CLASS_MAPPINGS = {
    "Text2ImageNode": Text2ImageNode
}

__all__ = ['NODE_CLASS_MAPPINGS']