import numpy as np
import cv2
import torch
import logging

def select_best_contour(contours, image_shape, original_aspect_ratio):
    logging.info(f"Selecting best contour from {len(contours)} contours")
    logging.info(f"Image shape: {image_shape}")

    if not contours:
        logging.warning("No contours found")
        return None
    
    image_area = image_shape[0] * image_shape[1]
    logging.info(f"Total image area: {image_area}")

    best_contour = None
    best_score = float('-inf')
    
    for i, contour in enumerate(contours):
        area = cv2.contourArea(contour)
        perimeter = cv2.arcLength(contour, True)
        x, y, w, h = cv2.boundingRect(contour)
        aspect_ratio = max(w, h) / min(w, h)
        
        logging.info(f"Contour {i}:")
        logging.info(f"  Area: {area}")
        logging.info(f"  Perimeter: {perimeter}")
        logging.info(f"  Bounding box: x={x}, y={y}, w={w}, h={h}")
        logging.info(f"  Aspect ratio: {aspect_ratio}")

        # Calculate circularity
        circularity = 4 * np.pi * area / (perimeter * perimeter) if perimeter > 0 else 0
        logging.info(f"  Circularity: {circularity}")

        # Calculate convexity
        hull = cv2.convexHull(contour)
        hull_area = cv2.contourArea(hull)
        convexity = area / hull_area if hull_area > 0 else 0
        logging.info(f"  Convexity: {convexity}")

        # Calculate solidity
        solidity = area / hull_area if hull_area > 0 else 0
        logging.info(f"  Solidity: {solidity}")

        # Increase the weight of the area score
        area_score = (area / image_area) * 3 if area > image_area * 0.1 else 0
        
        # Favor contours with aspect ratios similar to the original image
        aspect_ratio_score = 1 / (abs(aspect_ratio - original_aspect_ratio) + 1)
        
        # Favor contours that are more centered
        center_x, center_y = x + w/2, y + h/2
        distance_from_center = np.sqrt((center_x - image_shape[1]/2)**2 + (center_y - image_shape[0]/2)**2)
        center_score = 1 - (distance_from_center / (np.sqrt(image_shape[0]**2 + image_shape[1]**2) / 2))
        
        # Penalize very small contours
        size_penalty = 0 if area > image_area * 0.1 else -2
        
        # Calculate the total score
        score = (area_score + aspect_ratio_score + center_score + 
                 circularity + convexity + solidity + size_penalty)
        
        logging.info(f"  Scores:")
        logging.info(f"    Area score: {area_score}")
        logging.info(f"    Aspect ratio score: {aspect_ratio_score}")
        logging.info(f"    Center score: {center_score}")
        logging.info(f"    Circularity: {circularity}")
        logging.info(f"    Convexity: {convexity}")
        logging.info(f"    Solidity: {solidity}")
        logging.info(f"    Size penalty: {size_penalty}")
        logging.info(f"    Total score: {score}")

        if score > best_score:
            best_score = score
            best_contour = contour
            logging.info(f"  New best contour")
        else:
            logging.info(f"  Not better than current best")

    if best_contour is not None:
        logging.info(f"Selected best contour with score: {best_score}")
        logging.info(f"Best contour area: {cv2.contourArea(best_contour)}")
        x, y, w, h = cv2.boundingRect(best_contour)
        logging.info(f"Best contour bounding box: x={x}, y={y}, w={w}, h={h}")
    else:
        logging.warning("No suitable contour found")

    return best_contour

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
        logging.info("Starting align_images function")
        
        # Convert tensors to numpy arrays
        image_np = self.tensor_to_numpy(image)
        image_mask_np = self.tensor_to_numpy(image_mask)
        mask_np = self.tensor_to_numpy(mask)
        logging.info(f"Image shape: {image_np.shape}, Image Mask shape: {image_mask_np.shape}, Mask shape: {mask_np.shape}")
        
        # Calculate the original aspect ratio
        original_aspect_ratio = image_np.shape[0] / image_np.shape[1]
        logging.info(f"Original aspect ratio: {original_aspect_ratio}")

        # Ensure mask is binary and single-channel
        image_mask_gray = self.ensure_grayscale(image_mask_np)
        _, image_mask_binary = cv2.threshold(image_mask_gray, 127, 255, cv2.THRESH_BINARY)
        logging.info(f"Binary image mask shape: {image_mask_binary.shape}")

        mask_gray = self.ensure_grayscale(mask_np)
        _, mask_binary = cv2.threshold(mask_gray, 127, 255, cv2.THRESH_BINARY)
        logging.info(f"Binary mask shape: {mask_binary.shape}")
        
        # Find contours of the image mask
        contours, _ = cv2.findContours(image_mask_binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        logging.info(f"Number of contours found in image mask: {len(contours)}")
        
        # Select the best contour for the image mask
        main_contour_image = select_best_contour(contours, image_mask_binary.shape, original_aspect_ratio)
        if main_contour_image is None:
            logging.error("No suitable contour found in image mask. Cannot proceed with alignment.")
            return (image,)
        
        # Get the bounding rectangle of the main contour in the image mask
        x, y, w, h = cv2.boundingRect(main_contour_image)
        logging.info(f"Bounding rectangle of object in image mask: x={x}, y={y}, w={w}, h={h}")
        
        # Calculate padding
        pad_left, pad_top = x, y
        pad_right, pad_bottom = image_mask_binary.shape[1] - (x + w), image_mask_binary.shape[0] - (y + h)
        logging.info(f"Padding: left={pad_left}, top={pad_top}, right={pad_right}, bottom={pad_bottom}")
        
        # Crop the image to remove padding
        cropped_image = image_np[pad_top:pad_top+h, pad_left:pad_left+w]
        logging.info(f"Cropped image shape: {cropped_image.shape}")
        
        # Find contours of the mask
        contours, _ = cv2.findContours(mask_binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        logging.info(f"Number of contours found in mask: {len(contours)}")
        
        # Select the best contour for the mask
        main_contour_mask = select_best_contour(contours, mask_binary.shape, original_aspect_ratio)
        if main_contour_mask is None:
            logging.error("No suitable contour found in mask. Cannot proceed with alignment.")
            return (image,)
        
        # Get the rotated bounding rectangle
        rect = cv2.minAreaRect(main_contour_mask)
        box = cv2.boxPoints(rect)
        box = np.int0(box)
        logging.info(f"Rotated bounding box: {box}")
        
        # Get the angle of rotation
        angle = rect[2]
        logging.info(f"Initial rotation angle: {angle}")
        
        # Adjust angle to minimize rotation
        if abs(angle) > 45:
            angle = 90 + angle if angle < 0 else 90 - angle
        logging.info(f"Adjusted rotation angle: {angle}")
        
        # Get the center, width, and height of the rotated rectangle
        center, (width, height) = rect[:2]
        logging.info(f"Rotated rectangle - Center: {center}, Width: {width}, Height: {height}")
        
        # Rotate the cropped image
        rotation_matrix = cv2.getRotationMatrix2D((cropped_image.shape[1] / 2, cropped_image.shape[0] / 2), angle, 1.0)
        rotated_image = cv2.warpAffine(cropped_image, rotation_matrix, (cropped_image.shape[1], cropped_image.shape[0]), flags=cv2.INTER_LINEAR)
        logging.info(f"Rotated image shape: {rotated_image.shape}")
        
        # Calculate scaling factor
        scale_x = width / rotated_image.shape[1]
        scale_y = height / rotated_image.shape[0]
        scale = min(scale_x, scale_y)  # Use the smaller scaling factor to fit within the mask area
        logging.info(f"Calculated scaling factor: {scale}")
        logging.info(f"Scale components - X: {scale_x}, Y: {scale_y}")
        
        # Scale the rotated image
        new_w = int(rotated_image.shape[1] * scale)
        new_h = int(rotated_image.shape[0] * scale)
        scaled_image = cv2.resize(rotated_image, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
        logging.info(f"Scaled image shape: {scaled_image.shape}")
        
        # Create a black background with the same size as the mask
        output_image = np.zeros_like(mask_np)
        logging.info(f"Output image shape: {output_image.shape}")
        
        # Calculate the position to place the scaled image
        x_offset = max(0, int(center[0] - new_w / 2))
        y_offset = max(0, int(center[1] - new_h / 2))
        logging.info(f"Offset for placement: x={x_offset}, y={y_offset}")
        
        # Place the scaled image onto the black background
        try:
            # Crop the scaled image if it's too large
            crop_x = min(new_w, mask_np.shape[1] - x_offset)
            crop_y = min(new_h, mask_np.shape[0] - y_offset)
            cropped_scaled_image = scaled_image[:crop_y, :crop_x]
            
            output_image[y_offset:y_offset+crop_y, x_offset:x_offset+crop_x] = cropped_scaled_image
            logging.info(f"Placed image shape: {cropped_scaled_image.shape}")
            logging.info("Successfully placed scaled image onto background")
        except ValueError as e:
            logging.error(f"Error placing scaled image: {e}")
            return (image,)
        
        # Apply the mask to the output image
        output_image = cv2.bitwise_and(output_image, output_image, mask=mask_binary)
        logging.info(f"Final output image shape: {output_image.shape}")
        
        # Check if the output image is all black
        if np.all(output_image == 0):
            logging.error("Output image is completely black")
            return (image,)
        else:
            logging.info(f"Non-zero pixels in output image: {np.count_nonzero(output_image)}")
        
        # Convert back to tensor
        aligned_tensor = torch.from_numpy(output_image.astype(np.float32) / 255.0).unsqueeze(0)
        logging.info(f"Aligned tensor shape: {aligned_tensor.shape}")
        
        return (aligned_tensor,)
 
    def tensor_to_numpy(self, tensor):
        # Convert ComfyUI IMAGE tensor to numpy array
        tensor = tensor.squeeze()
        logging.info(f"Tensor shape after squeeze: {tensor.shape}")

        if len(tensor.shape) == 3:
            if tensor.shape[-1] in [1, 3, 4]:  # Likely (H, W, C)
                array = (tensor.cpu().numpy() * 255).astype(np.uint8)
            elif tensor.shape[0] in [1, 3, 4]:  # Likely (C, H, W)
                array = (tensor.permute(1, 2, 0).cpu().numpy() * 255).astype(np.uint8)
            else:
                logging.error(f"Unexpected tensor shape: {tensor.shape}")
                raise ValueError(f"Unexpected tensor shape: {tensor.shape}")
        elif len(tensor.shape) == 2:
            array = (tensor.cpu().numpy() * 255).astype(np.uint8)
            array = np.expand_dims(array, axis=2)  # Add channel dimension
        else:
            logging.error(f"Unexpected tensor shape after squeeze: {tensor.shape}")
            raise ValueError(f"Unexpected tensor shape after squeeze: {tensor.shape}")

        logging.info(f"Numpy array shape after conversion: {array.shape}")
        return array

    def ensure_grayscale(self, img):
        logging.info(f"Input image shape to ensure_grayscale: {img.shape}")
        if len(img.shape) == 2:
            logging.info("Image is already grayscale")
            return img  # Already grayscale
        elif len(img.shape) == 3:
            if img.shape[2] == 1:
                logging.info("Single-channel image, squeezing")
                return img.squeeze()  # Single-channel image
            elif img.shape[2] == 3:
                logging.info("Converting RGB to grayscale")
                return cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
            elif img.shape[2] == 4:
                logging.info("Converting RGBA to grayscale")
                return cv2.cvtColor(img, cv2.COLOR_RGBA2GRAY)
        logging.error(f"Unexpected image shape: {img.shape}")
        raise ValueError(f"Unexpected image shape: {img.shape}")

NODE_CLASS_MAPPINGS = {
    "ImageRegistrationNode": ImageRegistrationNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ImageRegistrationNode": "Image Registration"
}
