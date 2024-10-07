import os
import math
from PIL import Image
import numpy as np

def get_resampling_filter():
    """
    Returns the appropriate resampling filter based on the Pillow version.
    """
    if hasattr(Image, 'Resampling'):
        return Image.Resampling.LANCZOS
    else:
        return Image.LANCZOS

def trim_image(im):
    """
    Trim the transparent borders of the image.
    """
    # Convert to numpy array
    img_data = np.array(im)
    
    # If image has alpha channel
    if img_data.shape[2] == 4:
        alpha = img_data[:, :, 3]
    else:
        # If no alpha channel, consider all pixels as opaque
        alpha = np.ones(img_data.shape[:2], dtype=bool)
    
    # Find bounding box
    non_empty_columns = np.where(alpha.max(axis=0))[0]
    non_empty_rows = np.where(alpha.max(axis=1))[0]
    
    if non_empty_rows.size and non_empty_columns.size:
        crop_box = (non_empty_columns[0], non_empty_rows[0],
                    non_empty_columns[-1] + 1, non_empty_rows[-1] + 1)
        return im.crop(crop_box)
    else:
        # Image is fully transparent
        return im

def resize_with_width(im, target_width):
    """
    Resize image to target width while maintaining aspect ratio.
    """
    w_percent = (target_width / float(im.width))
    target_height = int((float(im.height) * float(w_percent)))
    resample_filter = get_resampling_filter()
    return im.resize((target_width, target_height), resample_filter)

def segment_image(im, segment_height=768, num_segments=10):
    """
    Segment the image vertically into overlapping segments.
    """
    segments = []
    total_height = im.height
    step = max((total_height - segment_height) / (num_segments - 1), 0)
    
    for i in range(num_segments):
        upper = int(i * step)
        lower = upper + segment_height
        if lower > total_height:
            lower = total_height
            upper = lower - segment_height
            if upper < 0:
                upper = 0
                lower = min(segment_height, total_height)
        box = (0, upper, im.width, lower)
        segment = im.crop(box)
        
        # If the segment is smaller than desired, pad it
        if segment.height < segment_height:
            padded = Image.new("RGBA", (im.width, segment_height), (0,0,0,0))
            padded.paste(segment, (0,0))
            segment = padded
        segments.append(segment)
    return segments

def resize_original(im, target_height=768, final_size=(768,768)):
    """
    Resize original image to have height 768, width <=768,
    and pad with transparency to make it 768x768.
    """
    # Calculate new width to maintain aspect ratio
    w_percent = (target_height / float(im.height))
    new_width = int((float(im.width) * float(w_percent)))
    resample_filter = get_resampling_filter()
    resized = im.resize((new_width, target_height), resample_filter)
    
    # Create a new transparent image and paste the resized image centered horizontally
    new_im = Image.new("RGBA", final_size, (0,0,0,0))
    x_offset = (final_size[0] - new_width) // 2
    new_im.paste(resized, (x_offset, 0))
    return new_im

def process_image(input_path, output_folder):
    """
    Process the image as per the requirements and save outputs in a folder.
    """
    # Open image
    im = Image.open(input_path).convert("RGBA")
    
    # Step 1a: Trim the image
    trimmed = trim_image(im)
    
    # Step 1b: Resize to width 768
    zoomed = resize_with_width(trimmed, 768)
    
    # Step 1c: Segment into 10 overlapping images of 768x768
    segments = segment_image(zoomed, segment_height=768, num_segments=10)
    
    # Step 2a: Resize original image
    resized_original = resize_original(trimmed, target_height=768, final_size=(768,768))
    
    # Create output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)
    
    # Save segments
    for idx, seg in enumerate(segments, 1):
        seg.save(os.path.join(output_folder, f'segment_{idx}.png'))
    
    # Save resized original
    resized_original.save(os.path.join(output_folder, 'resized_original.png'))
    
    print(f"All images have been processed and saved to {output_folder}")
    return output_folder

if __name__ == "__main__":
    import argparse

    # Set up argument parser
    parser = argparse.ArgumentParser(description='Process an image as per specified requirements.')
    parser.add_argument('input_image', help='Path to the input image with transparency.')
    parser.add_argument('-o', '--output', default='output_images', help='Name of the output folder.')

    args = parser.parse_args()

    # Check if input file exists
    if not os.path.isfile(args.input_image):
        print(f"Error: The file {args.input_image} does not exist.")
        exit(1)
    
    # Process the image
    output_folder = process_image(args.input_image, args.output)
    print(f"Output folder: {output_folder}")

