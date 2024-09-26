import numpy as np
import cv2
import torch

class ScaleFactorCalculationNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "ref_image": ("IMAGE",),
                "current_mask": ("IMAGE",),
            },
        }

    RETURN_TYPES = ("FLOAT",)
    FUNCTION = "calculate_scale_factor"
    CATEGORY = "image/processing"

    def calculate_scale_factor(self, ref_image: torch.Tensor, current_mask: torch.Tensor):
        print("Starting calculate_scale_factor function")

        # Convert tensors to numpy arrays
        ref_image_np = self.tensor_to_numpy(ref_image)
        current_mask_np = self.tensor_to_numpy(current_mask)
        print(f"Reference image shape: {ref_image_np.shape}, Current mask shape: {current_mask_np.shape}")

        # Ensure masks are binary and single-channel
        ref_image_gray = self.ensure_grayscale(ref_image_np)
        _, ref_mask_binary = cv2.threshold(ref_image_gray, 127, 255, cv2.THRESH_BINARY)
        print(f"Binary reference image mask shape: {ref_mask_binary.shape}")

        current_mask_gray = self.ensure_grayscale(current_mask_np)
        _, current_mask_binary = cv2.threshold(current_mask_gray, 127, 255, cv2.THRESH_BINARY)
        print(f"Binary current mask shape: {current_mask_binary.shape}")

        # Calculate the size (e.g., area or width) of the can in the reference image
        ref_contours, _ = cv2.findContours(ref_mask_binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not ref_contours:
            print("No contours found in reference image. Cannot calculate scale factor.")
            return (1.0,)  # Return scale factor of 1.0 as default

        ref_contour = max(ref_contours, key=cv2.contourArea)
        ref_rect = cv2.minAreaRect(ref_contour)
        ref_size = max(ref_rect[1])
        print(f"Reference can size: {ref_size}")

        # Calculate the size of the can in the current mask
        current_contours, _ = cv2.findContours(current_mask_binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not current_contours:
            print("No contours found in current mask. Cannot calculate scale factor.")
            return (1.0,)  # Return scale factor of 1.0 as default

        current_contour = max(current_contours, key=cv2.contourArea)
        current_rect = cv2.minAreaRect(current_contour)
        current_size = max(current_rect[1])
        print(f"Current can size: {current_size}")

        # Handle cases where size might be zero
        if current_size == 0:
            print("Current can size is zero. Cannot calculate scale factor.")
            return (1.0,)

        # Calculate scale factor
        scale_factor = ref_size / current_size
        print(f"Calculated scale factor: {scale_factor}")

        # Return the scale factor as a float
        return (float(scale_factor),)

    def tensor_to_numpy(self, tensor):
        # Convert ComfyUI IMAGE tensor to numpy array
        tensor = tensor.squeeze()
        print(f"Tensor shape after squeeze: {tensor.shape}")

        if len(tensor.shape) == 3:
            if tensor.shape[0] in [1, 3, 4]:  # Likely (C, H, W)
                array = (tensor.permute(1, 2, 0).cpu().numpy() * 255).astype(np.uint8)
            elif tensor.shape[2] in [1, 3, 4]:  # Likely (H, W, C)
                array = (tensor.cpu().numpy() * 255).astype(np.uint8)
            else:
                raise ValueError(f"Unexpected tensor shape: {tensor.shape}")
        elif len(tensor.shape) == 2:
            array = (tensor.cpu().numpy() * 255).astype(np.uint8)
            array = np.expand_dims(array, axis=2)  # Add channel dimension
        else:
            raise ValueError(f"Unexpected tensor shape after squeeze: {tensor.shape}")

        print(f"Numpy array shape after conversion: {array.shape}")
        return array

    def ensure_grayscale(self, img):
        print(f"Input image shape to ensure_grayscale: {img.shape}")
        if len(img.shape) == 2:
            print("Image is already grayscale")
            return img  # Already grayscale
        elif len(img.shape) == 3:
            if img.shape[2] == 1:
                print("Single-channel image, squeezing")
                return img[:, :, 0]  # Single-channel image
            elif img.shape[2] == 3:
                print("Converting RGB to grayscale")
                return cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
            elif img.shape[2] == 4:
                print("Converting RGBA to grayscale")
                return cv2.cvtColor(img, cv2.COLOR_RGBA2GRAY)
        raise ValueError(f"Unexpected image shape: {img.shape}")

NODE_CLASS_MAPPINGS = {
    "ScaleFactorCalculationNode": ScaleFactorCalculationNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ScaleFactorCalculationNode": "Scale Factor Calculation"
}

