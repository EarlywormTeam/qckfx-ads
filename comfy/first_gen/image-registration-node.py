import numpy as np
import cv2
import torch

class ImageRegistrationNode:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "image": ("IMAGE",),
                "image_mask": ("IMAGE",),
                "mask": ("IMAGE",),
            },
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "align_images"
    CATEGORY = "image/processing"

    def align_images(self, image: torch.Tensor, image_mask: torch.Tensor, mask: torch.Tensor):
        print("Starting align_images function")
        # Convert tensors to numpy arrays
        image_np = self.tensor_to_numpy(image)
        image_mask_np = self.tensor_to_numpy(image_mask)
        mask_np = self.tensor_to_numpy(mask)
        print(f"Image shape: {image_np.shape}, Image Mask shape: {image_mask.shape}, Mask shape: {mask_np.shape}")
        
        # Ensure mask is binary and single-channel
        image_mask_gray = self.ensure_grayscale(image_mask_np)
        _, image_mask_binary = cv2.threshold(image_mask_gray, 127, 255, cv2.THRESH_BINARY)
        print(f"Binary image mask shape: {image_mask_binary.shape}")

        mask_gray = self.ensure_grayscale(mask_np)
        _, mask_binary = cv2.threshold(mask_gray, 127, 255, cv2.THRESH_BINARY)
        print(f"Binary mask shape: {mask_binary.shape}")
        
        # Find contours of the image mask
        contours, _ = cv2.findContours(image_mask_binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        print(f"Number of contours found in image mask: {len(contours)}")
        
        if not contours:
            print("No contours found in image mask. Returning original image.")
            return (image,)
        
        # Find the largest contour (assuming it's the main object)
        main_contour = max(contours, key=cv2.contourArea)
        print(f"Area of main contour in image mask: {cv2.contourArea(main_contour)}")
        
        # Get the bounding rectangle of the main contour in the image mask
        x, y, w, h = cv2.boundingRect(main_contour)
        print(f"Bounding rectangle of object in image mask: x={x}, y={y}, w={w}, h={h}")
        
        # Calculate padding
        pad_left, pad_top = x, y
        pad_right, pad_bottom = image_mask_binary.shape[1] - (x + w), image_mask_binary.shape[0] - (y + h)
        print(f"Padding: left={pad_left}, top={pad_top}, right={pad_right}, bottom={pad_bottom}")
        
        # Crop the image to remove padding
        cropped_image = image_np[pad_top:pad_top+h, pad_left:pad_left+w]
        print(f"Cropped image shape: {cropped_image.shape}")
        
        # Find contours of the mask
        contours, _ = cv2.findContours(mask_binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        print(f"Number of contours found in mask: {len(contours)}")
        
        if not contours:
            print("No contours found in mask. Returning original image.")
            return (image,)
        
        # Find the largest contour (assuming it's the main object)
        main_contour = max(contours, key=cv2.contourArea)
        print(f"Area of main contour in mask: {cv2.contourArea(main_contour)}")
        
        # Get the rotated bounding rectangle
        rect = cv2.minAreaRect(main_contour)
        box = cv2.boxPoints(rect)
        box = np.int0(box)
        print(f"Rotated bounding box: {box}")
        
        # Get the angle of rotation
        angle = rect[2]
        
        # Adjust angle to minimize rotation
        if abs(angle) > 45:
            angle = angle - 90 if angle > 0 else angle + 90
        
        # Reverse the angle for clockwise rotation
        angle = -angle
        
        # Get the center, width, and height of the rotated rectangle
        center, (height, width) = rect[:2]
        
        print(f"Final rotation angle: {angle}")
        print(f"Rotated rectangle - Center: {center}, Width: {width}, Height: {height}")
        
        # Step 1: Rotate the cropped image
        rotation_matrix = cv2.getRotationMatrix2D((cropped_image.shape[1] / 2, cropped_image.shape[0] / 2), angle, 1.0)
        cos = np.abs(rotation_matrix[0, 0])
        sin = np.abs(rotation_matrix[0, 1])
        rotated_w = int((cropped_image.shape[1] * cos) + (cropped_image.shape[0] * sin))
        rotated_h = int((cropped_image.shape[1] * sin) + (cropped_image.shape[0] * cos))
        rotation_matrix[0, 2] += (rotated_w / 2) - cropped_image.shape[1] / 2
        rotation_matrix[1, 2] += (rotated_h / 2) - cropped_image.shape[0] / 2
        rotated_image = cv2.warpAffine(cropped_image, rotation_matrix, (rotated_w, rotated_h), flags=cv2.INTER_LINEAR)
        print(f"Rotated image shape: {rotated_image.shape}")
        
        # Step 2: Calculate scaling factor
        scale_x = width / rotated_image.shape[1]
        scale_y = height / rotated_image.shape[0]
        scale = max(scale_x, scale_y)  # Use the larger scaling factor to fill the mask area
        print(f"Calculated scaling factor: {scale}")
        
        # Step 3: Scale the rotated image
        new_w = int(rotated_image.shape[1] * scale)
        new_h = int(rotated_image.shape[0] * scale)
        scaled_image = cv2.resize(rotated_image, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
        print(f"Scaled image shape: {scaled_image.shape}")
        
        # Create a black background with the same size as the mask
        output_image = np.zeros_like(mask_np)
        print(f"Output image shape: {output_image.shape}")
        
        # Calculate the position to place the scaled image
        x_offset = max(0, int(center[0] - new_w / 2))
        y_offset = max(0, int(center[1] - new_h / 2))
        print(f"Offset for placement: x={x_offset}, y={y_offset}")
        
        # Place the scaled image onto the black background
        try:
            # Crop the scaled image if it's too large
            crop_x = min(new_w, mask_np.shape[1] - x_offset)
            crop_y = min(new_h, mask_np.shape[0] - y_offset)
            cropped_scaled_image = scaled_image[:crop_y, :crop_x]
            
            output_image[y_offset:y_offset+crop_y, x_offset:x_offset+crop_x] = cropped_scaled_image
            print(f"Placed image shape: {cropped_scaled_image.shape}")
            print("Successfully placed scaled image onto background")
        except ValueError as e:
            print(f"Error placing scaled image: {e}")
        
        # Apply the mask to the output image
        output_image = cv2.bitwise_and(output_image, output_image, mask=mask_binary)
        print(f"Final output image shape: {output_image.shape}")
        
        # Check if the output image is all black
        if np.all(output_image == 0):
            print("WARNING: Output image is completely black")
        else:
            print(f"Non-zero pixels in output image: {np.count_nonzero(output_image)}")
        
        # Convert back to tensor
        aligned_tensor = torch.from_numpy(output_image.astype(np.float32) / 255.0).unsqueeze(0)
        print(f"Aligned tensor shape: {aligned_tensor.shape}")
        
        return (aligned_tensor,)
 
    def tensor_to_numpy(self, tensor):
        # Convert ComfyUI IMAGE tensor to numpy array
        tensor = tensor.squeeze()
        print(f"Tensor shape after squeeze: {tensor.shape}")

        if len(tensor.shape) == 3:
            if tensor.shape[-1] in [1, 3, 4]:  # Likely (H, W, C)
                array = (tensor.cpu().numpy() * 255).astype(np.uint8)
            elif tensor.shape[0] in [1, 3, 4]:  # Likely (C, H, W)
                array = (tensor.permute(1, 2, 0).cpu().numpy() * 255).astype(np.uint8)
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
                return img.squeeze()  # Single-channel image
            elif img.shape[2] == 3:
                print("Converting RGB to grayscale")
                return cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
            elif img.shape[2] == 4:
                print("Converting RGBA to grayscale")
                return cv2.cvtColor(img, cv2.COLOR_RGBA2GRAY)
        raise ValueError(f"Unexpected image shape: {img.shape}")

NODE_CLASS_MAPPINGS = {
    "ImageRegistrationNode": ImageRegistrationNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ImageRegistrationNode": "Image Registration"
}
