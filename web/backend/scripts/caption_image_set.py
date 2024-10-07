import os
import asyncio
from toolbox.services.llm import LLMService
from .caption_image import caption_image

async def caption_image_set(folder_path, prefix="", postfix=""):
    llm_service = LLMService()
    
    # Ensure the folder exists
    if not os.path.isdir(folder_path):
        raise ValueError(f"The specified folder does not exist: {folder_path}")
    
    captions = {}
    caption_tasks = []
    
    for filename in os.listdir(folder_path):
        if filename.lower().endswith('.png'):
            file_path = os.path.join(folder_path, filename)
            
            # Create a caption task for each image
            caption_tasks.append((filename, caption_image(file_path, llm_service, prefix, postfix)))
    
    # Await all caption tasks concurrently
    results = await asyncio.gather(*(task for _, task in caption_tasks))
    
    # Process the results
    for (filename, _), full_caption in zip(caption_tasks, results):
        captions[filename] = full_caption
        
        # Write the caption to a text file
        txt_filename = os.path.splitext(filename)[0] + '.txt'
        txt_file_path = os.path.join(folder_path, txt_filename)
        with open(txt_file_path, 'w', encoding='utf-8') as txt_file:
            txt_file.write(full_caption)
    
    return captions

# Example usage remains the same
