import os 
import random
import shutil
from collections import defaultdict 
from PIL import Image  
import numpy as np  
import pandas as pd 

#1. Calculate Average Hash
def average_hash(image_path, hash_size=16):
    img = Image.open(image_path).convert("L")  
    img = img.resize((hash_size, hash_size), Image.Resampling.LANCZOS)  
    pixels = np.array(img)
    avg = pixels.mean()
    hash_bits = (pixels >= avg).astype(int).flatten()  
    hash_string = ''.join(hash_bits.astype(str))  
    return hash_string


#2. Compare images based on hash
def compare_images(hash1, hash2):
    if len(hash1) != len(hash2):
        raise ValueError("Hash length mismatch!")
    return sum(c1 != c2 for c1, c2 in zip(hash1, hash2))  


#3. Remove duplicate images and labels with hash saving
def remove_duplicates(image_folder, label_folder, duplicate_image_folder, label_duplicate_folder, excel_file):
    os.makedirs(duplicate_image_folder, exist_ok=True)
    os.makedirs(label_duplicate_folder, exist_ok=True)

    #Read saved hash data from Excel
    if os.path.exists(excel_file):
        existing_data = pd.read_excel(excel_file)
        file_hashes = dict(zip(existing_data["Hash"], existing_data["Filename"]))
    else:
        file_hashes = {}

    image_data = [] 

    for root, _, files in os.walk(image_folder):
        for filename in files:
            if filename.endswith(('.png', '.jpg', '.jpeg')):
                file_path = os.path.join(root, filename)
                file_hash = average_hash(file_path)  
                is_duplicate = False
                for existing_hash, existing_file in file_hashes.items():
                    if compare_images(file_hash, existing_hash) <= 5:  
                        print(f"Duplicate image found: {filename} (Similar to {existing_file})")
                        shutil.move(file_path, os.path.join(duplicate_image_folder, filename))
                        label_file = os.path.splitext(filename)[0] + '.txt'
                        label_path = os.path.join(label_folder, label_file)
                        if os.path.exists(label_path):
                            shutil.move(label_path, os.path.join(label_duplicate_folder, label_file))
                            print(f"Moved label {label_file} to {label_duplicate_folder}")
                        else:
                            print(f"Label file not found for {filename}")

                        is_duplicate = True
                        break
                    
                if not is_duplicate:
                    file_hashes[file_hash] = filename
                    image_data.append([filename, file_hash])

    #Save the new hash information to Excel
    if image_data:
        new_df = pd.DataFrame(image_data, columns=["Filename", "Hash"])
        if os.path.exists(excel_file):
            existing_df = pd.read_excel(excel_file)
            combined_df = pd.concat([existing_df, new_df], ignore_index=True)
            combined_df.to_excel(excel_file, index=False)
        else:
            new_df.to_excel(excel_file, index=False)

    print("Duplicate removal complete.")

#4. Balanced label data distribution across classes
def distribute_labels_balanced(dataset_path, output_path, target):
    images_path = os.path.join(dataset_path, "images")
    labels_path = os.path.join(dataset_path, "labels")
    output_images_path = os.path.join(output_path, "images")
    output_labels_path = os.path.join(output_path, "labels")

    os.makedirs(output_images_path, exist_ok=True)
    os.makedirs(output_labels_path, exist_ok=True)

    final_label_count = defaultdict(int)

    #Read all `.txt` files in `labels_path` directory
    for root, _, files in os.walk(labels_path):
        for label_file in files:
            if label_file.endswith(".txt"):
                label_file_path = os.path.join(root, label_file)

                class_counts = defaultdict(int)
                with open(label_file_path, "r") as f:
                    for line in f:
                        class_id = line.split()[0]
                        class_counts[class_id] += 1

                #Make sure the corresponding image files exist before copying
                image_file = label_file.replace(".txt", ".jpg")
                image_file_path = os.path.join(images_path, image_file)
                if os.path.exists(image_file_path):
                    shutil.copy(label_file_path, os.path.join(output_labels_path, label_file))
                    shutil.copy(image_file_path, os.path.join(output_images_path, image_file))
                    for class_id, count in class_counts.items():
                        final_label_count[class_id] += count
                else:
                    print(f"Warning: Image file {image_file} does not exist for label file {label_file}")

    print("Balanced distribution complete.")
    for class_id, count in sorted(final_label_count.items()):
        print(f"Class {class_id}: {count}")

#5. Split data into train, test, val
def split_dataset(dataset_path, output_path, split_ratios):
    images_path = os.path.join(dataset_path, "images")
    labels_path = os.path.join(dataset_path, "labels")

    for split in ["train", "test", "val"]:
        os.makedirs(os.path.join(output_path, split, "images"), exist_ok=True)
        os.makedirs(os.path.join(output_path, split, "labels"), exist_ok=True)

    label_data = defaultdict(list)

    #Read all `.txt` files in `labels_path` directory
    for root, _, files in os.walk(labels_path):
        for label_file in files:
            if label_file.endswith(".txt"):
                with open(os.path.join(root, label_file), "r") as f:
                    lines = f.readlines()
                class_ids = {line.split()[0] for line in lines}
                for class_id in class_ids:
                    label_data[class_id].append(label_file)

    #Distribute data into train, test, val
    split_data = {"train": [], "test": [], "val": []}
    used_files = set()

    for class_id, files in label_data.items():
        random.shuffle(files)
        n_total = len(files)
        n_train = int(n_total * split_ratios["train"])
        n_test = int(n_total * split_ratios["test"])

        split_data["train"].extend(files[:n_train])
        split_data["test"].extend(files[n_train:n_train + n_test])
        split_data["val"].extend(files[n_train + n_test:])

    for split, files in split_data.items():
        for label_file in files:
            shutil.copy(os.path.join(labels_path, label_file), os.path.join(output_path, split, "labels", label_file))
            image_file = label_file.replace(".txt", ".jpg")
            shutil.copy(os.path.join(images_path, image_file), os.path.join(output_path, split, "images", image_file))

    print("Dataset split complete.")

#Main Function
if __name__ == "__main__":
    remove_duplicates(
        "data/images",
        "data/labels",
        "data/images_dup",
        "data/labels_dup",
        "data/image_descriptors2.xlsx"
    )
    distribute_labels_balanced("data/tomato", "data/tomato/balanced", target=7000)
    split_dataset("data/tomato/balanced", "data/tomato/split", {"train": 0.8, "test": 0.1, "val": 0.1})
