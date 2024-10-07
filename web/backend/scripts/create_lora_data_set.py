import os
import shutil
import asyncio
from scripts.create_image_set import process_image
from scripts.caption_image_set import caption_image_set

async def create_lora_data_set(input_image_path, output_folder="lora_dataset", prefix="", postfix=""):
    # Step 1: Process the image
    processed_folder = process_image(input_image_path, output_folder)
    
    # Step 2: Caption the images
    await caption_image_set(processed_folder, prefix=prefix, postfix=postfix)
    
    # Step 3: Zip the folder
    zip_path = shutil.make_archive(output_folder, 'zip', output_folder)
    
    # Step 4: Clean up the unzipped folder
    shutil.rmtree(output_folder)
    
    return zip_path

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Create a LoRA training dataset from an input image.')
    parser.add_argument('input_image', help='Path to the input image with transparency.')
    parser.add_argument('-o', '--output', default='lora_dataset', help='Name of the output folder and zip file.')
    parser.add_argument('--prefix', default='', help='Optional prefix for image captions.')
    parser.add_argument('--postfix', default='', help='Optional postfix for image captions.')

    args = parser.parse_args()

    if not os.path.isfile(args.input_image):
        print(f"Error: The file {args.input_image} does not exist.")
        exit(1)

    zip_path = asyncio.run(create_lora_data_set(args.input_image, args.output, args.prefix, args.postfix))
    print(f"LoRA dataset created and zipped: {zip_path}")
