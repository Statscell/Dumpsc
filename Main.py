import os

from System.Lib import nul, Console
from System.Dumpsc import process_sc, decompress_data
from System.Decode import decode_sc, cut_sprites
from pathlib import Path

input_folder = "./In-Compressed"
output_folder = "./Out-Sprites"

def get_files():
    all_files = os.listdir(input_folder)
    if (len(all_files) < 1):
        Console.error('Input directory is Empty !!!')
        return

    files = []
    for test_file in all_files:
        if test_file.endswith(".sc"):
            files.append(test_file)

    if (len(files) < 1):
        Console.warn('No valid files found !!!')
        return
    
    return files

def extract_images():
    # Getting files
    files = get_files()
    if files is None: return

    for file in files:
        if file.endswith('_tex.sc'):
            sc_file = file[:-7] + ".sc"
            sc_file_name = sc_file[:-3]
            
            # Creating Sub directory for specified file
            sc_output_dir = f"{output_folder}/{sc_file_name}"
            Path(f"{sc_output_dir}/texture").mkdir(parents=True, exist_ok=True)

            with open(f"{input_folder}/{file}", "rb") as f:
                print('')
                Console.info(f"Processing {file}")
                # extracting texture
                images = process_sc(f"{sc_file_name}_tex", f.read(), f"{sc_output_dir}/texture/", True)

            if sc_file not in files:
                Console.warn(f"{sc_file} not found! Will skip cutting images")
                continue
            
            Console.info(f"Processing {sc_file}")
            with open(f"{input_folder}/{sc_file}", "rb") as f:
                data = decompress_data(f.read(), sc_file_name)                
                sprite_globals, sprite_data,sheet_data = decode_sc(data, sc_file_name)
                cut_sprites(sprite_globals, sprite_data, sheet_data, images, f"{sc_output_dir}")

            Console.success(f"Successfully extracted textures for {sc_file_name}")


if __name__ == '__main__':
    # Verifying and creating necessary directories
    [os.system(f'mkdir {i}{nul}') for i in ['In-Compressed', 'Out-Sprites']]
    Console.info('Directories successfully initiated!')

    # main task
    extract_images()
